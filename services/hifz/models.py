from __future__ import annotations

from django.db import models

from packages.permissions.resolve import ScopeAttrs
from services.common.models import TenantModel


class QuranJourney(TenantModel):
    STATUS = [("memorizing", "في الحفظ"), ("retaining", "في المراجعة الطويلة"), ("paused", "متوقف"),
              ("completed_with_retention", "أتمّ الختم"), ("ijazah_track", "مسار الإجازة")]
    student = models.OneToOneField("people.Student", on_delete=models.CASCADE, related_name="journey")
    riwayah = models.CharField(max_length=32, default="hafs_asim")
    mushaf_type = models.CharField(max_length=32, default="madani_15_line")
    policy_key = models.CharField(max_length=40, default="sabaq_sabqi_manzil")
    policy_overrides = models.JSONField(default=dict)
    status = models.CharField(max_length=32, choices=STATUS, default="memorizing")
    started_at = models.DateField()
    direction = models.CharField(max_length=12, default="backward")
    current_ayah_index = models.PositiveIntegerField(null=True, blank=True)   # next ayah to memorize
    level = models.CharField(max_length=40, blank=True)
    quran_core_version = models.CharField(max_length=20, default="0.1.0")
    # materialized aggregates (refreshed on write + daily)
    memorized_ayat = models.PositiveIntegerField(default=0)
    strong_ayat = models.PositiveIntegerField(default=0)
    needs_revision_ayat = models.PositiveIntegerField(default=0)
    weak_ayat = models.PositiveIntegerField(default=0)
    critical_ayat = models.PositiveIntegerField(default=0)
    mastered_ayat = models.PositiveIntegerField(default=0)
    avg_retention = models.FloatField(default=0.0)
    memorized_pages_order = models.JSONField(default=list)     # pages in the order memorized (oldest first)

    class Meta:
        db_table = "hifz_journey"

    def scope_attrs(self):
        return self.student.scope_attrs()


class JourneyEvent(TenantModel):
    journey = models.ForeignKey(QuranJourney, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=40)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    actor = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "hifz_journey_event"
        ordering = ["-occurred_at"]


class StudentAyahState(TenantModel):
    """Current projection of the Memory Map. History lives in AyahStateEvent."""
    journey = models.ForeignKey(QuranJourney, on_delete=models.CASCADE, related_name="ayah_states")
    ayah_index = models.PositiveIntegerField()
    state = models.CharField(max_length=16, default="not_memorized")
    retention_score = models.FloatField(default=0.0)
    stability_days = models.FloatField(default=0.0)
    memorized_at = models.DateTimeField(null=True, blank=True)
    last_recited_at = models.DateTimeField(null=True, blank=True)
    last_passed_at = models.DateTimeField(null=True, blank=True)
    last_fail_at = models.DateTimeField(null=True, blank=True)
    success_count = models.PositiveIntegerField(default=0)
    fail_count = models.PositiveIntegerField(default=0)
    consecutive_successes = models.PositiveIntegerField(default=0)
    next_due_at = models.DateTimeField(null=True, blank=True)
    student_factor = models.FloatField(default=1.0)
    override_state = models.CharField(max_length=16, blank=True, null=True)
    engine_version = models.CharField(max_length=20, default="retention/v1")

    class Meta:
        db_table = "hifz_ayah_state"
        unique_together = [("journey", "ayah_index")]
        indexes = [models.Index(fields=["journey", "next_due_at"]), models.Index(fields=["journey", "state"])]


class AyahStateEvent(TenantModel):
    journey = models.ForeignKey(QuranJourney, on_delete=models.CASCADE, related_name="ayah_events")
    ayah_index = models.PositiveIntegerField()
    prev_state = models.CharField(max_length=16)
    new_state = models.CharField(max_length=16)
    prev_score = models.FloatField()
    new_score = models.FloatField()
    cause = models.CharField(max_length=16)     # recitation | decay | override | import | assessment
    cause_ref = models.UUIDField(null=True, blank=True)
    engine_version = models.CharField(max_length=20)
    occurred_at = models.DateTimeField()

    class Meta:
        db_table = "hifz_ayah_state_event"
        indexes = [models.Index(fields=["journey", "ayah_index", "occurred_at"])]


class DailyPlan(TenantModel):
    STATUS = [("proposed", "مقترحة"), ("approved", "معتمدة"), ("edited", "معدّلة"), ("overridden", "مستبدلة"),
              ("done", "منجزة"), ("carried", "مرحّلة")]
    journey = models.ForeignKey(QuranJourney, on_delete=models.CASCADE, related_name="plans")
    plan_date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS, default="proposed")
    rationale = models.JSONField(default=list)
    paused_new = models.BooleanField(default=False)
    planner_version = models.CharField(max_length=20, default="planner/v1")
    approved_by = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "hifz_daily_plan"
        unique_together = [("journey", "plan_date")]

    def scope_attrs(self):
        return self.journey.student.scope_attrs()


class PlanSegment(TenantModel):
    plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name="segments")
    purpose = models.CharField(max_length=16)         # new | near | far | mutashabihat | assessment
    from_ayah_index = models.PositiveIntegerField()
    to_ayah_index = models.PositiveIntegerField()
    pages = models.JSONField(default=list)
    reason = models.CharField(max_length=200, blank=True)
    repetitions_required = models.PositiveSmallIntegerField(default=1)
    completion = models.CharField(max_length=16, default="pending")   # pending | self_reported | verified
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "hifz_plan_segment"
        ordering = ["order"]


class PlanAction(TenantModel):
    plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name="actions")
    action = models.CharField(max_length=16)           # approve | edit | override | carry_forward
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    actor = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "hifz_plan_action"


class MistakeType(TenantModel):
    """Tenant custom mistake types (standard ones live in the engine catalog)."""
    key = models.CharField(max_length=40)
    name_ar = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True)
    default_weight = models.FloatField(default=0.5)
    default_severity = models.CharField(max_length=8, default="minor")

    class Meta:
        db_table = "hifz_mistake_type"
        unique_together = [("tenant", "key")]


STANDARD_MISTAKE_TYPES = [
    {"key": "forgotten_word", "name_ar": "نسيان كلمة", "name_en": "Forgotten word", "severity": "major"},
    {"key": "incorrect_word", "name_ar": "كلمة خاطئة", "name_en": "Incorrect word", "severity": "major"},
    {"key": "skipped_ayah", "name_ar": "تجاوز آية", "name_en": "Skipped Ayah", "severity": "major"},
    {"key": "repeated_ayah", "name_ar": "تكرار آية", "name_en": "Repeated Ayah", "severity": "minor"},
    {"key": "mutashabihat_confusion", "name_ar": "التباس متشابه", "name_en": "Mutashabihat confusion", "severity": "major"},
    {"key": "harakah", "name_ar": "خطأ حركة", "name_en": "Harakah", "severity": "minor"},
    {"key": "tajweed", "name_ar": "خطأ تجويد", "name_en": "Tajweed", "severity": "minor"},
    {"key": "makharij", "name_ar": "خطأ مخرج", "name_en": "Makharij", "severity": "minor"},
    {"key": "waqf_ibtida", "name_ar": "وقف وابتداء", "name_en": "Waqf / Ibtida", "severity": "minor"},
]


class RecitationSession(TenantModel):
    OUTCOME = [("pass", "اجتاز"), ("repeat", "يعيد"), ("partial", "جزئي")]
    journey = models.ForeignKey(QuranJourney, on_delete=models.CASCADE, related_name="sessions")
    teacher = models.ForeignKey("people.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    halaqah = models.ForeignKey("people.Halaqah", null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    plan_segment = models.ForeignKey(PlanSegment, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    purpose = models.CharField(max_length=16, default="near")      # new | near | far | assessment | review_queue
    from_ayah_index = models.PositiveIntegerField()
    to_ayah_index = models.PositiveIntegerField()
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=8, choices=OUTCOME, default="pass")
    grade = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True)
    note_visibility = models.CharField(max_length=12, default="parent")   # private | supervisor | parent
    source = models.CharField(max_length=16, default="in_person")          # in_person | live | review_queue | assessment
    idempotency_key = models.CharField(max_length=64, blank=True)
    recorded_by = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "hifz_recitation_session"
        indexes = [models.Index(fields=["journey", "started_at"])]
        constraints = [models.UniqueConstraint(fields=["tenant", "idempotency_key"], condition=models.Q(idempotency_key__gt=""),
                                               name="uniq_recitation_idempotency")]

    def scope_attrs(self):
        return self.journey.student.scope_attrs()


class MistakeEvent(TenantModel):
    session = models.ForeignKey(RecitationSession, on_delete=models.CASCADE, related_name="mistakes")
    ayah_index = models.PositiveIntegerField()
    word_position = models.PositiveSmallIntegerField(null=True, blank=True)
    mistake_type = models.CharField(max_length=40)
    severity = models.CharField(max_length=8, default="major")
    confused_with_ayah_index = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "hifz_mistake_event"
        indexes = [models.Index(fields=["session"]), models.Index(fields=["ayah_index"])]
