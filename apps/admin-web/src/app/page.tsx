"use client";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { SampleMap } from "@/components/SampleMap";
import { IconGlobe } from "@/components/icons";

/* Public site — the project's front door. Arabic-first; English mirrors. */
const AR = {
  nav: ["الفكرة", "الوحدات", "سلامة القرآن", "لمن", "مفتوح المصدر"],
  h1: "نظام تشغيل مفتوح المصدر لتعليم القرآن",
  lede: "ليس برنامج إدارة مركز. تَلَقِّي يتابع رحلة الطالب مع القرآن آيةً آية: ما حُفظ، وما ثبت، وما يُراجَع اليوم — ويربط الطالب والمعلم وولي الأمر والمشرف والمركز حول هذه الرحلة.",
  cta1: "جرّب العرض التجريبي", cta2: "الكود على GitHub",
  loop: ["يحفظ الطالب", "يتدرّب", "يسمّع للمعلم", "يسجّل النظام", "يتغيّر الثبات", "تُجدوَل المراجعة", "يراجع المعلم", "يرى ولي الأمر تقدمًا حقيقيًا", "يرى المشرف صحة المؤسسة"],
  pillarsTitle: "أربعة أشياء لا يفعلها غيرنا معًا",
  pillars: [
    ["خريطة الحفظ", "لكل آية حالة قابلة للقياس بتاريخها الكامل: متين، يحتاج مراجعة، ضعيف، حرج، متقن. تُعرض على مستوى المصحف والجزء والصفحة والآية."],
    ["محرك الثبات", "منحنى نسيان حتمي قابل للتفسير يحسب استقرار الاسترجاع من تسميعات المعلم وأخطائه وزمن المراجعة. بلا ذكاء اصطناعي، وبشرح عربي لكل رقم."],
    ["تسميع بأربع نقرات", "المعلم يبقى على المصحف: ينقر الكلمة، يختار نوع الخطأ، يضغط اجتاز. ثم تُحدَّث الخريطة وتُقترح خطة الغد تلقائيًا."],
    ["فصل مباشر بلا تسجيل", "قاعة قرآنية مبنية للغرض: مصحف مشترك يتبع المعلم، وقاعة انتظار، وصوت أولًا، وتسجيلٌ غائب بالتصميم عند تعطيله — لا واجهة زووم."],
  ],
  safetyTitle: "القرآن أولًا — حدود لا تُتجاوز",
  safety: [
    ["نصٌّ واحد مصدره واحد", "نواة قرآن مغلقة وموقّعة ومُتحقّق منها؛ لا يمكن لأي خدمة أو مدير أو نموذج ذكاء أن يكتب فيها. أي تغيير في حرف واحد يُسقط الاختبارات."],
    ["لا صوت مولّد", "التلاوات المرجعية من قرّاء حقيقيين بحقوق موثّقة. لا يُستخدم التوليد الصوتي للقرآن أبدًا."],
    ["السلطة للإنسان", "صحة التجويد والمخارج، والإجازة، والفتوى، وتصحيح الحديث، وتفسير القرآن — قرارات بشرية مؤهلة لا يؤدّيها البرنامج."],
    ["الثبات مقياس تعليمي", "الرقم يصف استقرار الاسترجاع لا الحكم الشرعي على التلاوة، ويُكتب ذلك في كل شاشة."],
    ["عند الشك: افعل أقل", "أي كشف آلي غير متأكد يذهب إلى المعلم. لا تخمين، ولا إكمال آيات توليديًا."],
    ["الذكاء الاصطناعي اختياري", "المنصة كاملة تعمل بلا أي مزوّد ذكاء. عند تفعيله يبقى مساعدًا موسومًا ومربوطًا بمصادره."],
  ],
  audienceTitle: "لمن؟",
  audience: ["مراكز التحفيظ الصغيرة", "المساجد", "مدارس القرآن", "المؤسسات الكبيرة متعددة الفروع", "الجمعيات الخيرية", "الأكاديميات الإسلامية", "أكاديميات القرآن عن بُعد", "المعلمون المستقلون", "الدور النسائية", "برامج الأطفال", "المنظمات الدولية بعدة لغات وعملات"],
  modulesTitle: "وحدات تُفعَّل وتُعطَّل مستقلة — والخادم هو من يفرض ذلك",
  modules: ["الطلاب وأولياء الأمور", "المعلمون والموظفون", "الحلقات والحضور", "رحلة الطالب وخريطة الحفظ", "محرك الثبات", "منهجية الحفظ", "خطة الحفظ والمراجعة", "التسميع", "الاختبارات", "المتشابهات", "التدريب الذاتي", "قائمة مراجعة المعلم", "بوابة ولي الأمر", "لوحة المشرف", "الإنذار المبكر", "التقارير", "الفصل المباشر", "الرسوم والفواتير", "التبرعات", "التفسير والحديث", "المكتبة الإسلامية", "المقررات", "التنبيهات", "سجل التدقيق"],
  ossTitle: "مفتوح المصدر، يُستضاف ذاتيًا على خادم واحد",
  ossLede: "AGPL-3.0. PostgreSQL مع عزل صفوف لكل مؤسسة. Django وNext.js وFlutter. يعمل على خادم افتراضي صغير، ويتوسّع عند الحاجة. نسخة سحابية مُدارة لاحقًا لمن لا يريد التشغيل بنفسه.",
  footer: "tallaqi.com · نص القرآن: مشروع تنزيل — tanzil.net · تَلَقِّي مشروع مفتوح المصدر برخصة AGPL-3.0",
};
const EN: typeof AR = {
  nav: ["Idea", "Modules", "Quran safety", "For whom", "Open source"],
  h1: "An open-source operating system for Quran education",
  lede: "Not a center management program. Talaqqi follows the student's Quran journey Ayah by Ayah: what was memorized, what stays strong, what to revise today — and connects student, teacher, parent, supervisor, and center around it.",
  cta1: "Try the demo", cta2: "Code on GitHub",
  loop: ["Student learns", "practices", "recites to the teacher", "system records", "retention changes", "revision is scheduled", "teacher reviews", "parent sees real progress", "supervisor sees institutional health"],
  pillarsTitle: "Four things nobody else does together",
  pillars: [
    ["Memory Map", "Every Ayah has a measurable state with full history: strong, needs revision, weak, critical, mastered. Shown at Quran, Juz, page, and Ayah level."],
    ["Retention Engine", "A deterministic, explainable forgetting curve computes recall stability from teacher-verified recitations, mistakes, and time. No AI, and an Arabic explanation for every number."],
    ["Tasmee' in four taps", "The teacher stays on the Mushaf: tap the word, pick the mistake type, press Pass. The map updates and tomorrow's plan is proposed."],
    ["Live class, no recording", "A purpose-built Quran classroom: shared Mushaf that follows the teacher, waiting room, audio-first, and recording absent by design when disabled — not a Zoom link."],
  ],
  safetyTitle: "Quran first — boundaries that are never crossed",
  safety: [
    ["One text, one source", "A sealed, signed, verified Quran Core; no service, admin, or AI model can write to it. A single changed letter fails the tests."],
    ["No generated audio", "Reference recitations come from real reciters with documented rights. Generative audio is never used for Quran."],
    ["Authority stays human", "Tajweed and Makharij correctness, Ijazah, rulings, Hadith grading, and Tafsir are decisions for qualified people, never the software."],
    ["Retention is an educational metric", "The number describes recall stability, not a religious judgment on the recitation, and every screen says so."],
    ["When unsure, do less", "Any uncertain automatic detection goes to the teacher. No guessing, no generative completion of Ayat."],
    ["AI is optional", "The whole platform runs with no AI provider. When enabled, it stays a labeled assistant tied to its sources."],
  ],
  audienceTitle: "For whom?",
  audience: ["Small memorization centers", "Mosques", "Quran schools", "Large multi-branch institutions", "Charities", "Islamic academies", "Online Quran academies", "Independent teachers", "Women's centers", "Children's programs", "International organizations in many languages and currencies"],
  modulesTitle: "Modules switch on and off independently — enforced by the backend",
  modules: ["Students & guardians", "Teachers & staff", "Halaqat & attendance", "Journey & Memory Map", "Retention engine", "Learning policy", "Hifz & revision planner", "Tasmee'", "Assessments", "Mutashabihat", "Self-practice", "Teacher review queue", "Parent portal", "Supervisor dashboard", "Early warning", "Reports", "Live classroom", "Fees & invoices", "Donations", "Tafsir & Hadith", "Islamic library", "Courses", "Notifications", "Audit log"],
  ossTitle: "Open source, self-hosted on a single server",
  ossLede: "AGPL-3.0. PostgreSQL with per-tenant row isolation. Django, Next.js, Flutter. Runs on a small VPS and scales when needed. A managed cloud later for those who do not want to operate it.",
  footer: "tallaqi.com · Quran text: Tanzil Project — tanzil.net · Talaqqi is open source under AGPL-3.0",
};

export default function Site() {
  const { locale, setLocale } = useI18n();
  const s = locale === "ar" ? AR : EN;
  const ids = ["idea", "modules", "safety", "who", "oss"];
  return (
    <div className="site">
      <nav className="site-nav">
        <Link href="/" className="wordmark" style={{ flexDirection: "row", alignItems: "baseline", gap: 10 }}><span className="ar" style={{ fontSize: 30 }}>تَلَقِّي</span><span className="latin">Talaqqi</span></Link>
        <div className="links">{s.nav.map((n, i) => <a key={i} href={`#${ids[i]}`}>{n}</a>)}</div>
        <div className="actions">
          <button className="lang" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}><IconGlobe />{locale === "ar" ? "English" : "العربية"}</button>
          <Link href="/login" className="pill-cta">{s.cta1}</Link>
        </div>
      </nav>

      <header className="hero">
        <div className="lattice" />
        <div className="watermark" aria-hidden>تلقي</div>
        <div className="hero-grid">
          <div className="fade-up">
            <span className="kicker">{locale === "ar" ? "مفتوح المصدر · عربي أولًا · يُستضاف ذاتيًا" : "Open source · Arabic-first · self-hosted"}</span>
            <h1 className="display">{s.h1}</h1>
            <p className="lede">{s.lede}</p>
            <div className="row" style={{ gap: 14 }}>
              <Link href="/login" className="pill-cta lg">{s.cta1}</Link>
              <a href="https://github.com/Osama-BanyHamad/tallaqi" className="pill-cta lg ghost">{s.cta2}</a>
            </div>
          </div>
          <div className="device fade-up" style={{ animationDelay: ".15s" }}>
            <div className="title"><b style={{ fontFamily: "var(--font-display)" }}>{locale === "ar" ? "خريطة الحفظ — يوسف، ١١ سنة" : "Memory Map — Yusuf, 11"}</b><span className="num muted" style={{ fontSize: 12 }}>{locale === "ar" ? "الجزء ٢٤ → ٣٠" : "Juz 24 → 30"}</span></div>
            <SampleMap />
            <div className="legend" style={{ marginTop: 14 }}>
              <span><i style={{ background: "var(--s-mastered)" }} />{locale === "ar" ? "متقن" : "Mastered"}</span><span><i style={{ background: "var(--s-strong)" }} />{locale === "ar" ? "متين" : "Strong"}</span><span><i style={{ background: "var(--s-needs)" }} />{locale === "ar" ? "يحتاج مراجعة" : "Needs revision"}</span><span><i style={{ background: "var(--s-weak)" }} />{locale === "ar" ? "ضعيف" : "Weak"}</span><span><i style={{ background: "var(--s-critical)" }} />{locale === "ar" ? "حرج" : "Critical"}</span>
            </div>
          </div>
        </div>
      </header>

      <section className="section" id="idea">
        <div className="section-head"><span className="eyebrow">{locale === "ar" ? "الحلقة الأهم" : "The loop that matters"}</span><h2>{locale === "ar" ? "كل شيء في المنصة يخدم هذه الحلقة" : "Everything in the platform serves this loop"}</h2></div>
        <div className="loop">{s.loop.map((x, i) => <span key={i}>{x}{i < s.loop.length - 1 && <i style={{ marginInlineStart: 8 }}>←</i>}</span>)}</div>
        <div className="section-head" style={{ marginTop: 64 }}><h2>{s.pillarsTitle}</h2></div>
        <div className="pillars stagger">
          {s.pillars.map(([h3, p], i) => (
            <div key={i} className="pillar">
              <div className="art">{i === 0 ? <div style={{ width: "88%" }}><SampleMap rows={[28, 29, 30]} compact /></div> : i === 1 ? <Curve /> : i === 2 ? <Words /> : <Wave />}</div>
              <h3>{h3}</h3><p>{p}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section alt" id="safety">
        <div className="section-head"><span className="eyebrow">{locale === "ar" ? "سلامة القرآن" : "Quran safety"}</span><h2>{s.safetyTitle}</h2></div>
        <div className="principles stagger">{s.safety.map(([b, p], i) => (
          <div key={i} className="principle">
            <span className="idx">{String(i + 1).padStart(2, "0")}</span>
            <svg className="star" viewBox="0 0 34 34" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M17 2l4.2 8.6L30 12l-6.5 6.4L25 28l-8-4.3L9 28l1.5-9.6L4 12l8.8-1.4z" /><circle cx="17" cy="16.5" r="3" /></svg>
            <b>{b}</b><p>{p}</p>
          </div>))}</div>
      </section>

      <section className="section" id="modules">
        <div className="section-head"><span className="eyebrow">{locale === "ar" ? "الوحدات" : "Modules"}</span><h2>{s.modulesTitle}</h2></div>
        <div className="audience">{s.modules.map((m, i) => <span key={i}>{m}</span>)}</div>
      </section>

      <section className="section alt" id="who">
        <div className="section-head"><span className="eyebrow">{s.audienceTitle}</span><h2>{locale === "ar" ? "من مسجدٍ بحلقة واحدة إلى مؤسسة في عدة دول" : "From a mosque with one Halaqah to an institution in several countries"}</h2></div>
        <div className="audience">{s.audience.map((m, i) => <span key={i}>{m}</span>)}</div>
      </section>

      <section className="section" id="oss">
        <div className="section-head"><span className="eyebrow">AGPL-3.0</span><h2>{s.ossTitle}</h2><p>{s.ossLede}</p></div>
        <pre className="code"><span className="c"># one VPS, PostgreSQL 16, Python 3.12, Node 22</span>{"\n"}git clone https://github.com/Osama-BanyHamad/tallaqi && cd talaqqi{"\n"}python apps/api/manage.py migrate{"\n"}python apps/api/manage.py load_quran_core   <span className="c"># verifies every checksum first</span>{"\n"}python apps/api/manage.py seed_demo{"\n"}python apps/api/manage.py runserver</pre>
      </section>

      <footer className="site-footer"><span>{s.footer}</span><span className="num">v0.1</span></footer>
    </div>
  );
}

function Curve() {
  return (<svg viewBox="0 0 200 70" width="88%" height="70" fill="none"><path d="M6 8 C 40 8, 60 60, 194 62" stroke="var(--s-weak)" strokeWidth="2" /><path d="M6 8 C 60 8, 90 40, 194 44" stroke="var(--s-needs)" strokeWidth="2" /><path d="M6 8 C 80 8, 120 22, 194 26" stroke="var(--s-strong)" strokeWidth="2.5" /><circle cx="6" cy="8" r="3" fill="var(--gold)" /></svg>);
}
function Words() {
  const w = ["إِنَّ", "ٱلْإِنسَٰنَ", "لَفِى", "خُسْرٍ"];
  return (<div className="quran" style={{ fontSize: 22, lineHeight: 1.6 }}>{w.map((x, i) => <span key={i} style={{ padding: "0 3px", borderRadius: 4, background: i === 2 ? "color-mix(in srgb, var(--s-weak) 28%, transparent)" : undefined, boxShadow: i === 2 ? "inset 0 -3px 0 var(--s-weak)" : undefined }}>{x} </span>)}</div>);
}
function Wave() {
  return (<svg viewBox="0 0 200 60" width="88%" height="60" fill="none" stroke="var(--lapis)" strokeWidth="2" strokeLinecap="round">{Array.from({ length: 34 }, (_, i) => { const a = Math.round((6 + 22 * Math.abs(Math.sin(i * .6)) * (i > 26 ? .25 : 1)) * 10) / 10; const x = Math.round((6 + i * 5.7) * 10) / 10; return <path key={i} d={`M${x} ${Math.round((30 - a) * 10) / 10} V${Math.round((30 + a) * 10) / 10}`} />; })}</svg>);
}
