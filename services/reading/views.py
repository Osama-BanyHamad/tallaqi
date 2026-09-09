"""Daily reading (wird) API. One active plan per person; the device schedules reminders from `reminder_time`."""
from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from packages.quran_core import get_core
from services.audit.models import AuditLog
from services.common.permissions import CapabilityPermission, check

from .models import MUSHAF_PAGES, ReadingLog, ReadingPlan


class PlanIn(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["khatmah", "pages"], default="khatmah")
    pages_per_day = serializers.IntegerField(min_value=1, max_value=60, required=False)
    target_days = serializers.IntegerField(min_value=1, max_value=730, required=False)
    start_page = serializers.IntegerField(min_value=1, max_value=MUSHAF_PAGES, default=1)
    reminder_time = serializers.RegexField(r"^([01]\d|2[0-3]):[0-5]\d$", required=False, allow_blank=True)

    def validate(self, d):
        if not d.get("pages_per_day") and not d.get("target_days"):
            raise serializers.ValidationError({"pages_per_day": "أدخل عدد الصفحات يوميًا أو عدد الأيام."})
        if not d.get("pages_per_day"):
            remaining = MUSHAF_PAGES - d["start_page"] + 1
            d["pages_per_day"] = max(1, -(-remaining // d["target_days"]))  # ceil
        return d


class PlanSerializer(serializers.ModelSerializer):
    progress = serializers.FloatField(read_only=True)
    pages_done = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReadingPlan
        fields = ["id", "kind", "pages_per_day", "current_page", "start_page", "riwayah", "status", "started_on", "target_date", "khatmat",
                  "reminder_time", "progress", "pages_done", "created_at", "updated_at"]
        read_only_fields = ["id", "current_page", "start_page", "status", "started_on", "khatmat", "created_at", "updated_at"]


class LogIn(serializers.Serializer):
    from_page = serializers.IntegerField(min_value=1, max_value=MUSHAF_PAGES)
    to_page = serializers.IntegerField(min_value=1, max_value=MUSHAF_PAGES)
    minutes = serializers.IntegerField(min_value=0, max_value=600, default=0)

    def validate(self, d):
        if d["to_page"] < d["from_page"]:
            raise serializers.ValidationError({"to_page": "نهاية القراءة قبل بدايتها."})
        return d


def _person_id(request):
    me = getattr(request, "membership", None)
    return me.person_id if me and me.person_id else None


def _today_range(plan: ReadingPlan) -> tuple[int, int]:
    first = plan.current_page
    last = min(MUSHAF_PAGES, first + plan.pages_per_day - 1)
    return first, last


def _streak(plan: ReadingPlan, today: date) -> int:
    days = set(ReadingLog.objects.filter(plan=plan, on_date__gte=today - timedelta(days=400)).values_list("on_date", flat=True))
    n, d = 0, today
    if d not in days:
        d -= timedelta(days=1)  # today not read yet does not break the streak
    while d in days:
        n += 1
        d -= timedelta(days=1)
    return n


class ReadingViewSet(viewsets.ViewSet):
    """`/reading/plan` (GET/POST/PATCH), `/reading/today`, `/reading/log` (POST), `/reading/history`."""

    permission_classes = [CapabilityPermission]
    required_module = "quran.reading"
    required_permission = "quran.reading.use"

    def _plan(self, request) -> ReadingPlan | None:
        pid = _person_id(request)
        if pid is None:
            return None
        return ReadingPlan.objects.filter(person_id=pid, status="active").order_by("-created_at").first()

    def _today_payload(self, plan: ReadingPlan, today: date):
        core = get_core(plan.riwayah)
        first, last = _today_range(plan)
        logs_today = list(ReadingLog.objects.filter(plan=plan, on_date=today).order_by("from_page"))
        read_today = sum(l.to_page - l.from_page + 1 for l in logs_today)
        p1, p2 = core.page(first), core.page(last)
        a1, a2 = core.ayah_by_index(p1.first_ayah_index), core.ayah_by_index(p2.last_ayah_index)
        remaining = MUSHAF_PAGES - plan.current_page + 1
        return {
            "plan": PlanSerializer(plan).data,
            "today": {"from_page": first, "to_page": last, "pages": last - first + 1,
                      "from_key": a1.key, "to_key": a2.key, "from_surah": core.surah(a1.surah).name_ar, "to_surah": core.surah(a2.surah).name_ar,
                      "juz": p1.juz, "done": read_today >= (last - first + 1), "read_today": read_today},
            "streak": _streak(plan, today),
            "days_left": -(-remaining // plan.pages_per_day),
            "remaining_pages": remaining,
        }

    @action(detail=False, methods=["get", "post", "patch"], url_path="plan")
    def plan(self, request):
        check(request, "quran.reading.use")
        pid = _person_id(request)
        if pid is None:
            return Response({"code": "no_person", "detail": "هذا الحساب غير مرتبط بشخص؛ لا يمكن إنشاء ورد."}, status=400)
        if request.method == "GET":
            plan = self._plan(request)
            if plan is None:
                return Response({"code": "no_plan", "detail": "لا يوجد ورد بعد."}, status=404)
            return Response(PlanSerializer(plan).data)
        if request.method == "PATCH":
            plan = self._plan(request)
            if plan is None:
                return Response({"code": "no_plan"}, status=404)
            data = request.data
            if "pages_per_day" in data:
                plan.pages_per_day = max(1, min(60, int(data["pages_per_day"])))
            if "current_page" in data:
                plan.current_page = max(1, min(MUSHAF_PAGES, int(data["current_page"])))
            if "reminder_time" in data:
                plan.reminder_time = str(data["reminder_time"] or "")[:5]
            if data.get("status") in ("active", "paused"):
                plan.status = data["status"]
            plan.save()
            return Response(PlanSerializer(plan).data)
        s = PlanIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        today = date.today()
        with transaction.atomic():
            ReadingPlan.objects.filter(person_id=pid, status="active").update(status="paused")
            remaining = MUSHAF_PAGES - d["start_page"] + 1
            plan = ReadingPlan.objects.create(
                person_id=pid, kind=d["kind"], pages_per_day=d["pages_per_day"], current_page=d["start_page"], start_page=d["start_page"],
                started_on=today, target_date=today + timedelta(days=-(-remaining // d["pages_per_day"])), reminder_time=d.get("reminder_time", ""))
        AuditLog.record(request, "reading.plan.create", "ReadingPlan", plan.id, after={"pages_per_day": plan.pages_per_day, "start_page": plan.start_page})
        return Response(self._today_payload(plan, today), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        check(request, "quran.reading.use")
        plan = self._plan(request)
        if plan is None:
            return Response({"code": "no_plan", "detail": "لا يوجد ورد بعد."}, status=404)
        return Response(self._today_payload(plan, date.today()))

    @action(detail=False, methods=["post"], url_path="log")
    def log(self, request):
        check(request, "quran.reading.use")
        plan = self._plan(request)
        if plan is None:
            return Response({"code": "no_plan"}, status=404)
        s = LogIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        today = date.today()
        with transaction.atomic():
            ReadingLog.objects.create(plan=plan, on_date=today, from_page=d["from_page"], to_page=d["to_page"], minutes=d["minutes"])
            if d["to_page"] >= plan.current_page:
                if d["to_page"] >= MUSHAF_PAGES:
                    plan.khatmat += 1
                    plan.current_page = 1
                else:
                    plan.current_page = d["to_page"] + 1
                plan.save(update_fields=["khatmat", "current_page", "updated_at"])
        return Response(self._today_payload(plan, today), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        check(request, "quran.reading.use")
        plan = self._plan(request)
        if plan is None:
            return Response({"days": []})
        try:
            n = max(1, min(365, int(request.query_params.get("days", 30))))
        except (TypeError, ValueError):
            n = 30
        since = date.today() - timedelta(days=n - 1)
        rows = ReadingLog.objects.filter(plan=plan, on_date__gte=since).order_by("on_date")
        by_day: dict[str, dict] = {}
        for r in rows:
            k = r.on_date.isoformat()
            e = by_day.setdefault(k, {"date": k, "pages": 0, "minutes": 0})
            e["pages"] += r.to_page - r.from_page + 1
            e["minutes"] += r.minutes
        return Response({"days": list(by_day.values()), "since": since.isoformat()})
