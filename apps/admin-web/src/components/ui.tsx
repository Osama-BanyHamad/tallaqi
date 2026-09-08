"use client";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum, fmtPct } from "@/lib/quran";

export function StatePill({ state }: { state: string }) {
  const { t } = useI18n();
  return <span className={`chip state-${state}`}><i className="dot" />{t(`state_${state}` as Key)}</span>;
}
export function Pct({ v }: { v: number | null | undefined }) { const { locale } = useI18n(); return <span className="num">{fmtPct(v, locale)}</span>; }
export function Num({ v }: { v: number | null | undefined }) { const { locale } = useI18n(); return <span className="num">{fmtNum(v, locale)}</span>; }
export function Loading() { const { t } = useI18n(); return <p className="muted">{t("loading")}</p>; }
export function Empty({ text }: { text?: string }) { const { t } = useI18n(); return <p className="muted">{text ?? t("empty")}</p>; }
export function ErrorBox({ e }: { e: unknown }) { const { t } = useI18n(); return <p role="alert" style={{ color: "var(--s-weak)" }}>{t("error")}: {(e as Error)?.message}</p>; }

export function retentionColor(v: number | null | undefined) {
  const pct = Math.round((v ?? 0) * 100);
  return pct >= 85 ? "var(--s-strong)" : pct >= 60 ? "var(--s-needs)" : pct >= 35 ? "var(--s-weak)" : "var(--s-critical)";
}
export function RetentionBar({ v, width }: { v: number | null | undefined; width?: number }) {
  const pct = Math.round((v ?? 0) * 100);
  return (
    <span className="bar">
      <span className="track" style={{ width: width ?? 90 }}><span className="fill" style={{ width: `${pct}%`, background: retentionColor(v) }} /></span>
      <Pct v={v} />
    </span>
  );
}

const TONES = ["#1b2c74", "#2f7a5b", "#3c9aa2", "#7a4a9a", "#b0662a", "#4a5f8f"];
export function Avatar({ name, small }: { name: string; small?: boolean }) {
  const parts = name.replace(/^(أبو|أم|د\.|الشيخ|الأستاذة|الأستاذ)\s+/u, "").split(/\s+/).filter(Boolean);
  const initials = parts.slice(0, 2).map((p) => p[0]).join("");
  let h = 0; for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return <span className={`avatar ${small ? "sm" : ""}`} style={{ ["--tone" as string]: TONES[h % TONES.length] }} aria-hidden>{initials}</span>;
}

/** 30 cells, Juz 1 → 30 right-to-left; each coloured by the materialized Juz state. */
export function JuzStrip({ map, large }: { map?: [number, number | null, string][] | null; large?: boolean }) {
  const cells: { cov: number; state: string }[] = Array.from({ length: 30 }, (_, i) => {
    const c = map?.[i];
    return { cov: Number(c?.[0] ?? 0), state: String(c?.[2] ?? "not_memorized") };
  });
  return (
    <span className={`juzstrip ${large ? "lg" : ""}`} title="Juz 1 → 30">
      {cells.map((c, i) => <i key={i} data-s={c.cov > 0 ? c.state : "not_memorized"} style={{ opacity: c.cov > 0 ? 0.55 + c.cov * 0.45 : 1 }} />)}
    </span>
  );
}

export function Kpi({ label, value, sub, tone, accent, unit }: { label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: "ok" | "behind" | "attention"; accent?: boolean; unit?: string }) {
  return (
    <div className={`kpi ${accent ? "accent" : ""} ${tone ? `tone-${tone}` : ""}`}>
      <div className="l">{label}</div>
      <div className="v">{value}{unit && <small>{unit}</small>}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

export function PageHead({ eyebrow, title, sub, actions }: { eyebrow: string; title: React.ReactNode; sub?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="page-head fade-up">
      <div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{sub && <p>{sub}</p>}</div>
      {actions && <div className="row">{actions}</div>}
    </div>
  );
}

export function fmtDate(iso: string | null | undefined, locale: "ar" | "en") {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-JO" : "en-GB", { dateStyle: "medium" }).format(new Date(iso));
}
