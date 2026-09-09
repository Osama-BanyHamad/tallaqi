from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from services.audit.models import AuditLog
from services.common.permissions import CapabilityPermission, check, scoped
from services.hifz.models import QuranJourney

from . import asr, services
from .providers import AiUnavailable, get_provider

MAX_AUDIO_BYTES = 12 * 1024 * 1024
MAX_RANGE = 120  # Ayat per check; longer ranges are split by the client
ASR_DISCLAIMER = "كشف آلي غير معصوم: ما يظهر هنا مقترحات تُقارَن بالنص الموثّق، ويعتمدها المعلم أو يرفضها. لا يُعرض النص المسموع كقرآن."


class AiViewSet(viewsets.ViewSet):
    """YELLOW-class assistant: drafts and candidate detections for humans to review.
    Disabled per tenant by default; 503 when no provider is configured."""
    permission_classes = [CapabilityPermission]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    required_module = {"status": "ai.assist", "weekly_note": "ai.assist", "explain_journey": "ai.assist", "asr_check": "hifz.asr"}
    required_permission = {"status": "ai.assist.use", "weekly_note": "ai.assist.use", "explain_journey": "ai.assist.use", "asr_check": "hifz.asr.use"}

    def _journey(self, request):
        jid = request.data.get("journey_id")
        sid = request.data.get("student_id")
        qs = scoped(request, QuranJourney.objects.select_related("student__person"), branch_field="student__branch_id",
                    halaqah_field="student__enrollments__halaqah_id", student_field="student_id", person_field="student__person_id")
        j = qs.filter(pk=jid).first() if jid else qs.filter(student_id=sid).first() if sid else None
        if j is None:
            return None
        check(request, "hifz.journey.read", "hifz.journey", j)
        return j

    def _respond(self, request, kind, fn):
        j = self._journey(request)
        if j is None:
            return Response({"code": "not_found", "detail": "journey_id or student_id required"}, status=404)
        try:
            out = fn(j)
        except AiUnavailable as e:
            return Response({"code": "ai_unavailable", "detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        AuditLog.record(request, f"ai.{kind}", "QuranJourney", j.id, after={"provider": out["provider"], "model": out["model"], "chars": len(out["text"])})
        return Response(out)

    @action(detail=False, methods=["get"])
    def status(self, request):
        p = get_provider()
        return Response({"enabled": True, "provider": p.name, "model": p.model, "asr_model": p.asr_model, "configured": p.name != "null", "safety": "YELLOW",
                         "disclaimer": services.DISCLAIMER, "debug": bool(settings.DEBUG)})

    @action(detail=False, methods=["post"], url_path="weekly-note")
    def weekly_note(self, request):
        return self._respond(request, "weekly_note", services.weekly_note_draft)

    @action(detail=False, methods=["post"], url_path="explain-journey")
    def explain_journey(self, request):
        return self._respond(request, "explain_journey", services.explain_journey)

    @action(detail=False, methods=["post"], url_path="asr-check")
    def asr_check(self, request):
        """Multipart: audio (file), from_ayah_index, to_ayah_index, optional journey_id.
        Returns candidate mismatches positioned on the verified text — never the transcript as Quran."""
        try:
            frm, to = int(request.data.get("from_ayah_index")), int(request.data.get("to_ayah_index"))
        except (TypeError, ValueError):
            return Response({"code": "invalid", "detail": "from_ayah_index and to_ayah_index are required"}, status=400)
        if not (1 <= frm <= to <= 6236) or to - frm + 1 > MAX_RANGE:
            return Response({"code": "invalid", "detail": f"range must be 1..6236 and at most {MAX_RANGE} ayat"}, status=400)
        f = request.FILES.get("audio")
        if f is None:
            return Response({"code": "invalid", "detail": "audio file is required"}, status=400)
        if f.size > MAX_AUDIO_BYTES:
            return Response({"code": "invalid", "detail": "audio too large (max 12 MB)"}, status=413)
        journey = None
        if request.data.get("journey_id"):
            journey = self._journey(request)
            if journey is None:
                return Response({"code": "not_found", "detail": "journey not found"}, status=404)
        provider = get_provider()
        prompt = "تلاوة قرآنية مرتّلة باللغة العربية الفصحى."
        try:
            transcript = provider.transcribe(f.read(), f.name or "audio.webm", f.content_type or "application/octet-stream", language="ar", prompt=prompt)
        except AiUnavailable as e:
            return Response({"code": "ai_unavailable", "detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if transcript.strip().rstrip(".") == prompt.strip().rstrip("."):
            transcript = ""  # silent / unintelligible audio: the model echoes the prompt; treat as nothing heard
        result = asr.check_recitation(transcript, frm, to)
        result.update({"source": "ai", "provider": provider.name, "model": provider.asr_model, "safety": "YELLOW", "disclaimer": ASR_DISCLAIMER,
                       "from_ayah_index": frm, "to_ayah_index": to})
        AuditLog.record(request, "ai.asr_check", "QuranJourney" if journey else "Range", journey.id if journey else f"{frm}-{to}",
                        after={"provider": provider.name, "model": provider.asr_model, "accuracy": result["accuracy"], "candidates": len(result["candidates"]), "bytes": f.size})
        return Response(result)
