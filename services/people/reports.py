"""Reports: attendance, hifz progress, students — JSON or CSV. Read-only, scoped, capability-gated."""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta

from django.http import HttpResponse
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.common.permissions import CapabilityPermission, check, scoped

from .models import AttendanceRecord, Halaqah, Student


def _csv(name: str, header: list[str], rows: list[list]) -> HttpResponse:
    buf = io.StringIO()
    buf.write("﻿")  # BOM so Excel opens Arabic correctly
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    r = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    r["Content-Disposition"] = f'attachment; filename="{name}.csv"'
    return r


class ReportsView(viewsets.ViewSet):
    permission_classes = [CapabilityPermission]
    required_module = "intel.reports"
    required_permission = {"attendance": "intel.reports.read", "hifz": "intel.reports.read", "students": "intel.reports.read"}

    def _range(self, request):
        to = parse_date(request.query_params.get("to") or "") or date.today()
        frm = parse_date(request.query_params.get("from") or "") or (to - timedelta(days=30))
        return frm, to

    @action(detail=False, methods=["get"])
    def attendance(self, request):
        frm, to = self._range(request)
        if request.query_params.get("export") == "csv":
            check(request, "intel.reports.export", "intel.reports")
        halaqat = scoped(request, Halaqah.objects.select_related("branch"), branch_field="branch_id", halaqah_field="id")
        recs = AttendanceRecord.objects.filter(halaqah__in=halaqat, on_date__gte=frm, on_date__lte=to).select_related("student__person", "halaqah")
        per_student: dict = {}
        for r in recs:
            d = per_student.setdefault(r.student_id, {"name": r.student.person.display_name_ar, "halaqah": r.halaqah.name, "present": 0, "late": 0, "absent": 0, "excused": 0, "left_early": 0, "total": 0})
            d[r.status] = d.get(r.status, 0) + 1
            d["total"] += 1
        rows = sorted(per_student.values(), key=lambda x: (x["halaqah"], x["name"]))
        for d in rows:
            d["rate"] = round((d["present"] + d["late"]) / d["total"], 3) if d["total"] else None
        per_halaqah: dict = {}
        for d in rows:
            h = per_halaqah.setdefault(d["halaqah"], {"halaqah": d["halaqah"], "students": 0, "present": 0, "total": 0})
            h["students"] += 1
            h["present"] += d["present"] + d["late"]
            h["total"] += d["total"]
        for h in per_halaqah.values():
            h["rate"] = round(h["present"] / h["total"], 3) if h["total"] else None
        if request.query_params.get("export") == "csv":
            return _csv(f"attendance_{frm}_{to}", ["الطالب", "الحلقة", "حاضر", "متأخر", "غائب", "بعذر", "انصرف مبكرًا", "المجموع", "النسبة"],
                        [[d["name"], d["halaqah"], d["present"], d["late"], d["absent"], d["excused"], d["left_early"], d["total"], d["rate"]] for d in rows])
        return Response({"from": frm, "to": to, "halaqat": list(per_halaqah.values()), "students": rows})

    @action(detail=False, methods=["get"])
    def hifz(self, request):
        from services.hifz.models import QuranJourney, RecitationSession
        frm, to = self._range(request)
        if request.query_params.get("export") == "csv":
            check(request, "intel.reports.export", "intel.reports")
        journeys = scoped(request, QuranJourney.objects.select_related("student__person", "student__branch"), branch_field="student__branch_id",
                          halaqah_field="student__enrollments__halaqah_id", student_field="student_id")
        sessions = RecitationSession.objects.filter(journey__in=journeys, started_at__date__gte=frm, started_at__date__lte=to)
        stats: dict = {}
        for s in sessions:
            d = stats.setdefault(s.journey_id, {"sessions": 0, "passed": 0, "new_ayat": 0, "revision_ayat": 0})
            d["sessions"] += 1
            d["passed"] += 1 if s.outcome == "pass" else 0
            n = s.to_ayah_index - s.from_ayah_index + 1
            if s.purpose == "new":
                d["new_ayat"] += n
            else:
                d["revision_ayat"] += n
        rows = []
        for j in journeys:
            d = stats.get(j.id, {"sessions": 0, "passed": 0, "new_ayat": 0, "revision_ayat": 0})
            rows.append({"journey_id": j.id, "student_id": j.student_id, "name": j.student.person.display_name_ar, "code": j.student.student_code, "branch": j.student.branch.name,
                         "memorized_pages": len(j.memorized_pages_order or []), "memorized_ayat": j.memorized_ayat, "avg_retention": j.avg_retention,
                         "weak_ayat": j.weak_ayat, "critical_ayat": j.critical_ayat, **d})
        rows.sort(key=lambda r: r["name"])
        if request.query_params.get("export") == "csv":
            return _csv(f"hifz_{frm}_{to}", ["الطالب", "الرقم", "الفرع", "صفحات محفوظة", "آيات محفوظة", "متوسط الثبات", "ضعيف", "حرج", "تسميعات", "اجتاز", "آيات جديدة", "آيات مراجعة"],
                        [[r["name"], r["code"], r["branch"], r["memorized_pages"], r["memorized_ayat"], r["avg_retention"], r["weak_ayat"], r["critical_ayat"], r["sessions"], r["passed"], r["new_ayat"], r["revision_ayat"]] for r in rows])
        return Response({"from": frm, "to": to, "students": rows})

    @action(detail=False, methods=["get"])
    def students(self, request):
        if request.query_params.get("export") == "csv":
            check(request, "intel.reports.export", "intel.reports")
        qs = scoped(request, Student.objects.select_related("person", "branch").prefetch_related("enrollments__halaqah", "guardian_links__guardian__person"),
                    branch_field="branch_id", halaqah_field="enrollments__halaqah_id", student_field="id")
        rows = []
        for s in qs.order_by("person__display_name_ar"):
            e = next((e for e in s.enrollments.all() if e.status == "active"), None)
            g = next((lk for lk in s.guardian_links.all() if lk.active), None)
            rows.append({"id": s.id, "name": s.person.display_name_ar, "code": s.student_code, "branch": s.branch.name, "halaqah": e.halaqah.name if e else "",
                         "status": s.status, "level": s.level, "dob": s.person.date_of_birth, "guardian": g.guardian.person.display_name_ar if g else "", "phone": g.guardian.person.phone if g else ""})
        if request.query_params.get("export") == "csv":
            return _csv("students", ["الطالب", "الرقم", "الفرع", "الحلقة", "الحالة", "المستوى", "تاريخ الميلاد", "ولي الأمر", "الهاتف"],
                        [[r["name"], r["code"], r["branch"], r["halaqah"], r["status"], r["level"], r["dob"], r["guardian"], r["phone"]] for r in rows])
        return Response({"students": rows})
