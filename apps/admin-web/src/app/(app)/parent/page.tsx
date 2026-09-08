"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { fmtNum } from "@/lib/quran";
import { Avatar, ErrorBox, JuzStrip, Kpi, Loading, Num, PageHead, Pct, RetentionBar, fmtDate } from "@/components/ui";

type Student = { id: string; person: { display_name_ar: string }; branch_name: string; halaqah: { name: string } | null; journey_summary: { id: string; memorized_pages: number; avg_retention: number; juz_map: [number, number | null, string][] } | null };
type Weekly = { student: { name: string }; week: { from: string; to: string }; attendance: { present: number; total: number }; new_pages: number; revision_pages: number; sessions: number; passed: number; retention: number | null; memorized_pages: number; weak_ayat: number; critical_ayat: number; juz_map: [number, number | null, string][]; teacher_note: string; plan: { segments: { id: string; purpose: string; from_key: { surah_name: string; ayah: number }; to_key: { surah_name: string; ayah: number } }[] } | null; current: { key: string; surah_name: string } | null };

/** The parent portal: the six questions, nothing else. */
export default function ParentPage() {
  const { t, locale } = useI18n();
  const tr = useT2();
  const [sel, setSel] = useState<string | null>(null);
  const kids = useQuery({ queryKey: ["my-children"], queryFn: () => api<{ results: Student[] }>("/students?page_size=20") });
  const id = sel ?? kids.data?.results[0]?.id ?? null;
  const w = useQuery({ queryKey: ["weekly", id], queryFn: () => api<Weekly>(`/students/${id}/weekly`), enabled: !!id });
  if (kids.isLoading) return <Loading />;
  if (kids.error) return <ErrorBox e={kids.error} />;
  const list = kids.data!.results;
  const d = w.data;
  return (
    <>
      <PageHead eyebrow={tr("ولي الأمر", "Parent")} title={tr("أبنائي", "My children")} sub={tr("هل حضر؟ ماذا حفظ؟ ماذا راجع؟ هل يتحسّن؟ ماذا يوصي المعلم؟ ما المطلوب اليوم؟", "Did they attend? What did they memorize and revise? Are they improving? What does the teacher recommend? What is due today?")} />
      <div className="row" style={{ gap: 8, marginBottom: 22 }}>
        {list.map((s) => <button key={s.id} className={`btn ${id === s.id ? "primary" : ""}`} onClick={() => setSel(s.id)}><Avatar name={s.person.display_name_ar} small />{s.person.display_name_ar}</button>)}
      </div>
      {!id ? <p className="muted">{t("empty")}</p> : w.isLoading || !d ? <Loading /> : (
        <div className="with-margin">
          <div className="stack" style={{ gap: 22 }}>
            <div className="kpis stagger">
              <Kpi accent label={t("attendance")} value={<><Num v={d.attendance.present} /><small>/ {fmtNum(d.attendance.total, locale)}</small></>} sub={`${fmtDate(d.week.from, locale)} → ${fmtDate(d.week.to, locale)}`} />
              <Kpi label={t("purpose_new")} value={<Num v={d.new_pages} />} unit={t("page")} />
              <Kpi label={tr("مراجعة", "Revision")} value={<Num v={d.revision_pages} />} unit={t("page")} />
              <Kpi label={t("retention")} value={<Pct v={d.retention} />} tone={d.retention != null && d.retention < 0.6 ? "attention" : undefined} />
            </div>
            <div className="surface pad"><JuzStrip map={d.juz_map} large /><div className="muted" style={{ marginTop: 8, fontSize: 13 }}><Num v={d.memorized_pages} /> {t("memorized_pages")}</div></div>
            <Answer q={tr("هل يتحسّن؟", "Improving?")} a={d.critical_ayat === 0 ? tr(`نعم. لا آيات حرجة هذا الأسبوع، واجتاز ${fmtNum(d.passed, "ar")} من ${fmtNum(d.sessions, "ar")} تسميعات.`, `Yes. No critical Ayat this week; passed ${d.passed} of ${d.sessions} recitations.`) : tr(`يحتاج متابعة: ${fmtNum(d.critical_ayat, "ar")} آيات حرجة و${fmtNum(d.weak_ayat, "ar")} ضعيفة.`, `Needs follow-up: ${d.critical_ayat} critical and ${d.weak_ayat} weak Ayat.`)} />
            <Answer q={tr("ماذا يوصي المعلم؟", "Teacher's note")} a={d.teacher_note || tr("لا توجد ملاحظة هذا الأسبوع.", "No note this week.")} />
            {d.current && <Answer q={tr("أين وصل؟", "Where are they?")} a={`${d.current.surah_name} — ${d.current.key}`} />}
          </div>
          <aside className="hashiya">
            <div><h3>{t("todays_plan")}</h3>
              <div className="stack" style={{ gap: 8 }}>
                {(d.plan?.segments ?? []).map((s) => <div key={s.id} className="seg" style={{ gridTemplateColumns: "auto 1fr" }}><span className={`purpose ${s.purpose}`}>{t(`purpose_${s.purpose}` as Key)}</span><span style={{ fontSize: 13 }}>{s.from_key.surah_name} {fmtNum(s.from_key.ayah, locale)} → {s.to_key.surah_name} {fmtNum(s.to_key.ayah, locale)}</span></div>)}
                {(d.plan?.segments.length ?? 0) === 0 && <p className="muted">—</p>}
              </div>
            </div>
            <div><h3>{t("explanation")}</h3><p>{tr("الثبات مقياس تعليمي لاستقرار الاسترجاع يُحسب من تسميعات المعلم؛ ليس حكمًا شرعيًا على التلاوة.", "Retention is an educational measure of recall stability computed from teacher-verified recitations, not a religious judgment.")}</p><RetentionBar v={d.retention} /></div>
          </aside>
        </div>
      )}
    </>
  );
}

function Answer({ q, a }: { q: string; a: string }) {
  return <div className="surface pad"><span className="eyebrow">{q}</span><p style={{ margin: "8px 0 0", fontSize: 16 }}>{a}</p></div>;
}
