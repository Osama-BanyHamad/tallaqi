"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, getLocale, getSession } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { ErrorBox, JuzStrip, Loading, Num, PageHead, Pct, RetentionBar } from "@/components/ui";

type Att = { from: string; to: string; halaqat: { halaqah: string; students: number; present: number; total: number; rate: number | null }[]; students: { name: string; halaqah: string; present: number; late: number; absent: number; excused: number; total: number; rate: number | null }[] };
type Hifz = { students: { journey_id: string; name: string; code: string; branch: string; memorized_pages: number; memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; sessions: number; passed: number; new_ayat: number; revision_ayat: number }[] };
type Stu = { students: { id: string; name: string; code: string; branch: string; halaqah: string; status: string; level: string; guardian: string; phone: string }[] };

async function downloadCsv(path: string, name: string) {
  const s = getSession();
  const r = await fetch(`/api/v1${path}${path.includes("?") ? "&" : "?"}export=csv`, { headers: { Authorization: `Bearer ${s?.access}`, "X-Tenant": s?.tenant ?? "", "Accept-Language": getLocale() } });
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = `${name}.csv`; a.click(); URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { t } = useI18n();
  const tr = useT2();
  const [tab, setTab] = useState<"attendance" | "hifz" | "students">("hifz");
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  const [from, setFrom] = useState(monthAgo);
  const [to, setTo] = useState(today);
  const range = `from=${from}&to=${to}`;
  const att = useQuery({ queryKey: ["rep-att", range], queryFn: () => api<Att>(`/reports/attendance?${range}`), enabled: tab === "attendance" });
  const hifz = useQuery({ queryKey: ["rep-hifz", range], queryFn: () => api<Hifz>(`/reports/hifz?${range}`), enabled: tab === "hifz" });
  const stu = useQuery({ queryKey: ["rep-stu"], queryFn: () => api<Stu>("/reports/students"), enabled: tab === "students" });
  const tabs = [["hifz", tr("الحفظ والثبات", "Hifz & retention")], ["attendance", tr("الحضور", "Attendance")], ["students", tr("الطلاب", "Students")]] as const;
  return (
    <>
      <PageHead eyebrow={tr("التقارير", "Reports")} title={tr("التقارير", "Reports")} sub={tr("أكاديمية وإدارية، بفلترة حسب المدة وتصدير CSV.", "Academic and administrative, filtered by period, exportable as CSV.")}
        actions={<><input className="input" type="date" style={{ width: 160 }} value={from} onChange={(e) => setFrom(e.target.value)} /><input className="input" type="date" style={{ width: 160 }} value={to} onChange={(e) => setTo(e.target.value)} />
          <button className="btn gold" onClick={() => downloadCsv(tab === "students" ? "/reports/students" : `/reports/${tab}?${range}`, `${tab}_${from}_${to}`)}>CSV ↓</button></>} />
      <div className="seg-btns" style={{ marginBottom: 22 }}>{tabs.map(([k, l]) => <button key={k} role="radio" aria-checked={tab === k} onClick={() => setTab(k)}>{l}</button>)}</div>
      {tab === "attendance" && (att.isLoading ? <Loading /> : att.error ? <ErrorBox e={att.error} /> : (
        <div className="stack" style={{ gap: 24 }}>
          <div className="kpis">{att.data!.halaqat.map((h) => <div key={h.halaqah} className="kpi"><div className="l">{h.halaqah}</div><div className="v"><Pct v={h.rate} /></div><div className="sub"><Num v={h.students} /> {t("students")} · <Num v={h.total} /> {tr("سجل", "records")}</div></div>)}</div>
          <div className="tbl"><table><thead><tr><th>{t("students")}</th><th>{t("halaqah")}</th><th>{t("present")}</th><th>{t("late")}</th><th>{t("absent")}</th><th>{t("excused")}</th><th>{tr("النسبة", "Rate")}</th></tr></thead>
            <tbody>{att.data!.students.map((s) => <tr key={s.name + s.halaqah}><td style={{ fontWeight: 600 }}>{s.name}</td><td>{s.halaqah}</td><td className="num">{s.present}</td><td className="num">{s.late}</td><td className="num" style={{ color: s.absent > 2 ? "var(--s-weak)" : undefined }}>{s.absent}</td><td className="num">{s.excused}</td><td><RetentionBar v={s.rate} /></td></tr>)}</tbody></table></div>
        </div>))}
      {tab === "hifz" && (hifz.isLoading ? <Loading /> : hifz.error ? <ErrorBox e={hifz.error} /> : (
        <div className="tbl"><table><thead><tr><th>{t("students")}</th><th>{tr("الأجزاء", "Juz")}</th><th>{t("memorized_pages")}</th><th>{t("retention")}</th><th>{t("state_critical")}</th><th>{t("sessions")}</th><th>{tr("آيات جديدة", "New ayat")}</th><th>{tr("آيات مراجعة", "Revision ayat")}</th></tr></thead>
          <tbody>{hifz.data!.students.map((s) => <tr key={s.journey_id} className="row-link" onClick={() => (window.location.href = `/journeys/${s.journey_id}`)}><td style={{ fontWeight: 600 }}>{s.name}<div className="muted" style={{ fontSize: 12 }}>{s.branch}</div></td><td style={{ minWidth: 160 }}><JuzStripLazy id={s.journey_id} /></td><td className="num"><Num v={s.memorized_pages} /></td><td><RetentionBar v={s.avg_retention} /></td><td className="num" style={{ color: s.critical_ayat ? "var(--s-critical)" : undefined }}><Num v={s.critical_ayat} /></td><td className="num"><Num v={s.passed} /> / <Num v={s.sessions} /></td><td className="num"><Num v={s.new_ayat} /></td><td className="num"><Num v={s.revision_ayat} /></td></tr>)}</tbody></table></div>))}
      {tab === "students" && (stu.isLoading ? <Loading /> : stu.error ? <ErrorBox e={stu.error} /> : (
        <div className="tbl"><table><thead><tr><th>{t("students")}</th><th>{t("code")}</th><th>{t("branch")}</th><th>{t("halaqah")}</th><th>{t("status")}</th><th>{tr("ولي الأمر", "Guardian")}</th><th>{tr("الهاتف", "Phone")}</th></tr></thead>
          <tbody>{stu.data!.students.map((s) => <tr key={s.id} className="row-link" onClick={() => (window.location.href = `/students/${s.id}`)}><td style={{ fontWeight: 600 }}>{s.name}</td><td className="num" dir="ltr">{s.code}</td><td>{s.branch}</td><td>{s.halaqah || "—"}</td><td><span className="chip">{s.status}</span></td><td>{s.guardian || "—"}</td><td className="num" dir="ltr">{s.phone || "—"}</td></tr>)}</tbody></table></div>))}
    </>
  );
}

function JuzStripLazy({ id }: { id: string }) {
  const q = useQuery({ queryKey: ["journey-strip", id], queryFn: () => api<{ juz_map: [number, number | null, string][] }>(`/journeys/${id}`), staleTime: 60_000 });
  return <JuzStrip map={q.data?.juz_map} />;
}
