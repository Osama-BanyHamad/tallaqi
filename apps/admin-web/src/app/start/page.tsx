"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, setSession, type Session } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { fmtNum } from "@/lib/quran";

type Goal = "juz30" | "juz_29_30" | "whole" | "keep";

/** Independent learner sign-up: three questions, then the learner lands on today's plan. */
export default function StartPage() {
  const { locale, setLocale } = useI18n();
  const tr = useT2();
  const r = useRouter();
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState<Goal>("juz30");
  const [juz, setJuz] = useState<Set<number>>(new Set());
  const [minutes, setMinutes] = useState(20);
  const [f, setF] = useState({ full_name: "", email: "", password: "", gender: "male" });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const GOALS: { key: Goal; ar: string; en: string; sub_ar: string; sub_en: string }[] = [
    { key: "juz30", ar: "أحفظ جزء عمّ", en: "Memorize Juz 30", sub_ar: "أشهر نقطة بداية؛ سور قصيرة وتقدّم يومي واضح", sub_en: "The most common start: short surahs, visible daily progress" },
    { key: "juz_29_30", ar: "أحفظ الجزأين ٢٩ و٣٠", en: "Memorize Juz 29 and 30", sub_ar: "خطة لبضعة أشهر بمراجعة منتظمة", sub_en: "A few months with steady revision" },
    { key: "whole", ar: "أحفظ القرآن كاملًا", en: "Memorize the whole Quran", sub_ar: "رحلة طويلة؛ نبدأ من جزء عمّ إلى البقرة", sub_en: "A long journey, from Juz 30 back to Al-Baqarah" },
    { key: "keep", ar: "أثبّت ما حفظته", en: "Keep what I memorized strong", sub_ar: "بلا حفظ جديد؛ مراجعة مجدولة حسب الثبات", sub_en: "No new memorization; revision scheduled by retention" },
  ];

  async function submit() {
    setBusy(true); setErr(null);
    try {
      const res = await fetch("/api/v1/auth/signup", { method: "POST", headers: { "Content-Type": "application/json", "Accept-Language": locale }, body: JSON.stringify({ ...f, locale, goal, memorized_juz: [...juz], daily_minutes: minutes }) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new ApiError(res.status, body.code ?? "error", typeof body.detail === "string" ? body.detail : Object.values(body.detail ?? {}).flat().join(" · ") || res.statusText, body);
      const s: Session = { access: body.access, refresh: body.refresh, account: body.account, memberships: body.memberships, tenant: body.tenant };
      setSession(s);
      r.replace("/me?welcome=1");
    } catch (e) { setErr((e as Error).message); setBusy(false); }
  }

  const steps = [tr("هدفك", "Your goal"), tr("ما تحفظه الآن", "What you know"), tr("وقتك اليومي", "Daily time"), tr("حسابك", "Your account")];
  return (
    <main className="login" style={{ gridTemplateColumns: "1fr" }}>
      <section className="login-form" style={{ alignItems: "start", paddingTop: 40 }}>
        <div className="stack fade-up" style={{ width: "min(640px, 100%)", gap: 22 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <Link href="/" className="wordmark" style={{ flexDirection: "row", alignItems: "baseline", gap: 10 }}><span className="ar" style={{ fontSize: 30, color: "var(--ink)" }}>تَلَقِّي</span><span className="latin" style={{ color: "var(--gold)" }}>Talaqqi</span></Link>
            <button type="button" className="btn sm" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>{locale === "ar" ? "English" : "العربية"}</button>
          </div>
          <div><span className="eyebrow">{tr("رحلتك الخاصة مع القرآن", "Your own Quran journey")}</span><h1 style={{ marginTop: 8 }}>{tr("ثلاثة أسئلة، ثم خطة اليوم", "Three questions, then today's plan")}</h1>
            <p style={{ margin: "8px 0 0", color: "var(--ink-2)" }}>{tr("مجاني ومفتوح المصدر. لا حاجة لمركز: خطة يومية، خريطة حفظ، تدريب ذاتي، وتسميع ذكي — وادعُ والدك أو صديقك ليسمّع لك من هاتفه.", "Free and open source. No center needed: a daily plan, a memory map, self-practice, an AI check, and invite a parent or friend to listen from their phone.")}</p></div>
          <ol className="row" style={{ gap: 6, padding: 0, margin: 0, listStyle: "none" }}>
            {steps.map((s, i) => <li key={s} className="chip" style={{ background: i === step ? "var(--lapis)" : undefined, color: i === step ? "#fff" : undefined, borderColor: i < step ? "var(--s-strong)" : undefined }}>{i < step ? "✓ " : ""}{s}</li>)}
          </ol>

          {step === 0 && (
            <div className="stack">
              {GOALS.map((g) => (
                <button key={g.key} type="button" onClick={() => setGoal(g.key)} className="surface pad" style={{ textAlign: "start", cursor: "pointer", borderColor: goal === g.key ? "var(--lapis)" : undefined, boxShadow: goal === g.key ? "0 0 0 3px var(--lapis-tint)" : undefined }}>
                  <b style={{ fontFamily: "var(--font-display)", fontSize: 16 }}>{locale === "en" ? g.en : g.ar}</b>
                  <div className="muted" style={{ fontSize: 13 }}>{locale === "en" ? g.sub_en : g.sub_ar}</div>
                </button>
              ))}
            </div>
          )}
          {step === 1 && (
            <div className="stack">
              <p style={{ margin: 0, color: "var(--ink-2)" }}>{tr("انقر الأجزاء التي تحفظها الآن (ولو تقريبًا). سنبدأ بمراجعتها، وتسميعاتك الحقيقية تضبط الخريطة.", "Tap the Juz you already memorize, even roughly. We start with revision, and your real recitations calibrate the map.")}</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(64px, 1fr))", gap: 8 }}>
                {Array.from({ length: 30 }, (_, i) => 30 - i).map((n) => {
                  const on = juz.has(n);
                  return <button key={n} type="button" onClick={() => { const s = new Set(juz); if (on) s.delete(n); else s.add(n); setJuz(s); }} className="btn" style={{ height: 52, flexDirection: "column", gap: 0, background: on ? "var(--lapis)" : undefined, color: on ? "#fff" : undefined, borderColor: on ? "var(--lapis)" : undefined }}>
                    <span style={{ fontSize: 10.5, opacity: .8 }}>{tr("الجزء", "Juz")}</span><b className="num" style={{ fontSize: 16 }}>{fmtNum(n, locale)}</b>
                  </button>;
                })}
              </div>
              <div className="row" style={{ gap: 8 }}>
                <button type="button" className="btn sm" onClick={() => setJuz(new Set([30]))}>{tr("جزء عمّ فقط", "Juz 30 only")}</button>
                <button type="button" className="btn sm" onClick={() => setJuz(new Set(Array.from({ length: 30 }, (_, i) => i + 1)))}>{tr("الكل", "All")}</button>
                <button type="button" className="btn sm" onClick={() => setJuz(new Set())}>{tr("لا شيء بعد", "Nothing yet")}</button>
                <span className="muted" style={{ fontSize: 12.5 }}>{fmtNum(juz.size, locale)} {tr("جزء", "Juz")}</span>
              </div>
            </div>
          )}
          {step === 2 && (
            <div className="stack">
              <p style={{ margin: 0, color: "var(--ink-2)" }}>{tr("كم دقيقة يوميًا تستطيع أن تلتزم بها؟ الخطة تُقسَّم بين حفظ جديد ومراجعة قريبة ومراجعة بعيدة.", "How many minutes a day can you commit? The plan splits them between new memorization, near revision, and far revision.")}</p>
              <div className="row" style={{ gap: 8 }}>
                {[10, 20, 30, 45, 60].map((m) => <button key={m} type="button" className={`btn ${minutes === m ? "primary" : ""}`} onClick={() => setMinutes(m)}><b className="num">{fmtNum(m, locale)}</b>&nbsp;{tr("دقيقة", "min")}</button>)}
              </div>
            </div>
          )}
          {step === 3 && (
            <form className="stack" onSubmit={(e) => { e.preventDefault(); submit(); }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13 }}>{tr("الاسم الكامل", "Full name")}</span><input className="input" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} required minLength={3} /></label>
                <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13 }}>{tr("الجنس", "Gender")}</span><select className="input" value={f.gender} onChange={(e) => setF({ ...f, gender: e.target.value })}><option value="male">{tr("ذكر", "Male")}</option><option value="female">{tr("أنثى", "Female")}</option></select></label>
                <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13 }}>{tr("البريد الإلكتروني", "Email")}</span><input className="input" dir="ltr" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required /></label>
                <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13 }}>{tr("كلمة المرور (٨ أحرف فأكثر)", "Password (8+ characters)")}</span><input className="input" dir="ltr" type="password" minLength={8} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></label>
              </div>
              {err && <p role="alert" style={{ margin: 0, color: "var(--s-weak)", fontSize: 13.5 }}>{err}</p>}
              <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{tr("بإنشاء الحساب توافق على أن بياناتك تُستخدم لمتابعة حفظك فقط. لا إعلانات، ولا بيع بيانات، والكود مفتوح.", "By creating an account you agree that your data is used only to track your memorization. No ads, no data sales, and the code is open.")}</p>
              <button className="btn primary" disabled={busy} style={{ height: 48, fontSize: 15 }}>{busy ? "…" : tr("أنشئ رحلتي", "Create my journey")}</button>
            </form>
          )}
          <div className="row" style={{ justifyContent: "space-between" }}>
            <button type="button" className="btn" disabled={step === 0 || busy} onClick={() => setStep(step - 1)}>{tr("السابق", "Back")}</button>
            {step < 3 && <button type="button" className="btn primary" onClick={() => setStep(step + 1)}>{tr("التالي", "Next")}</button>}
          </div>
          <p className="muted" style={{ fontSize: 12.5 }}>{tr("لديك حساب أو مركز؟", "Have an account or a center?")} <Link href="/login">{tr("سجّل الدخول", "Sign in")}</Link></p>
        </div>
      </section>
    </main>
  );
}
