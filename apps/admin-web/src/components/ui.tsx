"use client";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum, fmtPct } from "@/lib/quran";

export function StatePill({ state }: { state: string }) {
  const { t } = useI18n();
  return <span className={`pill state-${state}`}><i className="dot" />{t(`state_${state}` as Key)}</span>;
}

export function Pct({ v }: { v: number | null | undefined }) {
  const { locale } = useI18n();
  return <span className="num">{fmtPct(v, locale)}</span>;
}
export function Num({ v }: { v: number | null | undefined }) {
  const { locale } = useI18n();
  return <span className="num">{fmtNum(v, locale)}</span>;
}

export function Loading() { const { t } = useI18n(); return <p className="muted">{t("loading")}</p>; }
export function Empty({ text }: { text?: string }) { const { t } = useI18n(); return <p className="muted">{text ?? t("empty")}</p>; }
export function ErrorBox({ e }: { e: unknown }) {
  const { t } = useI18n();
  return <p role="alert" style={{ color: "var(--s-weak)" }}>{t("error")}: {(e as Error)?.message}</p>;
}

export function RetentionBar({ v }: { v: number | null | undefined }) {
  const pct = Math.round((v ?? 0) * 100);
  const color = pct >= 85 ? "var(--s-strong)" : pct >= 60 ? "var(--s-needs)" : pct >= 35 ? "var(--s-weak)" : "var(--s-critical)";
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <span style={{ width: 64, height: 6, background: "var(--paper-3)", borderRadius: 3, overflow: "hidden", display: "inline-block" }}>
        <span style={{ display: "block", width: `${pct}%`, height: "100%", background: color }} />
      </span>
      <Pct v={v} />
    </span>
  );
}

export function fmtDate(iso: string | null | undefined, locale: "ar" | "en") {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-JO" : "en-GB", { dateStyle: "medium" }).format(new Date(iso));
}
