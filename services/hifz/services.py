"""Domain services for the Quran learning loop. Views call these; workers call these. No business logic in views."""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone

from django.db import transaction

from packages.hifz_engine import (ENGINE_VERSION, PLANNER_VERSION, TEMPLATES, AyahSnapshot, AyahState, LearningPolicy, Mistake,
                                  RecallEvent, RetentionPolicy, apply_recall, decay, explain, generate)
from packages.quran_core import get_core
from services.common.exceptions import DomainError

from .models import (AyahStateEvent, DailyPlan, JourneyEvent, MistakeEvent, PlanAction, PlanSegment, QuranJourney,
                     RecitationSession, StudentAyahState)

MEMORIZED = {"recent", "strong", "needs_revision", "weak", "critical", "mastered"}


# ---- policy ------------------------------------------------------------------------------
def policy_for(journey: QuranJourney) -> LearningPolicy:
    base = TEMPLATES.get(journey.policy_key, TEMPLATES["sabaq_sabqi_manzil"])
    if journey.policy_overrides:
        return base.model_copy(update=journey.policy_overrides, deep=True)
    return base


def retention_policy_for(policy: LearningPolicy) -> RetentionPolicy:
    m = policy.mastery
    return RetentionPolicy(strong_threshold=m.strong_threshold, weak_threshold=m.weak_threshold,
                           critical_threshold=m.critical_threshold, target_retention=m.target_retention,
                           mastered_min_successes=m.mastered_after_recalls)


# ---- state conversion ----------------------------------------------------------------------
def _to_engine(row: StudentAyahState) -> AyahState:
    return AyahState(ayah_index=row.ayah_index, state=row.state, retention_score=row.retention_score,
                     stability_days=row.stability_days, memorized_at=row.memorized_at, last_recited_at=row.last_recited_at,
                     last_passed_at=row.last_passed_at, success_count=row.success_count, fail_count=row.fail_count,
                     consecutive_successes=row.consecutive_successes, last_fail_at=row.last_fail_at,
                     next_due_at=row.next_due_at, student_factor=row.student_factor, override_state=row.override_state or None)


def _from_engine(row: StudentAyahState, s: AyahState) -> None:
    for f in ("state", "retention_score", "stability_days", "memorized_at", "last_recited_at", "last_passed_at",
              "success_count", "fail_count", "consecutive_successes", "last_fail_at", "next_due_at", "student_factor"):
        setattr(row, f, getattr(s, f))
    row.engine_version = ENGINE_VERSION


# ---- recitation ----------------------------------------------------------------------------
@transaction.atomic
def record_recitation(journey: QuranJourney, *, teacher=None, halaqah=None, purpose: str, from_ayah_index: int,
                      to_ayah_index: int, outcome: str, mistakes: list[dict], note: str = "", note_visibility="parent",
                      grade: float | None = None, plan_segment: PlanSegment | None = None, source="in_person",
                      idempotency_key: str = "", recorded_by=None, at: datetime | None = None, refresh: bool = True) -> RecitationSession:
    core = get_core(journey.riwayah)
    if not (1 <= from_ayah_index <= to_ayah_index <= core.ayah_count):
        raise DomainError("Invalid ayah range.")
    if idempotency_key:
        existing = RecitationSession.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing
    at = at or datetime.now(timezone.utc)
    policy = policy_for(journey)
    rp = retention_policy_for(policy)
    session = RecitationSession.objects.create(
        tenant_id=journey.tenant_id, journey=journey, teacher=teacher, halaqah=halaqah, plan_segment=plan_segment,
        purpose=purpose, from_ayah_index=from_ayah_index, to_ayah_index=to_ayah_index, started_at=at, ended_at=at,
        outcome=outcome, grade=grade, note=note, note_visibility=note_visibility, source=source,
        idempotency_key=idempotency_key, recorded_by=recorded_by)
    by_ayah: dict[int, list[Mistake]] = {}
    for m in mistakes:
        idx = int(m["ayah_index"])
        if not (from_ayah_index <= idx <= to_ayah_index):
            raise DomainError(f"Mistake outside recited range: {idx}")
        MistakeEvent.objects.create(tenant_id=journey.tenant_id, session=session, ayah_index=idx,
                                    word_position=m.get("word_position"), mistake_type=m["mistake_type"],
                                    severity=m.get("severity", "major"), confused_with_ayah_index=m.get("confused_with_ayah_index"),
                                    note=m.get("note", ""))
        by_ayah.setdefault(idx, []).append(Mistake(m["mistake_type"], m.get("severity", "major")))

    existing = {r.ayah_index: r for r in StudentAyahState.objects.filter(journey=journey, ayah_index__gte=from_ayah_index,
                                                                         ayah_index__lte=to_ayah_index)}
    events, to_create, to_update = [], [], []
    passed_all = outcome == "pass"
    for idx in range(from_ayah_index, to_ayah_index + 1):
        row = existing.get(idx) or StudentAyahState(tenant_id=journey.tenant_id, journey=journey, ayah_index=idx)
        before = _to_engine(row)
        ayah_mistakes = tuple(by_ayah.get(idx, ()))
        # pass: every Ayah passes (mistakes still lower quality) · partial: Ayat without a major mistake pass
        # repeat: only Ayat with no mistake at all pass, and with capped growth (marginal)
        if passed_all:
            ayah_passed, marginal = True, False
        elif outcome == "partial":
            ayah_passed, marginal = not any(m.severity == "major" for m in ayah_mistakes), False
        else:
            ayah_passed, marginal = not ayah_mistakes, True
        after = apply_recall(before, RecallEvent(at=at, purpose=purpose, passed=ayah_passed, mistakes=ayah_mistakes,
                                                 teacher_grade=grade, marginal=marginal), rp)
        _from_engine(row, after)
        (to_update if row.pk and idx in existing else to_create).append(row)
        events.append(AyahStateEvent(tenant_id=journey.tenant_id, journey=journey, ayah_index=idx, prev_state=before.state,
                                     new_state=after.state, prev_score=before.retention_score, new_score=after.retention_score,
                                     cause="recitation" if purpose != "assessment" else "assessment", cause_ref=session.id,
                                     engine_version=ENGINE_VERSION, occurred_at=at))
    StudentAyahState.objects.bulk_create(to_create)
    StudentAyahState.objects.bulk_update(to_update, ["state", "retention_score", "stability_days", "memorized_at", "last_recited_at",
                                                     "last_passed_at", "success_count", "fail_count", "consecutive_successes",
                                                     "last_fail_at", "next_due_at", "student_factor", "engine_version"])
    AyahStateEvent.objects.bulk_create(events)

    # advance position for new memorization
    if purpose == "new" and passed_all and journey.current_ayah_index and to_ayah_index >= journey.current_ayah_index:
        journey.current_ayah_index = _next_position(core, journey, to_ayah_index)
    _record_pages_order(core, journey, from_ayah_index, to_ayah_index, purpose, passed_all)
    if refresh:
        refresh_aggregates(journey)
        _emit_milestones(core, journey, at, before_ev=events)
    else:
        journey.save(update_fields=["current_ayah_index", "memorized_pages_order", "updated_at"])
    if plan_segment is not None and passed_all:
        plan_segment.completion = "verified"
        plan_segment.save(update_fields=["completion"])
    return session


def _next_position(core, journey: QuranJourney, last_done: int) -> int | None:
    """Backward direction: surah by surah from An-Nas downwards, ayat ascending inside a surah."""
    a = core.ayah_by_index(last_done)
    surah = core.surah(a.surah)
    if journey.direction == "backward":
        if a.ayah < surah.ayah_count:
            return last_done + 1
        return core.surah(a.surah - 1).start_index if a.surah > 1 else None
    return last_done + 1 if last_done < core.ayah_count else None


def _record_pages_order(core, journey: QuranJourney, first: int, last: int, purpose: str, passed: bool) -> None:
    if purpose != "new" or not passed:
        return
    order = list(journey.memorized_pages_order or [])
    for p in range(core.page_of(first), core.page_of(last) + 1):
        if p not in order:
            order.append(p)
    journey.memorized_pages_order = order


def refresh_aggregates(journey: QuranJourney) -> None:
    rows = StudentAyahState.objects.filter(journey=journey).values_list("state", "retention_score")
    counts = {"recent": 0, "strong": 0, "needs_revision": 0, "weak": 0, "critical": 0, "mastered": 0}
    total, score_sum = 0, 0.0
    for state, score in rows:
        if state in counts:
            counts[state] += 1
            total += 1
            score_sum += score
    journey.memorized_ayat = total
    journey.strong_ayat = counts["strong"] + counts["recent"]
    journey.needs_revision_ayat = counts["needs_revision"]
    journey.weak_ayat = counts["weak"]
    journey.critical_ayat = counts["critical"]
    journey.mastered_ayat = counts["mastered"]
    journey.avg_retention = round(score_sum / total, 4) if total else 0.0
    journey.save()


def _emit_milestones(core, journey: QuranJourney, at: datetime, before_ev) -> None:
    newly = [e.ayah_index for e in before_ev if e.prev_state in ("not_memorized", "learning") and e.new_state in MEMORIZED]
    if not newly:
        return
    memorized = set(StudentAyahState.objects.filter(journey=journey, state__in=MEMORIZED).values_list("ayah_index", flat=True))
    existing = set(JourneyEvent.objects.filter(journey=journey).values_list("event_type", flat=True))
    if "journey.first_memorization" not in existing:
        JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="journey.first_memorization", occurred_at=at)
    for idx in newly:
        a = core.ayah_by_index(idx)
        s = core.surah(a.surah)
        if all(i in memorized for i in range(s.start_index, s.start_index + s.ayah_count)):
            key = f"surah.completed:{s.number}"
            if key not in existing:
                JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="surah.completed",
                                            payload={"surah": s.number, "name_ar": s.name_ar}, occurred_at=at)
                existing.add(key)
        juz = core.unit("juz", core.juz_of(idx))
        if all(i in memorized for i in range(juz.first_ayah_index, juz.last_ayah_index + 1)):
            key = f"juz.completed:{juz.number}"
            if key not in existing:
                JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="juz.completed",
                                            payload={"juz": juz.number}, occurred_at=at)
                existing.add(key)


def recompute_milestones(journey: QuranJourney, now: datetime) -> None:
    """Backfill milestone events from the current map (used after bulk imports/simulations)."""
    core = get_core(journey.riwayah)
    memorized = set(StudentAyahState.objects.filter(journey=journey, state__in=MEMORIZED).values_list("ayah_index", flat=True))
    if not memorized:
        return
    existing = set(JourneyEvent.objects.filter(journey=journey).values_list("event_type", flat=True))
    first_at = StudentAyahState.objects.filter(journey=journey, memorized_at__isnull=False).order_by("memorized_at").values_list("memorized_at", flat=True).first() or now
    if "journey.first_memorization" not in existing:
        JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="journey.first_memorization", occurred_at=first_at)
    for s in core.surahs:
        rng = range(s.start_index, s.start_index + s.ayah_count)
        if all(i in memorized for i in rng) and not JourneyEvent.objects.filter(journey=journey, event_type="surah.completed", payload__surah=s.number).exists():
            at = StudentAyahState.objects.filter(journey=journey, ayah_index__in=list(rng)).order_by("-memorized_at").values_list("memorized_at", flat=True).first() or now
            JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="surah.completed", payload={"surah": s.number, "name_ar": s.name_ar}, occurred_at=at)
    for u in core.units_of("juz"):
        rng = range(u.first_ayah_index, u.last_ayah_index + 1)
        if all(i in memorized for i in rng) and not JourneyEvent.objects.filter(journey=journey, event_type="juz.completed", payload__juz=u.number).exists():
            at = StudentAyahState.objects.filter(journey=journey, ayah_index__in=list(rng)).order_by("-memorized_at").values_list("memorized_at", flat=True).first() or now
            JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="juz.completed", payload={"juz": u.number}, occurred_at=at)


# ---- decay / daily ---------------------------------------------------------------------------
@transaction.atomic
def run_decay(journey: QuranJourney, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    rp = retention_policy_for(policy_for(journey))
    rows = list(StudentAyahState.objects.filter(journey=journey, memorized_at__isnull=False))
    changed, events = [], []
    for row in rows:
        before = _to_engine(row)
        after = decay(before, now, rp)
        if abs(after.retention_score - before.retention_score) > 1e-6 or after.state != before.state:
            _from_engine(row, after)
            changed.append(row)
            if after.state != before.state:
                events.append(AyahStateEvent(tenant_id=journey.tenant_id, journey=journey, ayah_index=row.ayah_index,
                                             prev_state=before.state, new_state=after.state, prev_score=before.retention_score,
                                             new_score=after.retention_score, cause="decay", engine_version=ENGINE_VERSION, occurred_at=now))
    StudentAyahState.objects.bulk_update(changed, ["state", "retention_score", "next_due_at", "engine_version"], batch_size=1000)
    AyahStateEvent.objects.bulk_create(events)
    refresh_aggregates(journey)
    return len(changed)


# ---- memory map projections -----------------------------------------------------------------
def memory_map(journey: QuranJourney, level: str = "juz", number: int | None = None, now: datetime | None = None) -> dict:
    core = get_core(journey.riwayah)
    now = now or datetime.now(timezone.utc)
    rows = {r.ayah_index: r for r in StudentAyahState.objects.filter(journey=journey)}

    def agg(first: int, last: int) -> dict:
        total = last - first + 1
        counts = {"not_memorized": 0, "learning": 0, "recent": 0, "strong": 0, "needs_revision": 0, "weak": 0, "critical": 0, "mastered": 0}
        score_sum, n = 0.0, 0
        due = 0
        for i in range(first, last + 1):
            r = rows.get(i)
            st = r.state if r else "not_memorized"
            counts[st] = counts.get(st, 0) + 1
            if r and st in MEMORIZED:
                score_sum += r.retention_score
                n += 1
                if r.next_due_at and r.next_due_at <= now:
                    due += 1
        avg = score_sum / n if n else None
        if n == 0:
            state = "not_memorized" if counts["learning"] == 0 else "learning"
        elif counts["critical"] > 0 or (n and counts["weak"] / n >= 0.3):
            state = "critical" if counts["critical"] >= 2 else "weak"
        elif avg is not None and avg < 0.85:
            state = "needs_revision"
        elif counts["mastered"] == n:
            state = "mastered"
        else:
            state = "strong"
        return {"first_ayah_index": first, "last_ayah_index": last, "total_ayat": total, "memorized_ayat": n,
                "coverage": round(n / total, 3), "avg_retention": round(avg, 3) if avg is not None else None,
                "state": state, "counts": counts, "due_ayat": due}

    if level == "quran":
        return {"level": "quran", "units": [{"number": u.number, **agg(u.first_ayah_index, u.last_ayah_index)} for u in core.units_of("juz")]}
    if level == "pages":   # every page in one call: powers the folio strip
        return {"level": "pages", "units": [{"number": p.page, "juz": p.juz, **{k: v for k, v in agg(p.first_ayah_index, p.last_ayah_index).items() if k != "counts"}}
                                            for p in core.pages]}
    if level == "juz":
        u = core.unit("juz", number)
        pages = [p for p in core.pages if u.first_ayah_index <= p.first_ayah_index <= u.last_ayah_index]
        return {"level": "juz", "number": number, **agg(u.first_ayah_index, u.last_ayah_index),
                "units": [{"number": p.page, **agg(p.first_ayah_index, p.last_ayah_index)} for p in pages]}
    if level == "surah":
        s = core.surah(number)
        first, last = s.start_index, s.start_index + s.ayah_count - 1
        return {"level": "surah", "number": number, "name_ar": s.name_ar, **agg(first, last),
                "units": [ayah_detail(core, rows.get(i), i, now) for i in range(first, last + 1)]}
    if level == "page":
        p = core.page(number)
        return {"level": "page", "number": number, "juz": p.juz, **agg(p.first_ayah_index, p.last_ayah_index),
                "units": [ayah_detail(core, rows.get(i), i, now) for i in range(p.first_ayah_index, p.last_ayah_index + 1)]}
    raise DomainError("Unknown level.")


def ayah_detail(core, r: StudentAyahState | None, idx: int, now: datetime) -> dict:
    a = core.ayah_by_index(idx)
    base = {"ayah_index": idx, "key": a.key, "surah": a.surah, "ayah": a.ayah, "page": core.page_of(idx), "text_uthmani": a.text_uthmani}
    if r is None:
        return {**base, "state": "not_memorized", "retention_score": 0.0, "explanation": []}
    return {**base, "state": r.state, "retention_score": round(r.retention_score, 3), "stability_days": round(r.stability_days, 1),
            "last_passed_at": r.last_passed_at, "next_due_at": r.next_due_at, "success_count": r.success_count,
            "fail_count": r.fail_count, "override_state": r.override_state, "explanation": explain(_to_engine(r), now)}


# ---- planning --------------------------------------------------------------------------------
@transaction.atomic
def generate_plan(journey: QuranJourney, plan_date: date, now: datetime | None = None, *, regenerate=False) -> DailyPlan:
    now = now or datetime.now(timezone.utc)
    existing = DailyPlan.objects.filter(journey=journey, plan_date=plan_date).first()
    if existing and not (regenerate and existing.status == "proposed"):
        return existing
    core = get_core(journey.riwayah)
    policy = policy_for(journey)
    snaps = [AyahSnapshot(r.ayah_index, r.state, r.retention_score, r.next_due_at)
             for r in StudentAyahState.objects.filter(journey=journey).only("ayah_index", "state", "retention_score", "next_due_at")]
    plan = generate(core, policy, snaps, plan_date=plan_date, now=now, current_ayah_index=journey.current_ayah_index,
                    memorized_pages_order=journey.memorized_pages_order or [])
    if existing:
        existing.segments.all().delete()
        row = existing
        row.rationale, row.paused_new = plan.rationale, plan.paused_new
        row.save()
    else:
        row = DailyPlan.objects.create(tenant_id=journey.tenant_id, journey=journey, plan_date=plan_date, rationale=plan.rationale,
                                       paused_new=plan.paused_new, planner_version=PLANNER_VERSION,
                                       status="approved" if policy.auto_approve_plans else "proposed")
    for i, seg in enumerate(plan.segments):
        PlanSegment.objects.create(tenant_id=journey.tenant_id, plan=row, purpose=seg.purpose, from_ayah_index=seg.from_ayah_index,
                                   to_ayah_index=seg.to_ayah_index, pages=seg.pages, reason=seg.reason,
                                   repetitions_required=seg.repetitions_required, order=i)
    return row


@transaction.atomic
def plan_action(plan: DailyPlan, action: str, actor, *, segments: list[dict] | None = None, reason: str = "") -> DailyPlan:
    before = [dict(purpose=s.purpose, from_ayah_index=s.from_ayah_index, to_ayah_index=s.to_ayah_index, pages=s.pages)
              for s in plan.segments.all()]
    if action == "approve":
        plan.status, plan.approved_by = "approved", actor
    elif action in ("edit", "override"):
        if segments is None:
            raise DomainError("segments required")
        plan.segments.all().delete()
        core = get_core(plan.journey.riwayah)
        for i, s in enumerate(segments):
            f, t = int(s["from_ayah_index"]), int(s["to_ayah_index"])
            if not (1 <= f <= t <= core.ayah_count):
                raise DomainError("Invalid segment range")
            PlanSegment.objects.create(tenant_id=plan.tenant_id, plan=plan, purpose=s.get("purpose", "near"), from_ayah_index=f,
                                       to_ayah_index=t, pages=sorted({core.page_of(f), core.page_of(t)}),
                                       reason=s.get("reason", "تعديل المعلم"), repetitions_required=int(s.get("repetitions_required", 1)), order=i)
        plan.status, plan.approved_by = ("edited" if action == "edit" else "overridden"), actor
    elif action == "carry_forward":
        plan.status = "carried"
    else:
        raise DomainError("Unknown action")
    plan.save()
    after = [dict(purpose=s.purpose, from_ayah_index=s.from_ayah_index, to_ayah_index=s.to_ayah_index, pages=s.pages)
             for s in plan.segments.all()]
    PlanAction.objects.create(tenant_id=plan.tenant_id, plan=plan, action=action, before=before, after=after, reason=reason, actor=actor)
    return plan


# ---- overrides -------------------------------------------------------------------------------
@transaction.atomic
def override_ayah_state(journey: QuranJourney, first: int, last: int, state: str | None, actor, reason: str) -> int:
    now = datetime.now(timezone.utc)
    rows = {r.ayah_index: r for r in StudentAyahState.objects.filter(journey=journey, ayah_index__gte=first, ayah_index__lte=last)}
    n = 0
    for idx in range(first, last + 1):
        row = rows.get(idx) or StudentAyahState(tenant_id=journey.tenant_id, journey=journey, ayah_index=idx)
        prev = row.state
        row.override_state = state
        if state and row.memorized_at is None:
            row.memorized_at, row.last_passed_at = now, now
            row.stability_days = {"strong": 30, "mastered": 120, "needs_revision": 7, "weak": 2, "critical": 1}.get(state, 7)
            row.retention_score = {"strong": 0.9, "mastered": 0.97, "needs_revision": 0.75, "weak": 0.5, "critical": 0.25}.get(state, 0.75)
        row.state = state or row.state
        row.save()
        AyahStateEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, ayah_index=idx, prev_state=prev, new_state=row.state,
                                      prev_score=row.retention_score, new_score=row.retention_score, cause="override",
                                      engine_version=ENGINE_VERSION, occurred_at=now)
        n += 1
    JourneyEvent.objects.create(tenant_id=journey.tenant_id, journey=journey, event_type="memory_map.override",
                                payload={"from": first, "to": last, "state": state, "reason": reason}, occurred_at=now, actor=actor)
    refresh_aggregates(journey)
    return n
