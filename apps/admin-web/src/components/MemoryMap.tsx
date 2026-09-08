"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum } from "@/lib/quran";
import { Loading, Num, Pct, StatePill } from "@/components/ui";

type Unit = { number: number; state: string; coverage: number; avg_retention: number | null; memorized_ayat: number; total_ayat: number; due_ayat: number };
type Quran = { level: "quran"; units: Unit[] };
type Juz = { level: "juz"; number: number; units: Unit[] } & Unit;
type PageUnits = { level: "page"; number: number; juz: number; units: AyahRow[] } & Unit;
export type AyahRow = { ayah_index: number; key: string; surah: number; ayah: number; page: number; text_uthmani: string; state: string; retention_score: number;
  stability_days?: number; last_passed_at?: string | null; next_due_at?: string | null; success_count?: number; fail_count?: number; explanation: string[] };

const STATES = ["mastered", "strong", "recent", "needs_revision", "weak", "critical", "learning", "not_memorized"];

/** The signature: 30 Juz rows × their pages, each page a folio tile coloured by retention state. Quran → Juz → Page. */
export function MemoryMap({ journeyId, onSelectPage }: { journeyId: string; onSelectPage: (page: number | null) => void }) {
  const { t, locale } = useI18n();
  const [juz, setJuz] = useState<number | null>(null);
  const [page, setPage] = useState<number | null>(null);
  const quran = useQuery({ queryKey: ["mm", journeyId, "quran"], queryFn: () => api<Quran>(`/journeys/${journeyId}/memory-map?level=quran`) });
  const juzQ = useQuery({ queryKey: ["mm", journeyId, "juz", juz], queryFn: () => api<Juz>(`/journeys/${journeyId}/memory-map?level=juz&number=${juz}`), enabled: juz != null });
  const pages = useQuery({ queryKey: ["quran-pages"], queryFn: () => api<{ number: number; juz: number }[]>("/quran/hafs_asim/units/page"), staleTime: Infinity });
  if (quran.isLoading || pages.isLoading) return <Loading />;
  const byJuz: Record<number, number[]> = {};
  pages.data?.forEach((p) => { (byJuz[p.juz] ??= []).push(p.number); });
  const maxCols = Math.max(...Object.values(byJuz).map((a) => a.length));

  function pick(p: number) { const n = page === p ? null : p; setPage(n); onSelectPage(n); }

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>{t("memory_map")}</h2>
        {juz != null && <button className="btn" onClick={() => { setJuz(null); setPage(null); onSelectPage(null); }}>{t("quran_level")} ↩</button>}
      </div>
      {juz == null ? (
        <div className="mmap" style={{ ["--cols" as string]: maxCols }}>
          {quran.data!.units.map((u) => (
            <div key={u.number} className="mmap-row">
              <button className="juz" onClick={() => setJuz(u.number)} style={{ background: "none", border: 0, cursor: "pointer", textAlign: "start", padding: 0 }}>{t("juz")} {fmtNum(u.number, locale)}</button>
              <div className="pages">
                {byJuz[u.number].map((p) => <PageFolio key={p} journeyId={journeyId} page={p} juzState={u} selected={page === p} onClick={() => { setJuz(u.number); pick(p); }} />)}
              </div>
              <span className="stat">{u.avg_retention == null ? "—" : `${Math.round(u.avg_retention * 100)}%`}</span>
            </div>
          ))}
        </div>
      ) : juzQ.isLoading ? <Loading /> : (
        <div className="stack">
          <div className="row" style={{ gap: 18 }}>
            <h3>{t("juz")} {fmtNum(juz, locale)}</h3>
            <StatePill state={juzQ.data!.state} />
            <span className="muted" style={{ fontSize: 13 }}>{t("coverage")} <Pct v={juzQ.data!.coverage} /> · {t("avg_retention")} <Pct v={juzQ.data!.avg_retention} /> · <Num v={juzQ.data!.due_ayat} /> {t("due")}</span>
          </div>
          <div className="pages" style={{ display: "grid", gridTemplateColumns: `repeat(${juzQ.data!.units.length}, 1fr)`, gap: 6 }}>
            {juzQ.data!.units.map((u) => (
              <button key={u.number} className={`folio bg-${u.state} ${page === u.number ? "selected" : ""}`} style={{ height: 54 }} title={`${t("page")} ${u.number}`} onClick={() => pick(u.number)}>
                {u.due_ayat > 0 && <span className="due" />}
                <span style={{ position: "absolute", bottom: 3, insetInlineStart: 0, insetInlineEnd: 0, fontSize: 10, fontFamily: "var(--font-mono)", color: "rgba(255,255,255,.9)", mixBlendMode: "difference" }}>{u.number}</span>
              </button>
            ))}
          </div>
        </div>
      )}
      <div className="legend">
        {STATES.map((s) => <span key={s}><i className={`bg-${s}`} />{t(`state_${s}` as Key)}</span>)}
        <span><i style={{ background: "var(--gold)", width: 8, height: 8, borderRadius: "50%" }} />{t("due")}</span>
      </div>
    </div>
  );
}

function PageFolio({ journeyId, page, juzState, selected, onClick }: { journeyId: string; page: number; juzState: Unit; selected: boolean; onClick: () => void }) {
  // Quran-level view colours pages by the Juz aggregate to stay cheap; the Juz view fetches page-level states.
  void journeyId;
  const state = juzState.memorized_ayat === 0 ? "not_memorized" : juzState.state;
  return <button className={`folio bg-${state} ${selected ? "selected" : ""}`} title={`${page}`} onClick={onClick} style={{ opacity: juzState.coverage === 0 ? .6 : .55 + juzState.coverage * .45 }} />;
}

export function PageDetail({ journeyId, page }: { journeyId: string; page: number }) {
  const { t, locale } = useI18n();
  const q = useQuery({ queryKey: ["mm", journeyId, "page", page], queryFn: () => api<PageUnits>(`/journeys/${journeyId}/memory-map?level=page&number=${page}`) });
  if (q.isLoading) return <Loading />;
  const d = q.data!;
  return (
    <div className="stack" style={{ gap: 10 }}>
      <div className="row" style={{ gap: 14 }}><h3>{t("page")} {fmtNum(page, locale)}</h3><StatePill state={d.state} /><span className="muted" style={{ fontSize: 13 }}>{t("avg_retention")} <Pct v={d.avg_retention} /></span></div>
      <div className="stack" style={{ gap: 6 }}>
        {d.units.map((a) => (
          <details key={a.key} className="card" style={{ padding: "8px 12px" }}>
            <summary style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", listStyle: "none" }}>
              <span className={`pill state-${a.state}`} style={{ minWidth: 100, justifyContent: "center" }}><i className="dot" />{t(`state_${a.state}` as Key)}</span>
              <span className="num" style={{ fontSize: 12, color: "var(--ink-3)", minWidth: 44 }}>{a.key}</span>
              <span className="quran grow" style={{ fontSize: 20, lineHeight: 1.8, textAlign: "start", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{a.text_uthmani}</span>
              <span className="num" style={{ fontSize: 12 }}>{Math.round(a.retention_score * 100)}%</span>
            </summary>
            <div style={{ marginTop: 8, fontSize: 13, color: "var(--ink-2)" }}>
              <p className="quran" style={{ fontSize: 22, margin: "0 0 8px" }}>{a.text_uthmani}</p>
              <ul style={{ margin: 0, paddingInlineStart: 18 }}>{a.explanation.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
