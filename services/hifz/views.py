from __future__ import annotations

from datetime import date

from django.utils.dateparse import parse_date
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from packages.hifz_engine import TEMPLATES
from services.audit.models import AuditLog
from services.common.exceptions import DomainError
from services.common.permissions import CapabilityPermission, check, scoped
from services.people.models import Halaqah, Staff

from . import services
from .models import (
    STANDARD_MISTAKE_TYPES,
    DailyPlan,
    JourneyEvent,
    MistakeEvent,
    MistakeType,
    PlanSegment,
    QuranJourney,
    RecitationSession,
)


def _journeys(request):
    qs = QuranJourney.objects.select_related("student__person", "student__branch")
    return scoped(request, qs, branch_field="student__branch_id", halaqah_field="student__enrollments__halaqah_id",
                  student_field="student_id", person_field="student__person_id")


class JourneySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.person.display_name_ar", read_only=True)
    student_code = serializers.CharField(source="student.student_code", read_only=True)
    current_key = serializers.SerializerMethodField()
    memorized_pages = serializers.SerializerMethodField()

    class Meta:
        model = QuranJourney
        fields = ["id", "student", "student_name", "student_code", "riwayah", "mushaf_type", "policy_key", "policy_overrides", "status",
                  "started_at", "direction", "current_ayah_index", "current_key", "level", "memorized_ayat", "strong_ayat",
                  "needs_revision_ayat", "weak_ayat", "critical_ayat", "mastered_ayat", "avg_retention", "memorized_pages",
                  "memorized_pages_order", "juz_map", "updated_at"]
        read_only_fields = ["id", "student", "memorized_ayat", "strong_ayat", "needs_revision_ayat", "weak_ayat", "critical_ayat",
                            "mastered_ayat", "avg_retention", "memorized_pages_order", "juz_map", "updated_at"]

    def get_current_key(self, obj):
        from packages.quran_core import get_core
        if not obj.current_ayah_index:
            return None
        a = get_core(obj.riwayah).ayah_by_index(obj.current_ayah_index)
        return {"key": a.key, "surah": a.surah, "ayah": a.ayah, "page": get_core(obj.riwayah).page_of(a.ayah_index),
                "surah_name": get_core(obj.riwayah).surah(a.surah).name_ar}

    def get_memorized_pages(self, obj):
        return len(obj.memorized_pages_order or [])


class JourneyViewSet(viewsets.ModelViewSet):
    serializer_class = JourneySerializer
    permission_classes = [CapabilityPermission]
    required_module = "hifz.journey"
    required_permission = {"list": "hifz.journey.read", "retrieve": "hifz.journey.read", "update": "hifz.journey.write",
                           "partial_update": "hifz.journey.write", "memory_map": "hifz.memory_map.read", "timeline": "hifz.journey.read",
                           "plan": "hifz.planner.read", "plan_action": "hifz.planner.approve", "override": "hifz.memory_map.override",
                           "sessions": "hifz.tasmee.read", "decay": "hifz.retention.read"}
    http_method_names = ["get", "patch", "post", "head", "options"]
    filterset_fields = ["status", "policy_key", "student__branch"]
    search_fields = ["student__person__display_name_ar", "student__student_code"]
    ordering_fields = ["avg_retention", "memorized_ayat", "updated_at"]

    def get_queryset(self):
        return _journeys(self.request).order_by("-updated_at")

    @action(detail=True, methods=["get"], url_path="memory-map")
    def memory_map(self, request, pk=None):
        j = self.get_object()
        level = request.query_params.get("level", "quran")
        number = request.query_params.get("number")
        check(request, "hifz.memory_map.read", "hifz.memory_map", j)
        return Response(services.memory_map(j, level, int(number) if number else None))

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        j = self.get_object()
        ev = JourneyEvent.objects.filter(journey=j).order_by("-occurred_at")[:200]
        return Response([{"id": e.id, "event_type": e.event_type, "payload": e.payload, "occurred_at": e.occurred_at} for e in ev])

    @action(detail=True, methods=["get", "post"], url_path="plan")
    def plan(self, request, pk=None):
        j = self.get_object()
        d = parse_date(request.query_params.get("date") or request.data.get("date") or "") or date.today()
        if request.method == "POST":
            check(request, "hifz.planner.approve", "hifz.planner", j)
            plan = services.generate_plan(j, d, regenerate=True)
        else:
            plan = services.generate_plan(j, d)
        return Response(PlanSerializer(plan).data)

    @action(detail=True, methods=["post"], url_path="plan/action")
    def plan_action(self, request, pk=None):
        j = self.get_object()
        d = parse_date(request.data.get("date") or "") or date.today()
        plan = services.generate_plan(j, d)
        act = request.data.get("action")
        if act == "override":
            check(request, "hifz.planner.override", "hifz.planner", j)
        plan = services.plan_action(plan, act, request.user, segments=request.data.get("segments"), reason=request.data.get("reason", ""))
        AuditLog.record(request, f"plan.{act}", "DailyPlan", plan.id, after=PlanSerializer(plan).data)
        return Response(PlanSerializer(plan).data)

    @action(detail=True, methods=["post"])
    def override(self, request, pk=None):
        j = self.get_object()
        first, last = int(request.data["from_ayah_index"]), int(request.data["to_ayah_index"])
        state = request.data.get("state") or None
        if state not in (None, "strong", "mastered", "needs_revision", "weak", "critical"):
            raise DomainError("Invalid state")
        n = services.override_ayah_state(j, first, last, state, request.user, request.data.get("reason", ""))
        AuditLog.record(request, "memory_map.override", "QuranJourney", j.id, after={"from": first, "to": last, "state": state, "n": n})
        return Response({"updated": n})

    @action(detail=True, methods=["get"])
    def sessions(self, request, pk=None):
        j = self.get_object()
        qs = RecitationSession.objects.filter(journey=j).prefetch_related("mistakes").select_related("teacher__person").order_by("-started_at")[:100]
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def decay(self, request, pk=None):
        j = self.get_object()
        return Response({"changed": services.run_decay(j)})


class SegmentSerializer(serializers.ModelSerializer):
    from_key = serializers.SerializerMethodField()
    to_key = serializers.SerializerMethodField()

    class Meta:
        model = PlanSegment
        fields = ["id", "purpose", "from_ayah_index", "to_ayah_index", "from_key", "to_key", "pages", "reason", "repetitions_required", "completion", "order"]

    def _key(self, idx):
        from packages.quran_core import get_core
        a = get_core().ayah_by_index(idx)
        return {"key": a.key, "surah_name": get_core().surah(a.surah).name_ar, "ayah": a.ayah}

    def get_from_key(self, obj):
        return self._key(obj.from_ayah_index)

    def get_to_key(self, obj):
        return self._key(obj.to_ayah_index)


class PlanSerializer(serializers.ModelSerializer):
    segments = SegmentSerializer(many=True, read_only=True)

    class Meta:
        model = DailyPlan
        fields = ["id", "journey", "plan_date", "status", "rationale", "paused_new", "planner_version", "approved_by", "segments"]


class MistakeIn(serializers.Serializer):
    ayah_index = serializers.IntegerField(min_value=1)
    word_position = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    mistake_type = serializers.CharField()
    severity = serializers.ChoiceField(choices=["major", "minor"], required=False, default="major")
    confused_with_ayah_index = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class RecitationIn(serializers.Serializer):
    journey = serializers.UUIDField()
    halaqah = serializers.UUIDField(required=False, allow_null=True)
    plan_segment = serializers.UUIDField(required=False, allow_null=True)
    purpose = serializers.ChoiceField(choices=["new", "near", "far", "assessment"], default="near")
    from_ayah_index = serializers.IntegerField(min_value=1)
    to_ayah_index = serializers.IntegerField(min_value=1)
    outcome = serializers.ChoiceField(choices=["pass", "repeat", "partial"])
    grade = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    note_visibility = serializers.ChoiceField(choices=["private", "supervisor", "parent"], default="parent")
    mistakes = MistakeIn(many=True, required=False, default=list)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="")
    source = serializers.ChoiceField(choices=["in_person", "live", "assessment"], default="in_person")


class MistakeOut(serializers.ModelSerializer):
    class Meta:
        model = MistakeEvent
        fields = ["id", "ayah_index", "word_position", "mistake_type", "severity", "confused_with_ayah_index", "note"]


class SessionSerializer(serializers.ModelSerializer):
    mistakes = MistakeOut(many=True, read_only=True)
    teacher_name = serializers.CharField(source="teacher.person.display_name_ar", read_only=True, default="")
    student_name = serializers.CharField(source="journey.student.person.display_name_ar", read_only=True)
    from_key = serializers.SerializerMethodField()
    to_key = serializers.SerializerMethodField()

    class Meta:
        model = RecitationSession
        fields = ["id", "journey", "student_name", "teacher", "teacher_name", "halaqah", "plan_segment", "purpose", "from_ayah_index", "to_ayah_index",
                  "from_key", "to_key", "started_at", "ended_at", "outcome", "grade", "note", "note_visibility", "source", "mistakes", "created_at"]

    def get_from_key(self, o):
        from packages.quran_core import get_core
        return get_core().ayah_by_index(o.from_ayah_index).key

    def get_to_key(self, o):
        from packages.quran_core import get_core
        return get_core().ayah_by_index(o.to_ayah_index).key


class RecitationViewSet(viewsets.GenericViewSet):
    """Tasmee' recording. The most important teacher endpoint: one POST records a full evaluation."""
    permission_classes = [CapabilityPermission]
    required_module = "hifz.tasmee"
    required_permission = {"create": "hifz.tasmee.record", "list": "hifz.tasmee.read", "retrieve": "hifz.tasmee.read", "mistake_types": "hifz.tasmee.read"}
    serializer_class = SessionSerializer

    def get_queryset(self):
        qs = RecitationSession.objects.select_related("journey__student__person", "teacher__person").prefetch_related("mistakes")
        return scoped(self.request, qs, branch_field="journey__student__branch_id", halaqah_field="journey__student__enrollments__halaqah_id",
                      student_field="journey__student_id", person_field="journey__student__person_id")

    def list(self, request):
        qs = self.get_queryset().order_by("-started_at")
        if request.query_params.get("halaqah"):
            qs = qs.filter(halaqah_id=request.query_params["halaqah"])
        if request.query_params.get("date"):
            qs = qs.filter(started_at__date=parse_date(request.query_params["date"]))
        if request.query_params.get("purpose"):
            qs = qs.filter(purpose=request.query_params["purpose"])
        if request.query_params.get("journey"):
            qs = qs.filter(journey_id=request.query_params["journey"])
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(SessionSerializer(page, many=True).data)

    def retrieve(self, request, pk=None):
        return Response(SessionSerializer(self.get_object()).data)

    def create(self, request):
        s = RecitationIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        j = _journeys(request).filter(pk=d["journey"]).first()
        if j is None:
            return Response({"code": "not_found", "detail": "Journey not found."}, status=404)
        check(request, "hifz.tasmee.record", "hifz.tasmee", j)
        if request.membership and request.membership.person_id and j.student.person_id == request.membership.person_id:
            return Response({"code": "self_tasmee", "detail": "لا يُسجَّل التسميع للنفس؛ ادعُ مُسمِّعًا أو استخدم التدريب الذاتي."}, status=403)
        if d["idempotency_key"]:
            replay = RecitationSession.objects.filter(idempotency_key=d["idempotency_key"]).first()
            if replay:
                return Response(SessionSerializer(replay).data, status=status.HTTP_200_OK)
        teacher = Staff.objects.filter(person_id=request.membership.person_id).first() if request.membership else None
        halaqah = Halaqah.objects.filter(pk=d["halaqah"]).first() if d.get("halaqah") else None
        seg = PlanSegment.objects.filter(pk=d["plan_segment"], plan__journey=j).first() if d.get("plan_segment") else None
        session = services.record_recitation(j, teacher=teacher, halaqah=halaqah, purpose=d["purpose"], from_ayah_index=d["from_ayah_index"],
                                             to_ayah_index=d["to_ayah_index"], outcome=d["outcome"], mistakes=d["mistakes"], note=d["note"],
                                             note_visibility=d["note_visibility"], grade=d.get("grade"), plan_segment=seg, source=d["source"],
                                             idempotency_key=d["idempotency_key"], recorded_by=request.user)
        AuditLog.record(request, "assessment.recorded", "RecitationSession", session.id,
                        after={"outcome": session.outcome, "range": [session.from_ayah_index, session.to_ayah_index], "mistakes": len(d["mistakes"])})
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="mistake-types")
    def mistake_types(self, request):
        custom = [{"key": f"tenant_custom:{m.key}", "name_ar": m.name_ar, "name_en": m.name_en, "severity": m.default_severity}
                  for m in MistakeType.objects.all()]
        return Response(STANDARD_MISTAKE_TYPES + custom)


class PoliciesView(viewsets.ViewSet):
    permission_classes = [CapabilityPermission]
    required_module = "hifz.policy"
    required_permission = {"list": "hifz.policy.read"}

    def list(self, request):
        return Response([p.model_dump() for p in TEMPLATES.values()])
