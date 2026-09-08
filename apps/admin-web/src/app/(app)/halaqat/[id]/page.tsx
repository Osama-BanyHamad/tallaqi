"use client";
import Link from "next/link";
import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum } from "@/lib/quran";
import { ErrorBox, Loading, Num, RetentionBar, fmtDate } from "@/components/ui";

type Seg = { id: string; purpose: string; from_ayah_index: number; to_ayah_index: number; from_key: { surah_name: string; ayah: number }; to_key: { surah_name: string; ayah: number }; completion: string };
type Row = { student_id: string; journey_id: string | null; name: string; code: string; attendance: string | null;
  journey: { memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; memorized_pages: number } | null;
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
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["today", id] }); setToast(t("saved")); setTimeout(() => setToast(null), 1500); },
  });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const d = q.data!;
  const present = d.roster.filter((r) => r.attendance === "present" || r.attendance === "late").length;
  return (
    <>
      <div className="page-head">
        <div><span className="eyebrow">{t("today_title")} · {fmtDate(d.date, locale)}</span><h1>{d.halaqah.name}</h1><p>{d.halaqah.branch_name} · {d.halaqah.schedule_summary} · {d.halaqah.teachers.map((x) => x.name).join("، ")}</p></div>
        <div className="ledger" style={{ margin: 0, borderBlock: 0 }}>
          <div><div className="label">{t("attendance")}</div><div className="value num"><Num v={present} /> / <Num v={d.roster.length} /></div></div>
        </div>
      </div>
      <div className="stack" style={{ gap: 10 }}>
        {d.roster.map((r) => (
          <article key={r.student_id} className="card" style={{ display: "grid", gridTemplateColumns: "minmax(180px, 1fr) auto minmax(280px, 1.4fr) auto", gap: 18, alignItems: "center" }}>
            <div>
              <Link href={r.journey_id ? `/journeys/${r.journey_id}` : "#"} style={{ fontWeight: 600, fontSize: 15 }}>{r.name}</Link>
              <div className="muted" style={{ fontSize: 12 }} dir="ltr">{r.code}</div>
              {r.journey && <div style={{ marginTop: 6 }}><RetentionBar v={r.journey.avg_retention} /> <span className="muted" style={{ fontSize: 12 }}>· <Num v={r.journey.memorized_pages} /> {t("page")}{r.journey.critical_ayat ? ` · ${fmtNum(r.journey.critical_ayat, locale)} ${t("critical_ayat")}` : ""}</span></div>}
            </div>
            <div role="radiogroup" aria-label={t("attendance")} style={{ display: "flex", gap: 4 }}>
              {ATT.map((s) => (
                <button key={s} role="radio" aria-checked={r.attendance === s} className="btn" onClick={() => mark.mutate({ student_id: r.student_id, status: s })}
                  style={{ padding: "5px 10px", fontSize: 12.5, background: r.attendance === s ? (s === "absent" ? "var(--s-weak)" : s === "present" ? "var(--s-strong)" : "var(--gold)") : undefined, color: r.attendance === s ? "#fff" : undefined, borderColor: r.attendance === s ? "transparent" : undefined }}>{t(s)}</button>
              ))}
            </div>
            <div className="stack" style={{ gap: 6 }}>
              {r.plan?.segments.length ? r.plan.segments.map((s) => (
                <Link key={s.id} href={`/tasmee/${r.journey_id}?purpose=${s.purpose}&from=${s.from_ayah_index}&to=${s.to_ayah_index}&segment=${s.id}&halaqah=${id}`} className="seg" style={{ opacity: s.completion === "verified" ? .55 : 1, textDecoration: "none", color: "inherit" }}>
                  <span className={`purpose ${s.purpose}`}>{t(`purpose_${s.purpose}` as Key)}</span>
                  <span style={{ fontSize: 13 }}>{s.from_key.surah_name} {fmtNum(s.from_key.ayah, locale)} → {s.to_key.surah_name} {fmtNum(s.to_key.ayah, locale)}</span>
                  <span className="num" style={{ fontSize: 12, color: s.completion === "verified" ? "var(--s-strong)" : "var(--ink-3)" }}>{s.completion === "verified" ? "✓" : "→"}</span>
                </Link>
              )) : <span className="muted" style={{ fontSize: 13 }}>{r.plan?.paused_new ? "إيقاف مؤقت للحفظ الجديد" : "—"}</span>}
            </div>
            <div className="muted" style={{ fontSize: 12, textAlign: "end", minWidth: 110 }}>
              {r.last_session ? <>{fmtDate(r.last_session.started_at, locale)}<br />{t(`outcome_${r.last_session.outcome}` as Key)}</> : "—"}
            </div>
          </article>
        ))}
      </div>
      {toast && <div className="toast" role="status">{toast}</div>}
    </>
  );
}
