"""Learning Policy schema (Pydantic) and shipped templates."""
from __future__ import annotations

from pydantic import BaseModel, Field


class NewMemorization(BaseModel):
    daily_amount_pages: float = Field(0.5, ge=0, le=5)
    max_daily_pages: float = 1.0
    direction: str = "backward"                # backward (from Juz 30) | forward | custom
    pause_when_critical_in_last_pages: int = 3   # count of critical ayat in the last N memorized pages
    pause_window_pages: int = 5
    pause_when_backlog_pages_over: int = 10
    pause_when_recent_retention_below: float = 0.70


class NearRevision(BaseModel):
    window_pages: int = 20
    daily_amount_pages: float = 2.0
    repetitions_required: int = 3


class FarRevision(BaseModel):
    cycle_days: int = 30
    daily_amount_pages: float = 4.0
    ordering: str = "weakest_first"            # weakest_first | sequential | mixed


class Mastery(BaseModel):
    strong_threshold: float = 0.85
    weak_threshold: float = 0.60
    critical_threshold: float = 0.35
    target_retention: float = 0.90
    mastered_after_recalls: int = 6


class Assessment(BaseModel):
    juz_exam_required: bool = True
    passing_score: int = 90
    max_major_mistakes: int = 2


class LearningPolicy(BaseModel):
    key: str
    name_ar: str
    name_en: str = ""
    version: int = 1
    units: str = "page"
    new_memorization: NewMemorization = NewMemorization()
    near_revision: NearRevision = NearRevision()
    far_revision: FarRevision = FarRevision()
    mastery: Mastery = Mastery()
    assessment: Assessment = Assessment()
    weekend_days: list[int] = [4]              # 0=Mon … 4=Fri
    auto_approve_plans: bool = True


TEMPLATES: dict[str, LearningPolicy] = {
    "sabaq_sabqi_manzil": LearningPolicy(key="sabaq_sabqi_manzil", name_ar="سبق · سبقي · منزل", name_en="Sabaq / Sabqi / Manzil"),
    "page_weekly": LearningPolicy(key="page_weekly", name_ar="صفحة أسبوعيًا", name_en="Page-based weekly",
                                  new_memorization=NewMemorization(daily_amount_pages=0.2, max_daily_pages=0.5),
                                  near_revision=NearRevision(window_pages=10, daily_amount_pages=1.0),
                                  far_revision=FarRevision(cycle_days=45, daily_amount_pages=2.0)),
    "children_ayah": LearningPolicy(key="children_ayah", name_ar="آيات للصغار", name_en="Ayah-based for children", units="ayah",
                                    new_memorization=NewMemorization(daily_amount_pages=0.15, max_daily_pages=0.3),
                                    near_revision=NearRevision(window_pages=5, daily_amount_pages=0.5),
                                    far_revision=FarRevision(cycle_days=60, daily_amount_pages=1.0)),
    "post_hifz_40": LearningPolicy(key="post_hifz_40", name_ar="مراجعة ما بعد الختم (40 يومًا)", name_en="Post-Hifz 40-day cycle",
                                   new_memorization=NewMemorization(daily_amount_pages=0.0, max_daily_pages=0.0),
                                   near_revision=NearRevision(window_pages=0, daily_amount_pages=0.0),
                                   far_revision=FarRevision(cycle_days=40, daily_amount_pages=15.0, ordering="mixed")),
}
