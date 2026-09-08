"""Adaptive Planner v1 — deterministic daily plan from policy + memory map. Teachers approve/override."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from packages.quran_core import QuranCore

from .policy import LearningPolicy

PLANNER_VERSION = "planner/v1"
MEMORIZED = {"recent", "strong", "needs_revision", "weak", "critical", "mastered"}


@dataclass(frozen=True)
class AyahSnapshot:
    ayah_index: int
    state: str
    retention_score: float
    next_due_at: datetime | None


@dataclass
class Segment:
    purpose: str                 # new | near | far
    from_ayah_index: int
    to_ayah_index: int
    pages: list[int]
    reason: str
    repetitions_required: int = 1


@dataclass
class Plan:
    plan_date: date
    segments: list[Segment] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    paused_new: bool = False


def _page_index(core: QuranCore, snaps: list[AyahSnapshot]):
    by_page: dict[int, list[AyahSnapshot]] = {}
    for s in snaps:
        by_page.setdefault(core.page_of(s.ayah_index), []).append(s)
    return by_page


def _page_stats(core: QuranCore, page: int, rows: list[AyahSnapshot]):
    total = len(core.page_ayat(page))
    memorized = [r for r in rows if r.state in MEMORIZED]
    if not memorized:
        return None
    avg = sum(r.retention_score for r in memorized) / len(memorized)
    critical = sum(1 for r in memorized if r.state == "critical")
    weak = sum(1 for r in memorized if r.state in ("weak", "critical"))
    return {"coverage": len(memorized) / total, "avg": avg, "critical": critical, "weak": weak, "n": len(memorized)}


def _segments_for_pages(core: QuranCore, purpose: str, pages: list[int], reason: str, reps: int = 1) -> list[Segment]:
    """One segment per run of consecutive pages, so a segment never spans pages the student is not revising."""
    out: list[Segment] = []
    run: list[int] = []
    for p in sorted(set(pages)) + [None]:
        if run and (p is None or p != run[-1] + 1):
            out.append(Segment(purpose, core.page(run[0]).first_ayah_index, core.page(run[-1]).last_ayah_index, list(run), reason, reps))
            run = []
        if p is not None:
            run.append(p)
    return out


def generate(core: QuranCore, policy: LearningPolicy, snaps: list[AyahSnapshot], *, plan_date: date, now: datetime,
             current_ayah_index: int | None, memorized_pages_order: list[int]) -> Plan:
    """memorized_pages_order: pages in the order they were memorized (oldest first)."""
    plan = Plan(plan_date=plan_date)
    by_page = _page_index(core, snaps)
    stats = {p: _page_stats(core, p, rows) for p, rows in by_page.items()}
    stats = {p: s for p, s in stats.items() if s}
    memorized_pages = [p for p in memorized_pages_order if p in stats] or sorted(stats)

    if plan_date.weekday() in policy.weekend_days:
        plan.rationale.append("يوم عطلة حسب السياسة؛ خطة مراجعة خفيفة فقط.")

    # ---- pause conditions ----
    nm = policy.new_memorization
    recent_pages = memorized_pages[-nm.pause_window_pages:] if memorized_pages else []
    crit_recent = sum(stats[p]["critical"] for p in recent_pages)
    due_pages = [p for p in memorized_pages if any(s.next_due_at and s.next_due_at <= now for s in by_page[p])]
    recent_avg = (sum(stats[p]["avg"] for p in recent_pages) / len(recent_pages)) if recent_pages else 1.0
    paused = False
    if nm.daily_amount_pages <= 0:
        paused = True
    elif crit_recent >= nm.pause_when_critical_in_last_pages:
        paused = True
        plan.rationale.append(f"إيقاف الحفظ الجديد مؤقتًا: {crit_recent} آيات حرجة في آخر {nm.pause_window_pages} صفحات.")
    elif len(due_pages) > nm.pause_when_backlog_pages_over:
        paused = True
        plan.rationale.append(f"إيقاف الحفظ الجديد مؤقتًا: تراكم مراجعة {len(due_pages)} صفحة.")
    elif recent_avg < nm.pause_when_recent_retention_below:
        paused = True
        plan.rationale.append(f"إيقاف الحفظ الجديد مؤقتًا: ثبات الصفحات الأخيرة {recent_avg:.0%}.")
    plan.paused_new = paused

    # ---- new memorization ----
    if not paused and current_ayah_index and plan_date.weekday() not in policy.weekend_days:
        page = core.page_of(current_ayah_index)
        page_ayat = core.page_ayat(page)
        remaining = [a for a in page_ayat if a.ayah_index >= current_ayah_index] if nm.direction != "backward" else \
                    [a for a in page_ayat if a.ayah_index >= current_ayah_index]
        target = max(1, round(len(page_ayat) * min(nm.daily_amount_pages, nm.max_daily_pages)))
        chosen = remaining[:target]
        if chosen:
            plan.segments.append(Segment("new", chosen[0].ayah_index, chosen[-1].ayah_index, [page],
                                         f"حفظ جديد: {len(chosen)} آية من صفحة {page}.", policy.near_revision.repetitions_required))
            plan.rationale.append(f"الحفظ الجديد {min(nm.daily_amount_pages, nm.max_daily_pages)} صفحة حسب السياسة.")

    # ---- near revision (Sabqi): last N memorized pages, weakest first ----
    nr = policy.near_revision
    near_pool = memorized_pages[-nr.window_pages:] if nr.window_pages > 0 else []
    if near_pool and nr.daily_amount_pages > 0:
        ranked = sorted(near_pool, key=lambda p: stats[p]["avg"])
        take = ranked[: max(1, round(nr.daily_amount_pages))]
        plan.segments.extend(_segments_for_pages(core, "near", take,
                                                 f"مراجعة قريبة: أضعف {len(take)} من آخر {len(near_pool)} صفحة.", nr.repetitions_required))

    # ---- far revision (Manzil): due pages outside the near window ----
    fr = policy.far_revision
    far_pool = [p for p in memorized_pages if p not in near_pool]
    if far_pool and fr.daily_amount_pages > 0:
        due_far = [p for p in due_pages if p in far_pool]
        if fr.ordering == "weakest_first":
            due_far.sort(key=lambda p: stats[p]["avg"])
        elif fr.ordering == "sequential":
            due_far.sort()
        n = max(1, round(fr.daily_amount_pages))
        take = due_far[:n]
        if len(take) < n:  # keep the cycle moving even when nothing is due yet
            cycle_len = len(far_pool)
            per_day = max(1, round(cycle_len / max(fr.cycle_days, 1)))
            day_no = (plan_date.toordinal()) % max(1, cycle_len // per_day or 1)
            fill = [p for p in sorted(far_pool)[day_no * per_day:(day_no + 1) * per_day] if p not in take]
            take += fill[: n - len(take)]
        if take:
            reason = f"مراجعة بعيدة: {len(take)} صفحة ({'الأضعف أولًا' if fr.ordering == 'weakest_first' else 'بالترتيب'})."
            plan.segments.extend(_segments_for_pages(core, "far", take, reason, 1))
    if not plan.segments:
        plan.rationale.append("لا توجد مقاطع للخطة اليوم.")
    return plan
