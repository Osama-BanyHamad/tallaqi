from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.audit.models import AuditLog
from services.common.permissions import CapabilityPermission, check, scoped

from .models import AttendanceRecord, Enrollment, Guardian, GuardianLink, Halaqah, HalaqahStaff, Person, Staff, Student


class PersonSerializer(serializers.ModelSerializer):
    display_name_ar = serializers.CharField(required=False, allow_blank=True)
    display_name_en = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Person
        fields = ["id", "first_name", "last_name", "display_name_ar", "display_name_en", "date_of_birth", "gender", "phone", "email", "status"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Display names default to "first last" so forms only need the two name parts."""
        first, last = attrs.get("first_name", ""), attrs.get("last_name", "")
        if not attrs.get("display_name_ar") and (first or last or self.instance is None):
            attrs["display_name_ar"] = f"{first} {last}".strip() or (self.instance.display_name_ar if self.instance else "")
        return attrs


class GuardianIn(serializers.Serializer):
    display_name_ar = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    relationship = serializers.CharField(required=False, default="parent")
    gender = serializers.CharField(required=False, allow_blank=True, default="")


class StudentSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    halaqah = serializers.SerializerMethodField()
    journey_summary = serializers.SerializerMethodField()
    halaqah_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    guardian = GuardianIn(write_only=True, required=False)

    class Meta:
        model = Student
        fields = ["id", "person", "branch", "branch_name", "student_code", "level", "status", "is_minor", "notes", "halaqah", "journey_summary", "created_at",
                  "halaqah_id", "guardian"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"student_code": {"required": False, "allow_blank": True}}

    def get_halaqah(self, obj):
        e = next((e for e in obj.enrollments.all() if e.status == "active"), None)
        return {"id": e.halaqah_id, "name": e.halaqah.name} if e else None

    def get_journey_summary(self, obj):
        j = getattr(obj, "journey", None)
        if j is None:
            return None
        return {"id": j.id, "status": j.status, "memorized_ayat": j.memorized_ayat, "avg_retention": j.avg_retention,
                "weak_ayat": j.weak_ayat, "critical_ayat": j.critical_ayat, "memorized_pages": len(j.memorized_pages_order or []),
                "juz_map": j.juz_map, "current_ayah_index": j.current_ayah_index}

    @transaction.atomic
    def create(self, validated):
        halaqah_id = validated.pop("halaqah_id", None)
        gdata = validated.pop("guardian", None)
        pdata = validated.pop("person")
        if not pdata.get("display_name_ar"):
            pdata["display_name_ar"] = f"{pdata.get('first_name', '')} {pdata.get('last_name', '')}".strip()
        person = Person.objects.create(**pdata)
        if not validated.get("student_code"):
            validated["student_code"] = f"S{1000 + Student.objects.count() + 1}"
        student = Student.objects.create(person=person, **validated)
        if halaqah_id:
            h = Halaqah.objects.get(pk=halaqah_id)
            Enrollment.objects.create(student=student, halaqah=h, start_date=date.today())
        if gdata:
            gp = Person.objects.create(first_name=gdata["display_name_ar"].split(" ")[0], display_name_ar=gdata["display_name_ar"],
                                       phone=gdata.get("phone", ""), email=gdata.get("email", ""), gender=gdata.get("gender", ""))
            g = Guardian.objects.create(person=gp)
            GuardianLink.objects.create(guardian=g, student=student, relationship=gdata.get("relationship", "parent"))
        return student

    @transaction.atomic
    def update(self, instance, validated):
        validated.pop("guardian", None)
        halaqah_id = validated.pop("halaqah_id", "__unset__")
        pdata = validated.pop("person", None)
        if pdata:
            for k, v in pdata.items():
                setattr(instance.person, k, v)
            instance.person.save()
        obj = super().update(instance, validated)
        if halaqah_id != "__unset__":
            current = obj.enrollments.filter(status="active").first()
            if halaqah_id and (current is None or str(current.halaqah_id) != str(halaqah_id)):
                obj.enrollments.filter(status="active").update(status="ended", end_date=date.today(), reason="moved")
                Enrollment.objects.create(student=obj, halaqah_id=halaqah_id, start_date=date.today())
            elif not halaqah_id and current:
                obj.enrollments.filter(status="active").update(status="ended", end_date=date.today(), reason="unenrolled")
        return obj


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [CapabilityPermission]
    required_module = "people.students"
    required_permission = {"list": "people.students.read", "retrieve": "people.students.read", "create": "people.students.write",
                           "update": "people.students.write", "partial_update": "people.students.write", "destroy": "people.students.write",
                           "guardians": "people.guardians.read", "weekly": "hifz.journey.read", "attendance_history": "ops.attendance.read"}
    filterset_fields = ["status", "branch", "level"]
    search_fields = ["person__display_name_ar", "person__display_name_en", "student_code", "person__phone"]
    ordering_fields = ["created_at", "student_code"]

    def get_queryset(self):
        qs = Student.objects.select_related("person", "branch", "journey").prefetch_related("enrollments__halaqah")
        qs = scoped(self.request, qs, branch_field="branch_id", halaqah_field="enrollments__halaqah_id", student_field="id", person_field="person_id")
        if self.request.query_params.get("halaqah"):
            qs = qs.filter(enrollments__halaqah_id=self.request.query_params["halaqah"], enrollments__status="active")
        return qs.order_by("person__display_name_ar")

    def perform_create(self, serializer):
        obj = serializer.save()
        from services.hifz.models import QuranJourney
        QuranJourney.objects.get_or_create(student=obj, defaults={"riwayah": self.request.tenant.default_riwayah,
                                           "mushaf_type": self.request.tenant.default_mushaf_type, "started_at": date.today()})
        AuditLog.record(self.request, "student.created", "Student", obj.id, after={"code": obj.student_code})

    @action(detail=True, methods=["get"])
    def weekly(self, request, pk=None):
        """Parent-facing weekly summary: the six questions, computed from verified data only."""
        from datetime import timedelta

        from django.utils import timezone as tz

        from services.hifz import services as hifz
        from services.hifz.models import RecitationSession
        from services.hifz.views import PlanSerializer

        st = self.get_object()
        j = getattr(st, "journey", None)
        now = tz.now()
        week_ago = now - timedelta(days=7)
        att = list(AttendanceRecord.objects.filter(student=st, on_date__gte=week_ago.date()).values_list("status", flat=True))
        sessions = list(RecitationSession.objects.filter(journey=j, started_at__gte=week_ago).order_by("-started_at")) if j else []
        from packages.quran_core import get_core
        core = get_core()

        def pages(purposes):
            seen = set()
            for s in sessions:
                if s.purpose in purposes and s.outcome != "repeat":
                    for pg in range(core.page_of(s.from_ayah_index), core.page_of(s.to_ayah_index) + 1):
                        seen.add(pg)
            return len(seen)

        note = next((s.note for s in sessions if s.note and s.note_visibility == "parent"), "")
        plan = hifz.generate_plan(j, now.date()) if j else None
        return Response({
            "student": {"id": st.id, "name": st.person.display_name_ar, "code": st.student_code},
            "week": {"from": week_ago.date(), "to": now.date()},
            "attendance": {"present": sum(1 for a in att if a in ("present", "late")), "total": len(att)},
            "new_pages": pages({"new"}), "revision_pages": pages({"near", "far"}),
            "sessions": len(sessions), "passed": sum(1 for s in sessions if s.outcome == "pass"),
            "retention": j.avg_retention if j else None, "memorized_pages": len(j.memorized_pages_order or []) if j else 0,
            "weak_ayat": j.weak_ayat if j else 0, "critical_ayat": j.critical_ayat if j else 0,
            "juz_map": j.juz_map if j else [], "teacher_note": note,
            "plan": PlanSerializer(plan).data if plan else None,
            "current": ({"key": core.ayah_by_index(j.current_ayah_index).key, "surah_name": core.surah(core.ayah_by_index(j.current_ayah_index).surah).name_ar}
                        if j and j.current_ayah_index else None),
        })

    @action(detail=True, methods=["get", "post"])
    def guardians(self, request, pk=None):
        st = self.get_object()
        if request.method == "POST":
            check(request, "people.guardians.link", "people.guardians")
            g = GuardianIn(data=request.data)
            g.is_valid(raise_exception=True)
            d = g.validated_data
            gp = Person.objects.create(first_name=d["display_name_ar"].split(" ")[0], display_name_ar=d["display_name_ar"], phone=d["phone"], email=d["email"], gender=d["gender"])
            guardian = Guardian.objects.create(person=gp)
            GuardianLink.objects.create(guardian=guardian, student=st, relationship=d["relationship"], primary=not GuardianLink.objects.filter(student=st).exists())
            AuditLog.record(request, "guardian.linked", "Student", st.id, after={"guardian": str(guardian.id)})
        links = GuardianLink.objects.filter(student=st, active=True).select_related("guardian__person")
        return Response([{"id": lk.guardian_id, "name": lk.guardian.person.display_name_ar, "phone": lk.guardian.person.phone, "email": lk.guardian.person.email,
                          "relationship": lk.relationship, "primary": lk.primary} for lk in links])

    @action(detail=True, methods=["get"], url_path="attendance")
    def attendance_history(self, request, pk=None):
        from datetime import timedelta
        st = self.get_object()
        days = int(request.query_params.get("days", 60))
        since = date.today() - timedelta(days=days)
        rows = AttendanceRecord.objects.filter(student=st, on_date__gte=since).select_related("halaqah").order_by("-on_date")
        counts = {}
        for r in rows:
            counts[r.status] = counts.get(r.status, 0) + 1
        return Response({"since": since, "counts": counts, "records": [{"date": r.on_date, "status": r.status, "halaqah": r.halaqah.name, "reason": r.reason} for r in rows]})


class StaffSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    halaqat = serializers.SerializerMethodField()
    halaqah_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    account_email = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = ["id", "person", "branch", "staff_type", "qualifications", "riwayat", "max_load", "is_active", "halaqat", "halaqah_ids", "account_email"]

    def get_halaqat(self, obj):
        return [{"id": a.halaqah_id, "name": a.halaqah.name, "role": a.role} for a in obj.halaqah_assignments.all()]

    def get_account_email(self, obj):
        m = obj.person.memberships.first()
        return m.account.email if m else None

    def _sync(self, staff, ids):
        HalaqahStaff.objects.filter(staff=staff).exclude(halaqah_id__in=ids).delete()
        for hid in ids:
            HalaqahStaff.objects.get_or_create(halaqah_id=hid, staff=staff, role="teacher" if staff.staff_type == "teacher" else "assistant")

    @transaction.atomic
    def create(self, validated):
        ids = validated.pop("halaqah_ids", None)
        pdata = validated.pop("person")
        if not pdata.get("display_name_ar"):
            pdata["display_name_ar"] = f"{pdata.get('first_name', '')} {pdata.get('last_name', '')}".strip()
        person = Person.objects.create(**pdata)
        staff = Staff.objects.create(person=person, **validated)
        if ids is not None:
            self._sync(staff, ids)
        return staff

    @transaction.atomic
    def update(self, instance, validated):
        ids = validated.pop("halaqah_ids", None)
        pdata = validated.pop("person", None)
        if pdata:
            for k, v in pdata.items():
                setattr(instance.person, k, v)
            instance.person.save()
        obj = super().update(instance, validated)
        if ids is not None:
            self._sync(obj, ids)
        return obj


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [CapabilityPermission]
    required_module = "people.staff"
    required_permission = {"list": "people.staff.read", "retrieve": "people.staff.read", "create": "people.staff.write",
                           "update": "people.staff.write", "partial_update": "people.staff.write", "destroy": "people.staff.write"}
    filterset_fields = ["staff_type", "branch", "is_active"]
    search_fields = ["person__display_name_ar", "person__display_name_en"]

    def get_queryset(self):
        qs = Staff.objects.select_related("person", "branch").prefetch_related("halaqah_assignments__halaqah")
        return scoped(self.request, qs, branch_field="branch_id", person_field="person_id").order_by("person__display_name_ar")


class HalaqahSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    teachers = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    teacher_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Halaqah
        fields = ["id", "branch", "branch_name", "name", "kind", "gender_policy", "capacity", "riwayah", "mushaf_type", "policy_key",
                  "schedule_summary", "status", "teachers", "student_count", "teacher_id"]

    def _set_teacher(self, h, tid):
        HalaqahStaff.objects.filter(halaqah=h, role="teacher").exclude(staff_id=tid).delete()
        if tid:
            HalaqahStaff.objects.get_or_create(halaqah=h, staff_id=tid, role="teacher")

    @transaction.atomic
    def create(self, validated):
        tid = validated.pop("teacher_id", None)
        h = super().create(validated)
        self._set_teacher(h, tid)
        return h

    @transaction.atomic
    def update(self, instance, validated):
        tid = validated.pop("teacher_id", "__unset__")
        h = super().update(instance, validated)
        if tid != "__unset__":
            self._set_teacher(h, tid)
        return h

    def get_teachers(self, obj):
        return [{"id": a.staff_id, "name": a.staff.person.display_name_ar, "role": a.role} for a in obj.staff_assignments.all()]

    def get_student_count(self, obj):
        return sum(1 for e in obj.enrollments.all() if e.status == "active")


class HalaqahViewSet(viewsets.ModelViewSet):
    serializer_class = HalaqahSerializer
    permission_classes = [CapabilityPermission]
    required_module = "ops.halaqat"
    required_permission = {"list": "ops.halaqat.read", "retrieve": "ops.halaqat.read", "create": "ops.halaqat.write", "update": "ops.halaqat.write",
                           "partial_update": "ops.halaqat.write", "destroy": "ops.halaqat.write", "today": "ops.halaqat.read",
                           "attendance": "ops.attendance.mark", "enroll": "ops.halaqat.enroll", "attendance_matrix": "ops.attendance.read"}
    filterset_fields = ["branch", "kind", "status"]
    search_fields = ["name"]

    def get_queryset(self):
        qs = Halaqah.objects.select_related("branch").prefetch_related("staff_assignments__staff__person", "enrollments")
        return scoped(self.request, qs, branch_field="branch_id", halaqah_field="id").order_by("name")

    @action(detail=True, methods=["get"])
    def today(self, request, pk=None):
        """The teacher's working screen: roster + today's plan per student + attendance + last session."""
        from services.hifz import services as hifz
        from services.hifz.models import RecitationSession
        from services.hifz.views import PlanSerializer

        h = self.get_object()
        d = parse_date(request.query_params.get("date") or "") or date.today()
        att = {a.student_id: a for a in AttendanceRecord.objects.filter(halaqah=h, on_date=d)}
        enrollments = Enrollment.objects.filter(halaqah=h, status="active").select_related("student__person", "student__journey")
        roster = []
        for e in enrollments:
            st = e.student
            j = getattr(st, "journey", None)
            plan = hifz.generate_plan(j, d) if j else None
            last = RecitationSession.objects.filter(journey=j).order_by("-started_at").first() if j else None
            roster.append({
                "student_id": st.id, "journey_id": j.id if j else None, "name": st.person.display_name_ar, "code": st.student_code,
                "attendance": att[st.id].status if st.id in att else None,
                "journey": {"memorized_ayat": j.memorized_ayat, "avg_retention": j.avg_retention, "weak_ayat": j.weak_ayat,
                            "critical_ayat": j.critical_ayat, "current_ayah_index": j.current_ayah_index,
                            "memorized_pages": len(j.memorized_pages_order or []), "juz_map": j.juz_map} if j else None,
                "plan": PlanSerializer(plan).data if plan else None,
                "last_session": {"started_at": last.started_at, "outcome": last.outcome, "purpose": last.purpose,
                                 "range": [last.from_ayah_index, last.to_ayah_index]} if last else None,
            })
        return Response({"halaqah": HalaqahSerializer(h).data, "date": d, "roster": roster})

    @action(detail=True, methods=["post"])
    def attendance(self, request, pk=None):
        h = self.get_object()
        d = parse_date(request.data.get("date") or "") or date.today()
        out = []
        for row in request.data.get("records", []):
            rec, _ = AttendanceRecord.objects.update_or_create(halaqah=h, student_id=row["student_id"], on_date=d,
                                                               defaults={"status": row.get("status", "present"), "reason": row.get("reason", ""),
                                                                         "marked_by": request.user})
            out.append({"student_id": rec.student_id, "status": rec.status})
        AuditLog.record(request, "attendance.recorded", "Halaqah", h.id, after={"date": str(d), "count": len(out)})
        return Response({"date": d, "records": out})

    @action(detail=True, methods=["get"], url_path="attendance-history")
    def attendance_matrix(self, request, pk=None):
        from datetime import timedelta
        h = self.get_object()
        days = int(request.query_params.get("days", 30))
        since = date.today() - timedelta(days=days)
        recs = AttendanceRecord.objects.filter(halaqah=h, on_date__gte=since)
        by = {}
        for r in recs:
            by.setdefault(str(r.student_id), {})[str(r.on_date)] = r.status
        dates = sorted({str(r.on_date) for r in recs})
        students = [{"id": e.student_id, "name": e.student.person.display_name_ar, "days": by.get(str(e.student_id), {})}
                    for e in Enrollment.objects.filter(halaqah=h, status="active").select_related("student__person")]
        return Response({"since": since, "dates": dates, "students": students})

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        h = self.get_object()
        st = Student.objects.get(pk=request.data["student_id"])
        Enrollment.objects.filter(student=st, status="active").exclude(halaqah=h).update(status="ended", end_date=date.today(), reason="moved")
        e, _ = Enrollment.objects.get_or_create(student=st, halaqah=h, status="active", defaults={"start_date": date.today()})
        AuditLog.record(request, "student.enrolled", "Enrollment", e.id, after={"halaqah": str(h.id), "student": str(st.id)})
        return Response({"enrollment": e.id})


class DashboardView(viewsets.ViewSet):
    """Supervisor intelligence: on-track / behind / attention, with explanations."""
    permission_classes = [CapabilityPermission]
    required_module = "intel.supervisor"
    required_permission = {"list": "intel.supervisor.read"}

    def list(self, request):
        from datetime import timedelta

        from django.db.models import Count
        from django.utils import timezone as tz

        from services.hifz.models import QuranJourney, RecitationSession

        journeys = scoped(request, QuranJourney.objects.select_related("student__person", "student__branch"),
                          branch_field="student__branch_id", halaqah_field="student__enrollments__halaqah_id", student_field="student_id")
        week_ago = tz.now() - timedelta(days=7)
        two_weeks = tz.now() - timedelta(days=14)
        recent = dict(RecitationSession.objects.filter(started_at__gte=week_ago).values_list("journey_id").annotate(n=Count("id")).values_list("journey_id", "n"))
        absent = dict(AttendanceRecord.objects.filter(on_date__gte=two_weeks.date(), status="absent").values_list("student_id").annotate(n=Count("id")).values_list("student_id", "n"))
        attention, behind, on_track = [], [], []
        for j in journeys:
            reasons = []
            if j.critical_ayat >= 3:
                reasons.append(f"{j.critical_ayat} آيات حرجة")
            if j.memorized_ayat and j.avg_retention < 0.6:
                reasons.append(f"متوسط الثبات {j.avg_retention:.0%}")
            if absent.get(j.student_id, 0) >= 3:
                reasons.append(f"{absent[j.student_id]} غيابات في أسبوعين")
            if recent.get(j.id, 0) == 0 and j.memorized_ayat:
                reasons.append("بلا تسميع منذ أسبوع")
            row = {"journey_id": j.id, "student_id": j.student_id, "name": j.student.person.display_name_ar, "branch": j.student.branch.name,
                   "avg_retention": j.avg_retention, "memorized_ayat": j.memorized_ayat, "weak_ayat": j.weak_ayat, "critical_ayat": j.critical_ayat,
                   "sessions_7d": recent.get(j.id, 0), "absences_14d": absent.get(j.student_id, 0), "reasons": reasons, "juz_map": j.juz_map,
                   "memorized_pages": len(j.memorized_pages_order or [])}
            (attention if len(reasons) >= 2 else behind if reasons else on_track).append(row)
        halaqat = Halaqah.objects.filter(status="active").prefetch_related("enrollments__student__journey", "staff_assignments__staff__person")
        hrows = []
        for h in halaqat:
            js = [e.student.journey for e in h.enrollments.all() if e.status == "active" and hasattr(e.student, "journey")]
            if not js:
                continue
            hrows.append({"id": h.id, "name": h.name, "students": len(js), "teacher": next((a.staff.person.display_name_ar for a in h.staff_assignments.all()), ""),
                          "avg_retention": round(sum(j.avg_retention for j in js) / len(js), 3),
                          "critical_ayat": sum(j.critical_ayat for j in js), "memorized_pages": sum(len(j.memorized_pages_order or []) for j in js)})
        total = len(attention) + len(behind) + len(on_track)
        return Response({"totals": {"students": total, "on_track": len(on_track), "behind": len(behind), "attention": len(attention),
                                    "avg_retention": round(sum(j.avg_retention for j in journeys) / total, 3) if total else 0},
                         "attention": attention, "behind": behind, "on_track": on_track[:50], "halaqat": sorted(hrows, key=lambda r: r["avg_retention"])})
