"""AI assist use-cases. Every function builds a prompt from structured facts only and returns a labeled draft.

Guardrails (enforced here, not left to the model):
- No Quran text ever enters a prompt: positions are expressed as surah name + ayah number.
- The system prompt forbids quoting/generating verses, rulings, or Tajweed judgments.
- Output is sanitized: ayah brackets ﴿…﴾ and anything that looks like a quoted verse are removed.
- Every draft carries `source: "ai"`, the model name, and an Arabic disclaimer; nothing is saved automatically.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import timedelta

from django.utils import timezone

from packages.quran_core import get_core
from services.hifz import services as hifz
from services.hifz.models import MistakeEvent, QuranJourney, RecitationSession
from services.people.models import AttendanceRecord

from .providers import AiUnavailable, get_provider

DISCLAIMER = "مسودة بمساعدة الذكاء الاصطناعي من بيانات الطالب فقط — راجعها المعلم قبل اعتمادها. لا تحتوي نصًا قرآنيًا ولا حكمًا شرعيًا."

SYSTEM_AR = (
    "أنت مساعد لمعلم تحفيظ قرآن في منصة تعليمية. تكتب بالعربية الفصحى بأسلوب دافئ ومختصر.\n"
    "قواعد صارمة لا تُخالف:\n"
    "1) لا تقتبس ولا تكتب أي آية أو جزء من آية أو بسملة، ولا تكمل نصًا قرآنيًا مهما طُلب. أشر إلى المواضع باسم السورة ورقم الآية فقط.\n"
    "2) لا تصدر أحكامًا شرعية ولا أحكامًا على صحة التجويد أو المخارج؛ هذه للمعلم المؤهل.\n"
    "3) استخدم الحقائق المعطاة فقط، ولا تخترع أرقامًا أو أحداثًا. إن كانت البيانات قليلة فقل ذلك بلطف.\n"
    "4) الثبات مقياس تعليمي لاستقرار الاسترجاع وليس حكمًا على التلاوة.\n"
    "5) لا تذكر أنك نموذج ذكاء اصطناعي داخل النص."
)

_AYAH_BRACKETS = re.compile(r"[﴿⟨«][^﴾⟩»]{0,400}[﴾⟩»]")
_BASMALAH = re.compile(r"بِسْمِ\s+ٱ?للَّهِ|بسم الله الرحمن الرحيم")
_HEAVY_TASHKEEL = re.compile(r"(?:[ء-ي][ً-ْٰ]{1,3}\s*){6,}")


def sanitize(text: str) -> str:
    """Strip anything that could be a quoted verse: bracketed ayat, basmalah, long fully-vocalized runs."""
    text = _AYAH_BRACKETS.sub("", text)
    text = _BASMALAH.sub("", text)
    text = _HEAVY_TASHKEEL.sub("[…]", text)
    return re.sub(r"[ \t]+", " ", text).strip()


PURPOSE_AR = {"new": "حفظ جديد", "near": "مراجعة قريبة", "far": "مراجعة بعيدة", "assessment": "اختبار", "review_queue": "مراجعة معلم"}
OUTCOME_AR = {"pass": "اجتاز", "partial": "جزئي", "repeat": "يعيد"}
MISTAKE_AR = {"tashkeel": "تشكيل", "word_swap": "إبدال كلمة", "omission": "إسقاط", "addition": "زيادة", "hesitation": "تردد",
              "mutashabih": "التباس بمتشابه", "tajweed": "تجويد", "stop_start": "وقف وابتداء", "unknown": "أخرى"}


def _facts(journey: QuranJourney, days: int = 7) -> dict:
    core = get_core()
    since = timezone.now() - timedelta(days=days)
    sessions = list(RecitationSession.objects.filter(journey=journey, started_at__gte=since).order_by("-started_at")[:30])
    mistakes = Counter(m.mistake_type for m in MistakeEvent.objects.filter(session__in=sessions))
    att = list(AttendanceRecord.objects.filter(student=journey.student, on_date__gte=since.date()).values_list("status", flat=True))
    plan = hifz.generate_plan(journey, timezone.now().date())

    def pos(idx: int) -> str:
        a = core.ayah_by_index(idx)
        return f"{core.surah(a.surah).name_ar} {a.ayah}"

    return {
        "student": journey.student.person.display_name_ar,
        "days": days,
        "memorized_pages": len(journey.memorized_pages_order or []),
        "memorized_ayat": journey.memorized_ayat,
        "avg_retention_pct": round((journey.avg_retention or 0) * 100),
        "weak_ayat": journey.weak_ayat, "critical_ayat": journey.critical_ayat,
        "attendance": {"present": sum(1 for a in att if a in ("present", "late")), "total": len(att), "late": sum(1 for a in att if a == "late")},
        "sessions": [{"date": s.started_at.date().isoformat(), "purpose": PURPOSE_AR.get(s.purpose, s.purpose), "outcome": OUTCOME_AR.get(s.outcome, s.outcome),
                      "range": f"{pos(s.from_ayah_index)} → {pos(s.to_ayah_index)}", "grade": s.grade} for s in sessions[:10]],
        "mistake_types": {MISTAKE_AR.get(k, k): v for k, v in mistakes.most_common(5)},
        "current_position": pos(journey.current_ayah_index) if journey.current_ayah_index else None,
        "plan_today": [{"purpose": PURPOSE_AR.get(sg.purpose, sg.purpose), "range": f"{pos(sg.from_ayah_index)} → {pos(sg.to_ayah_index)}"} for sg in plan.segments.all()[:6]] if plan else [],
        "paused_new": bool(plan and plan.paused_new),
    }


def _facts_block(f: dict) -> str:
    lines = [f"الطالب: {f['student']}", f"المدة: آخر {f['days']} أيام",
             f"المحفوظ: {f['memorized_pages']} صفحة ({f['memorized_ayat']} آية)، متوسط الثبات {f['avg_retention_pct']}٪، آيات ضعيفة {f['weak_ayat']}، حرجة {f['critical_ayat']}",
             f"الحضور: {f['attendance']['present']} من {f['attendance']['total']} (تأخر {f['attendance']['late']})"]
    if f["current_position"]:
        lines.append(f"موضع الحفظ الجديد: {f['current_position']}")
    if f["sessions"]:
        lines.append("جلسات التسميع:")
        lines += [f"  - {s['date']}: {s['purpose']} {s['range']} — {s['outcome']}" + (f" (درجة {s['grade']})" if s["grade"] is not None else "") for s in f["sessions"]]
    else:
        lines.append("جلسات التسميع: لا توجد جلسات في هذه المدة")
    if f["mistake_types"]:
        lines.append("أكثر أنواع الأخطاء: " + "، ".join(f"{k} ({v})" for k, v in f["mistake_types"].items()))
    if f["plan_today"]:
        lines.append("خطة اليوم: " + "؛ ".join(f"{p['purpose']} {p['range']}" for p in f["plan_today"]))
    if f["paused_new"]:
        lines.append("ملاحظة النظام: الحفظ الجديد متوقف مؤقتًا بسبب تراكم المراجعة")
    return "\n".join(lines)


def _run(system: str, user: str, *, max_tokens: int) -> dict:
    provider = get_provider()
    text = sanitize(provider.complete(system, user, max_tokens=max_tokens))
    if not text:
        raise AiUnavailable("empty completion")
    return {"text": text, "source": "ai", "provider": provider.name, "model": provider.model, "disclaimer": DISCLAIMER, "safety": "YELLOW"}


def weekly_note_draft(journey: QuranJourney) -> dict:
    """A 3–4 sentence note from the teacher to the parent, drafted from the week's real data. The teacher edits and saves it."""
    f = _facts(journey)
    user = ("اكتب ملاحظة أسبوعية قصيرة (٣ إلى ٤ جمل) من المعلم إلى ولي أمر الطالب بناءً على الحقائق التالية فقط. "
            "ابدأ بما تحقق، ثم ما يحتاج متابعة، ثم نصيحة عملية واحدة للبيت. لا عناوين ولا نقاط، نص متصل.\n\n" + _facts_block(f))
    out = _run(SYSTEM_AR, user, max_tokens=320)
    out["facts"] = f
    return out


def explain_journey(journey: QuranJourney) -> dict:
    """For the teacher/supervisor: why the student is where they are and what to do this week."""
    f = _facts(journey, days=14)
    user = ("اشرح للمعلم أو المشرف حالة هذا الطالب في فقرتين قصيرتين: (١) ما الذي تقوله الأرقام والجلسات؟ (٢) ما التدخل المقترح لهذا الأسبوع "
            "(ترتيب المراجعة، حجم الحفظ الجديد، ما يستحق تنبيه ولي الأمر)؟ اعتمد الحقائق التالية فقط.\n\n" + _facts_block(f))
    out = _run(SYSTEM_AR, user, max_tokens=420)
    out["facts"] = f
    return out
