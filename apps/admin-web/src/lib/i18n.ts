"use client";
import { createContext, useContext } from "react";

export type Locale = "ar" | "en";

const dict = {
  ar: {
    app: "تَلَقِّي", tagline: "نظام تشغيل مفتوح المصدر لتعليم القرآن",
    nav_dashboard: "لوحة المشرف", nav_students: "الطلاب", nav_halaqat: "الحلقات", nav_staff: "المعلمون", nav_modules: "الوحدات والصلاحيات", nav_quran: "المصحف",
    signout: "تسجيل الخروج", switch_lang: "English",
    login_title: "تسجيل الدخول", email: "البريد الإلكتروني", password: "كلمة المرور", login_btn: "ادخل", login_hint: "بيانات العرض التجريبي: owner@demo.talaqqi / Talaqqi@2026",
    dash_title: "صحة التعلّم في المركز", dash_sub: "من يسير على خطته، ومن يتأخر، ومن يحتاج تدخلًا — بالأسباب.",
    on_track: "على المسار", behind: "متأخر", attention: "يحتاج تدخلًا", students: "طالب", avg_retention: "متوسط الثبات",
    reasons: "الأسباب", halaqah_perf: "أداء الحلقات", teacher: "المعلم", memorized_pages: "صفحات محفوظة", critical_ayat: "آيات حرجة",
    students_title: "الطلاب", search: "بحث بالاسم أو الرقم", code: "الرقم", branch: "الفرع", halaqah: "الحلقة", memorized: "المحفوظ", retention: "الثبات", status: "الحالة",
    journey: "رحلة الطالب مع القرآن", memory_map: "خريطة الحفظ", timeline: "المسار الزمني", sessions: "جلسات التسميع", todays_plan: "خطة اليوم",
    quran_level: "المصحف", juz: "الجزء", page: "صفحة", ayah: "آية", position: "موضع الحفظ الجديد",
    state_not_memorized: "غير محفوظ", state_learning: "قيد الحفظ", state_recent: "حديث الحفظ", state_strong: "متين", state_needs_revision: "يحتاج مراجعة", state_weak: "ضعيف", state_critical: "حرج", state_mastered: "متقن",
    purpose_new: "حفظ جديد", purpose_near: "مراجعة قريبة", purpose_far: "مراجعة بعيدة", purpose_assessment: "اختبار",
    outcome_pass: "اجتاز", outcome_repeat: "يعيد", outcome_partial: "جزئي",
    today_title: "حلقة اليوم", attendance: "الحضور", present: "حاضر", absent: "غائب", late: "متأخر", excused: "بعذر", start_tasmee: "ابدأ التسميع",
    tasmee: "التسميع", tap_word_hint: "انقر على الكلمة لتسجيل خطأ، ثم اختر نوعه.", pass: "اجتاز", repeat: "يعيد", partial: "جزئي", note: "ملاحظة للمعلم", save_eval: "احفظ التقييم", saved: "حُفظ التقييم", mistakes: "الأخطاء",
    next_due: "المراجعة القادمة", explanation: "لماذا هذا التقييم؟", last_passed: "آخر تسميع ناجح", stability: "الثبات التقديري",
    modules_title: "الوحدات المفعّلة", modules_sub: "التفعيل يُطبَّق في الخادم: تعطيل وحدة يُعيد 403 لواجهاتها.", safety_GREEN: "حتمي", safety_YELLOW: "مساعد", safety_RED: "بشري فقط", core: "أساسي", enabled: "مفعّلة", disabled: "معطّلة",
    quran_attribution: "نص القرآن: مشروع تنزيل — tanzil.net", loading: "جارٍ التحميل…", empty: "لا توجد بيانات بعد.", error: "تعذّر التحميل",
    ayat: "آية", of: "من", coverage: "التغطية", due: "مستحقة",
  },
  en: {
    app: "Talaqqi", tagline: "Open-source operating system for Quran education",
    nav_dashboard: "Supervisor", nav_students: "Students", nav_halaqat: "Halaqat", nav_staff: "Teachers", nav_modules: "Modules & permissions", nav_quran: "Mushaf",
    signout: "Sign out", switch_lang: "العربية",
    login_title: "Sign in", email: "Email", password: "Password", login_btn: "Sign in", login_hint: "Demo: owner@demo.talaqqi / Talaqqi@2026",
    dash_title: "Learning health of the center", dash_sub: "Who is on track, who is behind, who needs intervention — with reasons.",
    on_track: "On track", behind: "Behind", attention: "Needs attention", students: "students", avg_retention: "Avg. retention",
    reasons: "Reasons", halaqah_perf: "Halaqah performance", teacher: "Teacher", memorized_pages: "Memorized pages", critical_ayat: "Critical ayat",
    students_title: "Students", search: "Search by name or code", code: "Code", branch: "Branch", halaqah: "Halaqah", memorized: "Memorized", retention: "Retention", status: "Status",
    journey: "Quran journey", memory_map: "Memory map", timeline: "Timeline", sessions: "Tasmee' sessions", todays_plan: "Today's plan",
    quran_level: "Quran", juz: "Juz", page: "Page", ayah: "Ayah", position: "Next new memorization",
    state_not_memorized: "Not memorized", state_learning: "Learning", state_recent: "Recent", state_strong: "Strong", state_needs_revision: "Needs revision", state_weak: "Weak", state_critical: "Critical", state_mastered: "Mastered",
    purpose_new: "New", purpose_near: "Near revision", purpose_far: "Far revision", purpose_assessment: "Assessment",
    outcome_pass: "Pass", outcome_repeat: "Repeat", outcome_partial: "Partial",
    today_title: "Today's Halaqah", attendance: "Attendance", present: "Present", absent: "Absent", late: "Late", excused: "Excused", start_tasmee: "Start Tasmee'",
    tasmee: "Tasmee'", tap_word_hint: "Tap a word to record a mistake, then pick its type.", pass: "Pass", repeat: "Repeat", partial: "Partial", note: "Teacher note", save_eval: "Save evaluation", saved: "Evaluation saved", mistakes: "Mistakes",
    next_due: "Next revision", explanation: "Why this score?", last_passed: "Last successful recall", stability: "Estimated stability",
    modules_title: "Enabled modules", modules_sub: "Enforced by the backend: disabling a module makes its endpoints return 403.", safety_GREEN: "Deterministic", safety_YELLOW: "Assistive", safety_RED: "Human only", core: "Core", enabled: "Enabled", disabled: "Disabled",
    quran_attribution: "Quran text: Tanzil Project — tanzil.net", loading: "Loading…", empty: "Nothing here yet.", error: "Could not load",
    ayat: "ayat", of: "of", coverage: "Coverage", due: "due",
  },
} as const;

export type Key = keyof typeof dict.ar;
export const I18nContext = createContext<{ locale: Locale; t: (k: Key) => string; setLocale: (l: Locale) => void }>({
  locale: "ar", t: (k) => dict.ar[k], setLocale: () => {},
});
export const useI18n = () => useContext(I18nContext);
export const translate = (locale: Locale, k: Key) => (dict[locale] as Record<Key, string>)[k] ?? dict.ar[k];
