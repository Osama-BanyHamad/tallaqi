"""Daily reading (wird): a personal plan through the Mushaf by pages, independent of memorization.

Owned by a Person (not a Student), so teachers, parents, and independent learners can all keep a wird.
"""
from __future__ import annotations

from django.db import models

from packages.permissions.resolve import ScopeAttrs
from services.common.models import TenantModel

MUSHAF_PAGES = 604


class ReadingPlan(TenantModel):
    KINDS = [("khatmah", "ختمة"), ("pages", "صفحات يوميًا")]
    STATUS = [("active", "نشطة"), ("paused", "متوقفة"), ("completed", "مكتملة")]

    person = models.ForeignKey("people.Person", on_delete=models.CASCADE, related_name="reading_plans")
    kind = models.CharField(max_length=12, choices=KINDS, default="khatmah")
    pages_per_day = models.PositiveSmallIntegerField(default=2)
    current_page = models.PositiveSmallIntegerField(default=1)   # next page to read
    start_page = models.PositiveSmallIntegerField(default=1)
    riwayah = models.CharField(max_length=32, default="hafs_asim")
    status = models.CharField(max_length=12, choices=STATUS, default="active")
    started_on = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    khatmat = models.PositiveSmallIntegerField(default=0)         # completed cycles on this plan
    reminder_time = models.CharField(max_length=5, blank=True)    # "HH:MM" local; the device schedules the notification

    class Meta:
        db_table = "reading_plan"
        indexes = [models.Index(fields=["tenant", "person", "status"])]

    def scope_attrs(self):
        return ScopeAttrs(person_id=str(self.person_id))

    @property
    def pages_done(self) -> int:
        return self.current_page - self.start_page + self.khatmat * MUSHAF_PAGES

    @property
    def progress(self) -> float:
        """0..1 of the current cycle."""
        return max(0.0, min(1.0, (self.current_page - 1) / MUSHAF_PAGES))


class ReadingLog(TenantModel):
    plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE, related_name="logs")
    on_date = models.DateField()
    from_page = models.PositiveSmallIntegerField()
    to_page = models.PositiveSmallIntegerField()
    minutes = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "reading_log"
        indexes = [models.Index(fields=["tenant", "plan", "on_date"])]

    def scope_attrs(self):
        return ScopeAttrs(person_id=str(self.plan.person_id))
