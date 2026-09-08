"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { SampleMap } from "@/components/SampleMap";

export default function LoginPage() {
  const { t, locale, setLocale } = useI18n();
  const r = useRouter();
  const [email, setEmail] = useState("owner@demo.talaqqi");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try { await login(email, password); r.replace("/dashboard"); }
    catch (ex) { setErr((ex as Error).message); }
    finally { setBusy(false); }
  }

  return (
    <main className="login" style={{ minHeight: "100dvh", display: "grid", gridTemplateColumns: "minmax(0,1.1fr) minmax(380px,.9fr)" }}>
      <section style={{ position: "relative", overflow: "hidden", background: "radial-gradient(900px 500px at 85% -10%, var(--night-2), var(--night))", color: "var(--night-ink)", padding: "56px 64px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <div className="lattice" />
        <div style={{ position: "relative" }}>
          <Link href="/" className="wordmark"><span className="ar" style={{ fontSize: 64 }}>تَلَقِّي</span><span className="latin">Talaqqi</span></Link>
          <p style={{ marginTop: 30, maxWidth: "36ch", fontSize: 20, lineHeight: 1.75, color: "var(--night-ink)" }} className="fade-up">
            {locale === "ar" ? "رحلة الطالب مع القرآن: ما حُفظ، وما ثبت، وما يُراجَع اليوم — بيد المعلم، وبعين المشرف، وبطمأنينة ولي الأمر." : "The student's Quran journey: what was memorized, what stays strong, and what to revise today — in the teacher's hands, under the supervisor's eye, with the parent's peace of mind."}
          </p>
        </div>
        <div style={{ position: "relative", marginTop: 30 }} className="fade-up"><SampleMap dark /></div>
        <p style={{ position: "relative", fontSize: 12, color: "var(--night-muted)", marginTop: 24 }}>{t("quran_attribution")} · AGPL-3.0</p>
      </section>
      <section style={{ display: "grid", placeItems: "center", padding: 40 }}>
        <form onSubmit={submit} className="stack fade-up" style={{ width: "min(400px, 100%)", gap: 18 }}>
          <div><span className="eyebrow">{t("app")}</span><h1 style={{ marginTop: 8 }}>{t("login_title")}</h1></div>
          <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{t("email")}</span><input className="input" dir="ltr" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label className="stack" style={{ gap: 6 }}><span style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{t("password")}</span><input className="input" dir="ltr" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {err && <p role="alert" style={{ margin: 0, color: "var(--s-weak)", fontSize: 13.5 }}>{err}</p>}
          <button className="btn primary" disabled={busy} style={{ height: 46, fontSize: 15 }}>{t("login_btn")}</button>
          <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{t("login_hint")}</p>
          <div className="row"><button type="button" className="btn sm" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>{t("switch_lang")}</button><Link href="/" className="btn sm">{locale === "ar" ? "الموقع العام" : "Public site"}</Link></div>
        </form>
      </section>
      <style>{`@media (max-width: 900px){ .login { grid-template-columns: 1fr !important; } }`}</style>
    </main>
  );
}
