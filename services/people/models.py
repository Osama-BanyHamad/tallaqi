from __future__ import annotations

from django.db import models

from packages.permissions.resolve import ScopeAttrs
from services.common.models import TenantModel


class Person(TenantModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    display_name_ar = models.CharField(max_length=200)
    display_name_en = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=8, blank=True)         # male | female
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    photo_key = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=16, default="active")

    class Meta:
        db_table = "people_person"

    def __str__(self):
        return self.display_name_ar

    def scope_attrs(self):
        return ScopeAttrs(person_id=str(self.id))


class Student(TenantModel):
    STATUS = [("applicant", "متقدم"), ("active", "نشط"), ("paused", "متوقف"), ("left", "منسحب"), ("alumni", "خريج")]
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="student")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="students")
    student_code = models.CharField(max_length=32, blank=True)
    level = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="active")
    is_minor = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "people_student"
        unique_together = [("tenant", "student_code")]

    def scope_attrs(self):
        return ScopeAttrs(branch_id=str(self.branch_id), student_id=str(self.id), person_id=str(self.person_id),
                          halaqah_ids=tuple(str(h) for h in self.enrollments.filter(status="active").values_list("halaqah_id", flat=True)))


class Guardian(TenantModel):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="guardian")
    communication_preferences = models.JSONField(default=dict)

    class Meta:
        db_table = "people_guardian"


class GuardianLink(TenantModel):
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name="links")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardian_links")
    relationship = models.CharField(max_length=20, default="parent")
    primary = models.BooleanField(default=True)
    finance_visibility = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "people_guardian_link"
        unique_together = [("guardian", "student")]


class Consent(TenantModel):
    link = models.ForeignKey(GuardianLink, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=24)   # data_processing | media | asr | messaging | recording
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    jurisdiction = models.CharField(max_length=8, blank=True)
    evidence_ref = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "people_consent"


class Staff(TenantModel):
    TYPES = [("teacher", "معلم"), ("assistant", "معلم مساعد"), ("supervisor", "مشرف"), ("admin", "إداري"),
             ("finance", "مالية"), ("hr", "موارد بشرية"), ("instructor", "مدرب"), ("support", "دعم")]
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="staff")
    branch = models.ForeignKey("tenants.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff")
    staff_type = models.CharField(max_length=12, choices=TYPES, default="teacher")
    qualifications = models.JSONField(default=list)
    riwayat = models.JSONField(default=list)
    max_load = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "people_staff"

    def scope_attrs(self):
        return ScopeAttrs(branch_id=str(self.branch_id) if self.branch_id else None, person_id=str(self.person_id))


class Halaqah(TenantModel):
    KINDS = [("in_person", "حضوري"), ("online", "عن بُعد"), ("hybrid", "مدمج")]
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="halaqat")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=12, choices=KINDS, default="in_person")
    gender_policy = models.CharField(max_length=8, default="mixed")
    capacity = models.PositiveSmallIntegerField(default=15)
    riwayah = models.CharField(max_length=32, default="hafs_asim")
    mushaf_type = models.CharField(max_length=32, default="madani_15_line")
    policy_key = models.CharField(max_length=40, default="sabaq_sabqi_manzil")
    schedule_summary = models.CharField(max_length=200, blank=True)   # human-readable until scheduling module lands
    status = models.CharField(max_length=12, default="active")

    class Meta:
        db_table = "people_halaqah"
        unique_together = [("tenant", "branch", "name")]

    def __str__(self):
        return self.name

    def scope_attrs(self):
        return ScopeAttrs(branch_id=str(self.branch_id), halaqah_ids=(str(self.id),))


class HalaqahStaff(TenantModel):
    halaqah = models.ForeignKey(Halaqah, on_delete=models.CASCADE, related_name="staff_assignments")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="halaqah_assignments")
    role = models.CharField(max_length=12, default="teacher")   # teacher | assistant
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "people_halaqah_staff"
        unique_together = [("halaqah", "staff", "role")]


class Enrollment(TenantModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    halaqah = models.ForeignKey(Halaqah, on_delete=models.CASCADE, related_name="enrollments")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, default="active")
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "people_enrollment"


class AttendanceRecord(TenantModel):
    """MVP attendance: one record per student per halaqah per day."""
    STATUS = [("present", "حاضر"), ("absent", "غائب"), ("late", "متأخر"), ("excused", "بعذر"), ("left_early", "انصرف مبكرًا")]
    halaqah = models.ForeignKey(Halaqah, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    on_date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS, default="present")
    reason = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "people_attendance"
        unique_together = [("halaqah", "student", "on_date")]
