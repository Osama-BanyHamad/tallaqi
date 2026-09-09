"use client";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, login } from "@/lib/api";
import { homeFor, type Capabilities } from "@/components/Shell";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { SampleMap } from "@/components/SampleMap";

const DEMO_PASSWORD = "Talaqqi@2026";
const DEMO: { key: string; email: string; ar: string; en: string; hint_ar: string; hint_en: string; color: string }[] = [
  { key: "teacher", email: "teacher1@demo.talaqqi", ar: "معلم", en: "Teacher", hint_ar: "حلقة اليوم والتسميع من المصحف", hint_en: "Today's Halaqah and Tasmee'", color: "var(--lapis)" },
  { key: "student", email: "student1@demo.talaqqi", ar: "طالب", en: "Student", hint_ar: "خطة اليوم والتدريب الذاتي", hint_en: "Today's plan and self-practice", color: "var(--s-strong)" },
  { key: "parent", email: "parent1@demo.talaqqi", ar: "ولي أمر", en: "Parent", hint_ar: "الإجابات الست الأسبوعية", hint_en: "The six weekly answers", color: "var(--gold)" },
  { key: "owner", email: "owner@demo.talaqqi", ar: "مدير المركز", en: "Center owner", hint_ar: "لوحة المشرف والإدارة والمالية", hint_en: "Dashboard, administration, finance", color: "var(--s-recent)" },
];

export default function LoginPage() {
  return <Suspense><LoginInner /></Suspense>;
}

function LoginInner() {
  const { t, locale, setLocale } = useI18n();
  const tr = useT2();
  const r = useRouter();
  const sp = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function go(e: string, p: string, key = "form") {
    setBusy(key); setErr(null);
    try { await login(e, p); const caps = await api<Capabilities>("/me/capabilities"); r.replace(homeFor(caps)); }
    catch (ex) { setErr((ex as Error).message); setBusy(null); }
  }
  // /login?demo=teacher opens the demo directly from the site's role picker
  useEffect(() => {
    const d = DEMO.find((x) => x.key === sp.get("demo"));
    if (d) go(d.email, DEMO_PASSWORD, d.key);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sp]);

  return (
    <main className="login">
      <section className="login-brand">
        <div className="lattice" />
        <div style={{ position: "relative" }}>
          <Link href="/" className="wordmark"><span className="ar login-mark">تَلَقِّي</span><span className="latin">Talaqqi</span></Link>
          <p className="fade-up login-lede">
            {locale === "ar" ? "رحلة الطالب مع القرآن: ما حُفظ، وما ثبت، وما يُراجَع اليوم — بيد المعلم، وبعين المشرف، وبطمأنينة ولي الأمر." : "The student's Quran journey: what was memorized, what stays strong, and what to revise today — in the teacher's hands, under the supervisor's eye, with the parent's peace of mind."}
          </p>
        </div>
        <div className="fade-up login-map"><SampleMap dark /></div>
        <p className="login-attrib">{t("quran_attribution")} · AGPL-3.0</p>
      </section>
      <section className="login-form">
        <div className="stack fade-up" style={{ width: "min(440px, 100%)", gap: 22 }}>
          <div><span className="eyebrow">{t("app")}</span><h1 style={{ marginTop: 8 }}>{t("login_title")}</h1></div>
          <form onSubmit={(e) => { e.preventDefault(); go(email, password); }} className="stack" style={{ gap: 14 }}>
            <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{t("email")}</span><input className="input" dir="ltr" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="name@example.com" /></label>
            <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{t("password")}</span><input className="input" dir="ltr" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
            {err && <p role="alert" style={{ margin: 0, color: "var(--s-weak)", fontSize: 13.5 }}>{err}</p>}
            <button className="btn primary" disabled={!!busy} style={{ height: 46, fontSize: 15 }}>{busy === "form" ? "…" : t("login_btn")}</button>
          </form>
          <div className="row" style={{ gap: 10 }}><span style={{ flex: 1, height: 1, background: "var(--rule)" }} /><span className="muted" style={{ fontSize: 12.5 }}>{tr("أو جرّب العرض التجريبي بلمسة", "or try the demo with one click")}</span><span style={{ flex: 1, height: 1, background: "var(--rule)" }} /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {DEMO.map((d) => (
              <button key={d.key} type="button" className="btn" disabled={!!busy} onClick={() => go(d.email, DEMO_PASSWORD, d.key)}
                style={{ height: "auto", padding: "10px 12px", justifyContent: "flex-start", textAlign: "start", gap: 10, borderColor: `color-mix(in srgb, ${d.color} 40%, var(--rule))` }}>
                <span style={{ width: 10, height: 10, borderRadius: 999, background: d.color, flex: "none" }} />
                <span><b style={{ display: "block", fontSize: 14 }}>{busy === d.key ? "…" : locale === "en" ? d.en : d.ar}</b><span className="muted" style={{ fontSize: 11.5 }}>{locale === "en" ? d.hint_en : d.hint_ar}</span></span>
              </button>
            ))}
          </div>
          <div className="surface pad" style={{ background: "var(--gold-tint)", borderColor: "color-mix(in srgb, var(--gold) 40%, var(--rule))", padding: "14px 16px" }}>
            <b style={{ fontFamily: "var(--font-display)", fontSize: 14.5 }}>{tr("تحفظ وحدك؟", "Memorizing on your own?")}</b>
            <p style={{ margin: "4px 0 10px", fontSize: 13, color: "var(--ink-2)" }}>{tr("أنشئ رحلتك الخاصة مجانًا: خطة يومية، خريطة حفظ، تدريب ذاتي، وتسميع ذكي — وادعُ من يسمّع لك.", "Create your own free journey: a daily plan, a memory map, self-practice, an AI check, and invite someone to listen to you.")}</p>
            <Link href="/start" className="btn gold sm">{tr("ابدأ رحلتك مجانًا", "Start your free journey")} ←</Link>
          </div>
          <div className="row"><button type="button" className="btn sm" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>{t("switch_lang")}</button><Link href="/" className="btn sm">{locale === "ar" ? "الموقع العام" : "Public site"}</Link></div>
        </div>
      </section>
    </main>
  );
}
