"use client";
import Link from "next/link";
import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum } from "@/lib/quran";
import { Avatar, ErrorBox, JuzStrip, Kpi, Loading, Num, PageHead, RetentionBar, fmtDate } from "@/components/ui";

type Seg = { id: string; purpose: string; from_ayah_index: number; to_ayah_index: number; from_key: { surah_name: string; ayah: number }; to_key: { surah_name: string; ayah: number }; completion: string };
type Row = { student_id: string; journey_id: string | null; name: string; code: string; attendance: string | null;
  journey: { memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; memorized_pages: number; juz_map: [number, number | null, string][] } | null;
  plan: { status: string; paused_new: boolean; segments: Seg[] } | null; last_session: { started_at: string; outcome: string; purpose: string } | null };
type Today = { halaqah: { id: string; name: string; branch_name: string; schedule_summary: string; teachers: { name: string }[] }; date: string; roster: Row[] };
const ATT = ["present", "late", "absent", "excused"] as const;

export default function HalaqahToday({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [toast, setToast] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["today", id], queryFn: () => api<Today>(`/halaqat/${id}/today`) });
  const mark = useMutation({
    mutationFn: (v: { student_id: string; status: string }) => api(`/halaqat/${id}/attendance`, { method: "POST", json: { records: [v] } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["today", id] }); setToast(t("saved")); setTimeout(() => setToast(null), 1400); },
  });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const d = q.data!;
  const present = d.roster.filter((r) => r.attendance === "present" || r.attendance === "late").length;
  const pending = d.roster.reduce((n, r) => n + (r.plan?.segments.filter((s) => s.completion !== "verified").length ?? 0), 0);
  return (
    <>
      <PageHead eyebrow={`${t("today_title")} · ${fmtDate(d.date, locale)}`} title={d.halaqah.name} sub={`${d.halaqah.branch_name} · ${d.halaqah.schedule_summary} · ${d.halaqah.teachers.map((x) => x.name).join("، ")}`} />
      <div className="kpis stagger" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px, 220px))" }}>
        <Kpi accent label={t("attendance")} value={<><Num v={present} /><small>/ {fmtNum(d.roster.length, locale)}</small></>} />
        <Kpi label={locale === "ar" ? "مقاطع بانتظار التسميع" : "Segments awaiting Tasmee'"} value={<Num v={pending} />} />
      </div>
      <div className="list stagger">
        {d.roster.map((r) => (
          <article key={r.student_id} className="surface" style={{ display: "grid", gridTemplateColumns: "minmax(220px, 1fr) auto minmax(300px, 1.3fr) auto", gap: 20, alignItems: "center", padding: "16px 20px" }}>
            <div className="row" style={{ gap: 14, flexWrap: "nowrap" }}>
              <Avatar name={r.name} />
              <div style={{ minWidth: 0 }}>
                <Link href={r.journey_id ? `/journeys/${r.journey_id}` : "#"} style={{ fontWeight: 600, fontSize: 15.5, color: "inherit" }}>{r.name}</Link>
                <div className="muted" style={{ fontSize: 12 }} dir="ltr">{r.code}</div>
                {r.journey && <div style={{ marginTop: 8, display: "grid", gap: 6, maxWidth: 220 }}><JuzStrip map={r.journey.juz_map} /><RetentionBar v={r.journey.avg_retention} width={70} /></div>}
              </div>
            </div>
            <div className="seg-btns" role="radiogroup" aria-label={t("attendance")}>
              {ATT.map((s) => <button key={s} role="radio" data-v={s} aria-checked={r.attendance === s} onClick={() => mark.mutate({ student_id: r.student_id, status: s })}>{t(s)}</button>)}
            </div>
            <div className="stack" style={{ gap: 6 }}>
              {r.plan?.segments.length ? r.plan.segments.map((s) => (
                <Link key={s.id} href={`/tasmee/${r.journey_id}?purpose=${s.purpose}&from=${s.from_ayah_index}&to=${s.to_ayah_index}&segment=${s.id}&halaqah=${id}`} className="seg" style={{ opacity: s.completion === "verified" ? .55 : 1 }}>
                  <span className={`purpose ${s.purpose}`}>{t(`purpose_${s.purpose}` as Key)}</span>
                  <span style={{ fontSize: 13.5 }}>{s.from_key.surah_name} {fmtNum(s.from_key.ayah, locale)} → {s.to_key.surah_name} {fmtNum(s.to_key.ayah, locale)}</span>
                  <span className="num" style={{ fontSize: 13, color: s.completion === "verified" ? "var(--s-strong)" : "var(--gold)" }}>{s.completion === "verified" ? "✓" : locale === "ar" ? "سمّع" : "Recite"}</span>
                </Link>
              )) : <span className="muted" style={{ fontSize: 13 }}>{r.plan?.paused_new ? (locale === "ar" ? "إيقاف مؤقت للحفظ الجديد" : "New memorization paused") : "—"}</span>}
            </div>
            <div className="muted" style={{ fontSize: 12.5, textAlign: "end", minWidth: 110 }}>
              {r.last_session ? <>{fmtDate(r.last_session.started_at, locale)}<br /><span className="chip" style={{ marginTop: 4, ["--dot" as string]: r.last_session.outcome === "pass" ? "var(--s-strong)" : "var(--s-weak)" }}><i className="dot" />{t(`outcome_${r.last_session.outcome}` as Key)}</span></> : "—"}
            </div>
          </article>
        ))}
      </div>
      {toast && <div className="toast" role="status">{toast}</div>}
    </>
  );
}
