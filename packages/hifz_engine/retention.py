"""Retention Engine v1 — deterministic, explainable, no AI.

Educational metric only: it estimates how stable a student's recall of an Ayah is. It is never a
religious judgment of a recitation.

Model: FSRS-style forgetting curve R(t) = 1 / (1 + t / (9·S)), where S (stability, days) is the interval
at which recall probability falls to 0.9. Successful recalls grow S; failures shrink it.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

ENGINE_VERSION = "retention/v1"

DEFAULT_SEVERITY_WEIGHTS = {
    "forgotten_word": 1.0, "incorrect_word": 0.9, "skipped_ayah": 1.0, "repeated_ayah": 0.4,
    "mutashabihat_confusion": 0.8, "harakah": 0.5, "tajweed": 0.3, "makharij": 0.3, "waqf_ibtida": 0.2,
}


@dataclass(frozen=True)
class RetentionPolicy:
    strong_threshold: float = 0.85
    weak_threshold: float = 0.60
    critical_threshold: float = 0.35
    target_retention: float = 0.90
    initial_stability_days: float = 1.0
    min_stability_days: float = 0.5
    max_stability_days: float = 365.0
    mastered_stability_days: float = 120.0
    mastered_min_successes: int = 6
    recent_window_days: int = 7
    severity_weights: dict = field(default_factory=lambda: dict(DEFAULT_SEVERITY_WEIGHTS))
    custom_weight_default: float = 0.5


@dataclass
class AyahState:
    ayah_index: int
    state: str = "not_memorized"
    retention_score: float = 0.0
    stability_days: float = 0.0
    memorized_at: datetime | None = None
    last_recited_at: datetime | None = None
    last_passed_at: datetime | None = None
    success_count: int = 0
    fail_count: int = 0
    consecutive_successes: int = 0
    last_fail_at: datetime | None = None
    next_due_at: datetime | None = None
    student_factor: float = 1.0        # 0.7..1.3, slow-moving per-student adjustment
    override_state: str | None = None


@dataclass(frozen=True)
class Mistake:
    type: str
    severity: str = "major"            # major | minor


@dataclass(frozen=True)
class RecallEvent:
    at: datetime
    purpose: str                        # new | near | far | assessment | review_queue
    passed: bool
    mistakes: tuple[Mistake, ...] = ()
    hints_used: int = 0
    teacher_grade: float | None = None  # 0..100 optional
    marginal: bool = False              # clean Ayah inside a session the teacher marked "repeat": pass, but capped growth


def retention_at(stability_days: float, elapsed_days: float) -> float:
    if stability_days <= 0:
        return 0.0
    if elapsed_days <= 0:
        return 1.0
    return 1.0 / (1.0 + elapsed_days / (9.0 * stability_days))


def weighted_mistakes(event: RecallEvent, policy: RetentionPolicy) -> float:
    total = 0.0
    for m in event.mistakes:
        w = policy.severity_weights.get(m.type, policy.custom_weight_default)
        total += w * (1.0 if m.severity == "major" else 0.5)
    return total


def quality(event: RecallEvent, policy: RetentionPolicy) -> int:
    """5 excellent · 4 good · 3 marginal pass · 0 fail."""
    if not event.passed:
        return 0
    w = weighted_mistakes(event, policy) + 0.25 * event.hints_used
    if event.teacher_grade is not None and event.teacher_grade < 60:
        return 0
    q = 5 if w <= 0.5 else 4 if w <= 1.5 else 3 if w <= 3.0 else 0
    return min(q, 3) if event.marginal and q else q


GROWTH = {5: 2.3, 4: 1.7, 3: 1.25}
PURPOSE_WEIGHT = {"assessment": 1.15, "far": 1.05, "near": 1.0, "new": 1.0, "review_queue": 0.9}


def apply_recall(state: AyahState, event: RecallEvent, policy: RetentionPolicy) -> AyahState:
    s = replace(state)
    q = quality(event, policy)
    elapsed = (event.at - s.last_passed_at).total_seconds() / 86400 if s.last_passed_at else None
    s.last_recited_at = event.at
    if q >= 3:
        if s.memorized_at is None:
            s.memorized_at = event.at
            s.stability_days = policy.initial_stability_days
        else:
            g = GROWTH[q] * PURPOSE_WEIGHT.get(event.purpose, 1.0) * s.student_factor
            if elapsed is not None and s.stability_days > 0 and elapsed >= 0.6 * s.stability_days:
                g *= 1.10   # spacing bonus: recalled after a real interval
            s.stability_days = min(policy.max_stability_days, max(policy.min_stability_days, s.stability_days * g))
        s.last_passed_at = event.at
        s.success_count += 1
        s.consecutive_successes += 1
        s.retention_score = 1.0
    else:
        wm = weighted_mistakes(event, policy)
        shrink = 0.35 if wm >= 1.0 else 0.55
        s.stability_days = max(policy.min_stability_days, s.stability_days * shrink) if s.memorized_at else 0.0
        s.fail_count += 1
        s.consecutive_successes = 0
        s.last_fail_at = event.at
        s.retention_score = 0.4 if s.memorized_at else 0.0
    s.next_due_at = next_due(s, policy)
    s.state = derive_state(s, policy, now=event.at)
    return s


def next_due(state: AyahState, policy: RetentionPolicy) -> datetime | None:
    if state.memorized_at is None or state.last_passed_at is None or state.stability_days <= 0:
        return None
    # t at which R(t) == target: t = 9·S·(1/target − 1)
    days = 9.0 * state.stability_days * (1.0 / policy.target_retention - 1.0)
    return state.last_passed_at + timedelta(days=days)


def decay(state: AyahState, now: datetime, policy: RetentionPolicy) -> AyahState:
    s = replace(state)
    if s.memorized_at is None or s.last_passed_at is None:
        return s
    if s.last_fail_at and (s.last_fail_at > s.last_passed_at):
        base = 0.4
        elapsed = (now - s.last_fail_at).total_seconds() / 86400
        s.retention_score = base * retention_at(max(s.stability_days, policy.min_stability_days), elapsed)
    else:
        elapsed = (now - s.last_passed_at).total_seconds() / 86400
        s.retention_score = retention_at(s.stability_days, elapsed)
    s.next_due_at = next_due(s, policy)
    s.state = derive_state(s, policy, now)
    return s


def derive_state(s: AyahState, policy: RetentionPolicy, now: datetime) -> str:
    if s.override_state:
        return s.override_state
    if s.memorized_at is None:
        return "learning" if s.last_recited_at else "not_memorized"
    if (s.stability_days >= policy.mastered_stability_days and s.consecutive_successes >= policy.mastered_min_successes):
        return "mastered"
    r = s.retention_score
    if r < policy.critical_threshold:
        return "critical"
    if r < policy.weak_threshold:
        return "weak"
    if r < policy.strong_threshold:
        return "needs_revision"
    if (now - s.memorized_at).days <= policy.recent_window_days:
        return "recent"
    return "strong"


def explain(s: AyahState, now: datetime) -> list[str]:
    out = []
    if s.memorized_at is None:
        out.append("لم يُسمَّع هذا الموضع بعد كحفظ جديد.")
        return out
    if s.last_passed_at:
        d = (now - s.last_passed_at).days
        out.append(f"آخر تسميع ناجح قبل {d} يوم." if d != 1 else "آخر تسميع ناجح أمس.")
    if s.last_fail_at and s.last_passed_at and s.last_fail_at > s.last_passed_at:
        out.append("آخر تسميع لم يُجتَز.")
    out.append(f"ثبات الحفظ التقديري {s.stability_days:.0f} يومًا بعد {s.success_count} تسميعًا ناجحًا و{s.fail_count} غير ناجح.")
    if s.next_due_at:
        due = (s.next_due_at - now).days
        out.append("موعد المراجعة حلّ." if due <= 0 else f"المراجعة القادمة خلال {due} يوم.")
    return out
