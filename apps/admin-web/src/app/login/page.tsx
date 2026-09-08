"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/* 604 folios: the memory-map motif, used once as the login's signature. */
const FOLIOS = Array.from({ length: 604 }, (_, i) => i);

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
    <main style={{ minHeight: "100dvh", display: "grid", gridTemplateColumns: "minmax(0,1.1fr) minmax(360px,0.9fr)" }} className="login">
      <section style={{ background: "var(--spine)", color: "var(--spine-ink)", padding: "48px 56px", display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative", overflow: "hidden" }}>
        <div>
          <div className="wordmark"><span className="ar">تَلَقِّي</span><span className="latin">Talaqqi</span></div>
          <p style={{ marginTop: 26, maxWidth: "34ch", fontSize: 18, lineHeight: 1.7, color: "var(--spine-ink)" }}>
            {locale === "ar" ? "رحلة الطالب مع القرآن: ما حُفظ، وما ثبت، وما يُراجَع اليوم — بيد المعلم، وبعين المشرف، وبطمأنينة ولي الأمر." : "The student's Quran journey: what was memorized, what stays strong, and what to revise today — in the teacher's hands, under the supervisor's eye, with the parent's peace of mind."}
          </p>
        </div>
        <div aria-hidden style={{ display: "grid", gridTemplateColumns: "repeat(38, 1fr)", gap: 3, opacity: .9, marginTop: 30 }}>
          {FOLIOS.map((i) => {
            // deterministic hash → looks like a real memory map (Juz 30 strong, earlier Juz sparse), not a wave
            const h = ((i * 2654435761) >>> 0) % 1000 / 1000;
            const row = Math.floor(i / 38);
            const v = h * 0.55 + (row / 16) * 0.45;
            const c = v > .78 ? "var(--s-mastered)" : v > .55 ? "var(--s-strong)" : v > .4 ? "var(--s-recent)" : v > .25 ? "var(--s-needs)" : "rgba(255,255,255,.08)";
            return <span key={i} style={{ height: 9, borderRadius: 1, background: c }} />;
          })}
        </div>
        <p style={{ fontSize: 12, color: "var(--spine-muted)", marginTop: 20 }}>{t("quran_attribution")} · AGPL-3.0</p>
      </section>
      <section style={{ display: "grid", placeItems: "center", padding: 40 }}>
        <form onSubmit={submit} className="stack" style={{ width: "min(380px, 100%)" }}>
          <div>
            <span className="eyebrow">{t("app")}</span>
            <h1 style={{ marginTop: 6 }}>{t("login_title")}</h1>
          </div>
          <label className="stack" style={{ gap: 6 }}>
            <span style={{ fontSize: 13, color: "var(--ink-2)" }}>{t("email")}</span>
            <input className="input" dir="ltr" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label className="stack" style={{ gap: 6 }}>
            <span style={{ fontSize: 13, color: "var(--ink-2)" }}>{t("password")}</span>
            <input className="input" dir="ltr" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {err && <p role="alert" style={{ margin: 0, color: "var(--s-weak)", fontSize: 13.5 }}>{err}</p>}
          <button className="btn primary" disabled={busy} style={{ justifyContent: "center", padding: "11px 14px" }}>{t("login_btn")}</button>
          <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{t("login_hint")}</p>
          <button type="button" className="btn" onClick={() => setLocale(locale === "ar" ? "en" : "ar")} style={{ alignSelf: "flex-start" }}>{t("switch_lang")}</button>
        </form>
      </section>
      <style>{`@media (max-width: 860px){ .login { grid-template-columns: 1fr !important; } }`}</style>
    </main>
  );
}
