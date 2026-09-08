"use client";
import Link from "next/link";
import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum } from "@/lib/quran";
import { MemoryMap, PageDetail } from "@/components/MemoryMap";
import { Avatar, ErrorBox, JuzStrip, Kpi, Loading, Num, Pct, RetentionBar, fmtDate } from "@/components/ui";

type Journey = { id: string; student: string; student_name: string; student_code: string; riwayah: string; policy_key: string; status: string; started_at: string; current_ayah_index: number | null;
  current_key: { key: string; surah: number; ayah: number; page: number; surah_name: string } | null; level: string; memorized_ayat: number; strong_ayat: number; needs_revision_ayat: number; weak_ayat: number; critical_ayat: number; mastered_ayat: number; avg_retention: number; memorized_pages: number; juz_map: [number, number | null, string][] };
type Seg = { id: string; purpose: string; from_ayah_index: number; to_ayah_index: number; from_key: { key: string; surah_name: string; ayah: number }; to_key: { key: string; surah_name: string; ayah: number }; pages: number[]; reason: string; completion: string };
type Plan = { id: string; plan_date: string; status: string; rationale: string[]; paused_new: boolean; segments: Seg[] };
type Ev = { id: string; event_type: string; payload: Record<string, unknown>; occurred_at: string };
type Sess = { id: string; purpose: string; from_key: string; to_key: string; started_at: string; outcome: string; teacher_name: string; mistakes: { mistake_type: string }[]; note: string };

const EV: Record<string, string> = { "journey.first_memorization": "بداية الحفظ", "surah.completed": "أتمّ سورة", "juz.completed": "أتمّ الجزء", "memory_map.override": "تعديل يدوي لخريطة الحفظ" };
const STATUS: Record<string, string> = { memorizing: "في الحفظ", retaining: "في المراجعة الطويلة", paused: "متوقف", completed_with_retention: "أتمّ الختم", ijazah_track: "مسار الإجازة" };

export default function JourneyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const [page, setPage] = useState<number | null>(null);
  const j = useQuery({ queryKey: ["journey", id], queryFn: () => api<Journey>(`/journeys/${id}`) });
  const plan = useQuery({ queryKey: ["plan", id], queryFn: () => api<Plan>(`/journeys/${id}/plan`) });
  const tl = useQuery({ queryKey: ["timeline", id], queryFn: () => api<Ev[]>(`/journeys/${id}/timeline`) });
  const sessions = useQuery({ queryKey: ["sessions", id], queryFn: () => api<Sess[]>(`/journeys/${id}/sessions`) });
  if (j.isLoading) return <Loading />;
  if (j.error) return <ErrorBox e={j.error} />;
  const d = j.data!;
  const pct = Math.round(d.avg_retention * 100);
  return (
    <>
      <div className="page-head fade-up" style={{ alignItems: "center" }}>
        <div className="row" style={{ gap: 20 }}>
          <Avatar name={d.student_name} />
          <div>
            <span className="eyebrow">{t("journey")} · {STATUS[d.status] ?? d.status}</span>
            <h1 style={{ marginTop: 6 }}>{d.student_name}</h1>
            <p style={{ marginTop: 4 }}><span className="num" dir="ltr">{d.student_code}</span> · حفص عن عاصم · {d.policy_key.replaceAll("_", " ")}</p>
          </div>
        </div>
        {d.current_key && <Link className="btn gold" href={`/tasmee/${d.id}?purpose=new&from=${d.current_ayah_index}&to=${Math.min(d.current_ayah_index! + 7, 6236)}`}>{t("start_tasmee")}</Link>}
      </div>
      <div className="surface pad fade-up" style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 28, alignItems: "center", marginBottom: 26 }}>
        <div className="ring" style={{ ["--p" as string]: pct }}><div>{fmtNum(pct, locale)}٪<small>{t("avg_retention")}</small></div></div>
        <div className="stack" style={{ gap: 14 }}>
          <JuzStrip map={d.juz_map} large />
          <div className="kpis" style={{ marginBottom: 0, gap: 10 }}>
            <Kpi label={t("memorized_pages")} value={<Num v={d.memorized_pages} />} />
            <Kpi label={t("memorized")} value={<Num v={d.memorized_ayat} />} unit={t("ayat")} />
            <Kpi label={`${t("state_weak")} / ${t("state_critical")}`} tone={d.critical_ayat ? "attention" : undefined} value={<><Num v={d.weak_ayat} /> / <Num v={d.critical_ayat} /></>} />
            <Kpi label={t("position")} value={<span style={{ fontSize: 20 }}>{d.current_key ? `${d.current_key.surah_name} ${fmtNum(d.current_key.ayah, locale)}` : "—"}</span>} sub={d.current_key ? `${t("page")} ${fmtNum(d.current_key.page, locale)}` : undefined} />
          </div>
        </div>
      </div>
      <div className="with-margin">
        <div className="stack" style={{ gap: 34 }}>
          <div className="surface pad"><MemoryMap journeyId={id} onSelectPage={setPage} /></div>
          {page != null && <PageDetail journeyId={id} page={page} />}
          <section>
            <div className="section-title"><h2>{t("sessions")}</h2><small>{sessions.data?.length ?? 0}</small></div>
            {sessions.data?.length ? (
              <div className="tbl"><table>
                <thead><tr><th>{t("timeline")}</th><th>{t("purpose_new")}/{t("purpose_near")}</th><th>{t("ayah")}</th><th>{t("status")}</th><th>{t("mistakes")}</th><th>{t("teacher")}</th></tr></thead>
                <tbody>{sessions.data.slice(0, 25).map((s) => (
                  <tr key={s.id}><td className="num" style={{ fontSize: 12.5 }}>{fmtDate(s.started_at, locale)}</td><td>{t(`purpose_${s.purpose}` as Key)}</td><td className="num" dir="ltr">{s.from_key} → {s.to_key}</td>
                    <td><span className="chip" style={{ ["--dot" as string]: s.outcome === "pass" ? "var(--s-strong)" : s.outcome === "repeat" ? "var(--s-weak)" : "var(--s-needs)" }}><i className="dot" />{t(`outcome_${s.outcome}` as Key)}</span></td>
                    <td className="num"><Num v={s.mistakes.length} /></td><td>{s.teacher_name || "—"}</td></tr>))}</tbody>
              </table></div>) : <p className="muted">{t("empty")}</p>}
          </section>
        </div>
        <aside className="hashiya">
          <div>
            <h3>{t("todays_plan")}</h3>
            {plan.data ? (
              <div className="stack" style={{ gap: 8 }}>
                {plan.data.segments.map((s) => (
                  <Link key={s.id} href={`/tasmee/${id}?purpose=${s.purpose}&from=${s.from_ayah_index}&to=${s.to_ayah_index}&segment=${s.id}`} className="seg" style={{ gridTemplateColumns: "auto 1fr" }}>
                    <span className={`purpose ${s.purpose}`}>{t(`purpose_${s.purpose}` as Key)}</span>
                    <span style={{ fontSize: 13 }}>{s.from_key.surah_name} {fmtNum(s.from_key.ayah, locale)} → {s.to_key.surah_name} {fmtNum(s.to_key.ayah, locale)}<br /><span className="muted" style={{ fontSize: 12 }}>{s.reason}</span></span>
                  </Link>
                ))}
                {plan.data.rationale.map((r, i) => <p key={i} style={{ fontSize: 12.5 }}>{r}</p>)}
              </div>
            ) : <Loading />}
          </div>
          <div>
            <h3>{t("timeline")}</h3>
            <ul className="timeline">
              {(tl.data ?? []).slice(0, 12).map((e) => (
                <li key={e.id}><time>{fmtDate(e.occurred_at, locale)}</time><span>{EV[e.event_type] ?? e.event_type}{e.payload?.name_ar ? ` — ${e.payload.name_ar as string}` : e.payload?.juz ? ` ${fmtNum(e.payload.juz as number, locale)}` : ""}</span></li>
              ))}
            </ul>
          </div>
          <div>
            <h3>{t("explanation")}</h3>
            <p>{locale === "ar" ? "الثبات مقياس تعليمي لاستقرار الاسترجاع، يُحسب حتميًا من تسميعات المعلم وأخطائه وزمن المراجعة. ليس حكمًا شرعيًا على التلاوة." : "Retention is an educational measure of recall stability, computed deterministically from teacher-verified recitations, mistakes, and time. It is not a religious judgment."}</p>
            <div className="row" style={{ marginTop: 8 }}><RetentionBar v={d.avg_retention} /></div>
          </div>
        </aside>
      </div>
    </>
  );
}
