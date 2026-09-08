from datetime import UTC, date, datetime, timedelta

from packages.hifz_engine import (
    TEMPLATES,
    AyahSnapshot,
    AyahState,
    Mistake,
    RecallEvent,
    RetentionPolicy,
    apply_recall,
    decay,
    explain,
    generate,
)
from packages.hifz_engine.retention import retention_at
from packages.quran_core import get_core

T0 = datetime(2026, 1, 1, tzinfo=UTC)
P = RetentionPolicy()


def ev(at, passed=True, mistakes=(), purpose="near", hints=0):
    return RecallEvent(at=at, purpose=purpose, passed=passed, mistakes=tuple(mistakes), hints_used=hints)


def test_forgetting_curve_shape():
    assert retention_at(10, 0) == 1.0
    assert abs(retention_at(10, 10) - 0.9) < 1e-9
    assert retention_at(10, 100) < retention_at(10, 10)


def test_first_pass_memorizes_and_grows_with_spaced_successes():
    s = AyahState(ayah_index=1)
    s = apply_recall(s, ev(T0, purpose="new"), P)
    assert s.memorized_at == T0 and s.state == "recent" and s.stability_days == P.initial_stability_days
    s1 = apply_recall(s, ev(T0 + timedelta(days=1)), P)
    s2 = apply_recall(s1, ev(T0 + timedelta(days=4)), P)
    assert s2.stability_days > s1.stability_days > s.stability_days
    assert s2.success_count == 3 and s2.next_due_at > T0 + timedelta(days=4)


def test_failure_shrinks_stability_and_marks_weak_or_critical():
    s = AyahState(ayah_index=1)
    for d in (0, 2, 6, 14):
        s = apply_recall(s, ev(T0 + timedelta(days=d)), P)
    before = s.stability_days
    s = apply_recall(s, ev(T0 + timedelta(days=20), passed=False, mistakes=[Mistake("forgotten_word")]), P)
    assert s.stability_days < before and s.fail_count == 1 and s.state in ("weak", "critical")


def test_minor_mistakes_still_pass_with_smaller_growth():
    s = apply_recall(AyahState(1), ev(T0, purpose="new"), P)
    clean = apply_recall(s, ev(T0 + timedelta(days=2)), P)
    tajweed = apply_recall(s, ev(T0 + timedelta(days=2), mistakes=[Mistake("tajweed", "minor"), Mistake("waqf_ibtida", "minor")]), P)
    assert tajweed.success_count == 2 and tajweed.stability_days <= clean.stability_days


def test_decay_moves_state_down_over_time_and_is_deterministic():
    s = apply_recall(AyahState(1), ev(T0, purpose="new"), P)
    s = apply_recall(s, ev(T0 + timedelta(days=3)), P)
    d10 = decay(s, T0 + timedelta(days=13), P)
    d60 = decay(s, T0 + timedelta(days=63), P)
    assert d10.retention_score > d60.retention_score
    assert decay(s, T0 + timedelta(days=63), P) == d60
    assert d60.state in ("needs_revision", "weak", "critical")


def test_explanations_are_arabic_and_present():
    s = apply_recall(AyahState(1), ev(T0, purpose="new"), P)
    lines = explain(s, T0 + timedelta(days=3))
    assert lines and any("تسميع" in ln for ln in lines)


def test_planner_produces_new_near_far_segments():
    core = get_core()
    pol = TEMPLATES["sabaq_sabqi_manzil"]
    now = T0 + timedelta(days=100)
    # Student memorized pages 582..604 (Juz 30) at various strengths; current position is start of page 581.
    snaps, order = [], []
    for page in range(604, 581, -1):
        order.append(page)
        for a in core.page_ayat(page):
            age = (604 - page) * 4
            score = 0.95 if page > 598 else (0.5 if page in (590, 591) else 0.75)
            snaps.append(AyahSnapshot(a.ayah_index, "strong" if score > 0.85 else ("weak" if score < 0.6 else "needs_revision"),
                                      score, now - timedelta(days=1) if page < 587 else now + timedelta(days=age + 1)))
    plan = generate(core, pol, snaps, plan_date=date(2026, 4, 13), now=now,
                    current_ayah_index=core.page(581).first_ayah_index, memorized_pages_order=order)
    purposes = [s.purpose for s in plan.segments]
    assert "new" in purposes and "near" in purposes and "far" in purposes
    new = next(s for s in plan.segments if s.purpose == "new")
    assert core.page_of(new.from_ayah_index) == 581
    near = next(s for s in plan.segments if s.purpose == "near")
    assert set(near.pages) <= set(order[-20:])
    assert 590 in near.pages or 591 in near.pages   # weakest pages come first


def test_planner_pauses_new_when_backlog_is_large():
    core = get_core()
    pol = TEMPLATES["sabaq_sabqi_manzil"]
    now = T0
    snaps, order = [], []
    for page in range(604, 560, -1):
        order.append(page)
        for a in core.page_ayat(page):
            snaps.append(AyahSnapshot(a.ayah_index, "critical", 0.2, now - timedelta(days=5)))
    plan = generate(core, pol, snaps, plan_date=date(2026, 1, 5), now=now,
                    current_ayah_index=core.page(559).first_ayah_index, memorized_pages_order=order)
    assert plan.paused_new and not any(s.purpose == "new" for s in plan.segments)
    assert any("إيقاف" in r for r in plan.rationale)
