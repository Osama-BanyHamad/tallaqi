"use client";
import Link from "next/link";
import { use, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { Avatar, ErrorBox, JuzStrip, Kpi, Loading, Num, RetentionBar, fmtDate } from "@/components/ui";
import { StudentForm, type StudentInput } from "@/components/StudentForm";
import { Field, Modal, grid2 } from "@/components/forms";
import { useCapabilities } from "@/components/Shell";

type Student = { id: string; person: { first_name: string; last_name: string; display_name_ar: string; date_of_birth: string | null; gender: string; phone: string; email: string }; branch: string; branch_name: string; student_code: string; level: string; status: string; is_minor: boolean; notes: string;
  halaqah: { id: string; name: string } | null; journey_summary: { id: string; memorized_pages: number; memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; juz_map: [number, number | null, string][]; status: string } | null; created_at: string };
type Guardian = { id: string; name: string; phone: string; email: string; relationship: string; primary: boolean };
type Att = { since: string; counts: Record<string, number>; records: { date: string; status: string; halaqah: string; reason: string }[] };
const ATT_COLOR: Record<string, string> = { present: "var(--s-strong)", late: "var(--s-needs)", absent: "var(--s-weak)", excused: "var(--gold)", left_early: "var(--s-recent)" };

export default function StudentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const tr = useT2();
  const qc = useQueryClient();
  const caps = useCapabilities();
  const [editing, setEditing] = useState(false);
  const [addingGuardian, setAddingGuardian] = useState(false);
  const [g, setG] = useState({ display_name_ar: "", phone: "", relationship: "parent" });
  const s = useQuery({ queryKey: ["student", id], queryFn: () => api<Student>(`/students/${id}`) });
  const guardians = useQuery({ queryKey: ["guardians", id], queryFn: () => api<Guardian[]>(`/students/${id}/guardians`) });
  const att = useQuery({ queryKey: ["att", id], queryFn: () => api<Att>(`/students/${id}/attendance?days=60`) });
  const addGuardian = useMutation({ mutationFn: () => api(`/students/${id}/guardians`, { method: "POST", json: g }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["guardians", id] }); setAddingGuardian(false); } });
  if (s.isLoading) return <Loading />;
  if (s.error) return <ErrorBox e={s.error} />;
  const d = s.data!;
  const j = d.journey_summary;
  const can = (p: string) => caps.data?.permissions.includes(p);
  const initial: StudentInput = { id: d.id, person: { first_name: d.person.first_name, last_name: d.person.last_name, date_of_birth: d.person.date_of_birth, gender: d.person.gender, phone: d.person.phone, email: d.person.email }, branch: d.branch, student_code: d.student_code, level: d.level, status: d.status, is_minor: d.is_minor, notes: d.notes, halaqah_id: d.halaqah?.id ?? "" };
  const STATUS: Record<string, string> = { active: tr("نشط", "Active"), paused: tr("متوقف", "Paused"), applicant: tr("متقدم", "Applicant"), left: tr("منسحب", "Left"), alumni: tr("خريج", "Alumni") };
  return (
    <>
      <div className="page-head fade-up" style={{ alignItems: "center" }}>
        <div className="row" style={{ gap: 20 }}>
          <Avatar name={d.person.display_name_ar} />
          <div>
            <span className="eyebrow">{t("nav_students")} · {STATUS[d.status] ?? d.status}</span>
            <h1 style={{ marginTop: 6 }}>{d.person.display_name_ar}</h1>
            <p style={{ marginTop: 4 }}><span className="num" dir="ltr">{d.student_code}</span> · {d.branch_name} · {d.halaqah?.name ?? tr("بدون حلقة", "No Halaqah")}{d.level ? ` · ${d.level}` : ""}</p>
          </div>
        </div>
        <div className="row">
          {can("people.students.write") && <button className="btn" onClick={() => setEditing(true)}>{tr("تعديل", "Edit")}</button>}
          {j && <Link className="btn primary" href={`/journeys/${j.id}`}>{t("journey")} →</Link>}
        </div>
      </div>
      {editing && <StudentForm initial={initial} onClose={() => setEditing(false)} onSaved={() => { setEditing(false); qc.invalidateQueries({ queryKey: ["student", id] }); }} />}
      {j && (
        <div className="surface pad fade-up" style={{ marginBottom: 26 }}>
          <JuzStrip map={j.juz_map} large />
          <div className="kpis" style={{ marginBottom: 0, marginTop: 14, gap: 10 }}>
            <Kpi label={t("memorized_pages")} value={<Num v={j.memorized_pages} />} />
            <Kpi label={t("memorized")} value={<Num v={j.memorized_ayat} />} unit={t("ayat")} />
            <Kpi label={t("avg_retention")} value={<RetentionBar v={j.avg_retention} />} />
            <Kpi label={`${t("state_weak")} / ${t("state_critical")}`} tone={j.critical_ayat ? "attention" : undefined} value={<><Num v={j.weak_ayat} /> / <Num v={j.critical_ayat} /></>} />
          </div>
        </div>
      )}
      <div className="with-margin">
        <div className="stack" style={{ gap: 28 }}>
          <section>
            <div className="section-title"><h2>{t("attendance")}</h2><small>{tr("آخر ٦٠ يومًا", "last 60 days")}</small></div>
            {att.data ? (
              <div className="surface pad">
                <div className="row" style={{ gap: 8, marginBottom: 12 }}>
                  {Object.entries(att.data.counts).map(([k, v]) => <span key={k} className="chip"><i className="dot" style={{ background: ATT_COLOR[k] }} />{t(k as "present")}: <b className="num">{v}</b></span>)}
                  {Object.keys(att.data.counts).length === 0 && <span className="muted">{t("empty")}</span>}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {att.data.records.slice().reverse().map((r) => <span key={r.date} title={`${r.date} · ${t(r.status as "present")}`} style={{ width: 16, height: 16, borderRadius: 3, background: ATT_COLOR[r.status] ?? "var(--s-none)" }} />)}
                </div>
              </div>
            ) : <Loading />}
          </section>
          <section>
            <div className="section-title"><h2>{tr("بيانات الطالب", "Details")}</h2></div>
            <div className="surface pad" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14, fontSize: 14 }}>
              <div><div className="muted" style={{ fontSize: 12 }}>{tr("تاريخ الميلاد", "Date of birth")}</div>{fmtDate(d.person.date_of_birth, locale)}</div>
              <div><div className="muted" style={{ fontSize: 12 }}>{tr("الجنس", "Gender")}</div>{d.person.gender === "female" ? tr("أنثى", "Female") : tr("ذكر", "Male")}</div>
              <div><div className="muted" style={{ fontSize: 12 }}>{tr("قاصر", "Minor")}</div>{d.is_minor ? tr("نعم", "Yes") : tr("لا", "No")}</div>
              <div><div className="muted" style={{ fontSize: 12 }}>{tr("تاريخ التسجيل", "Enrolled")}</div>{fmtDate(d.created_at, locale)}</div>
              {d.notes && <div style={{ gridColumn: "1 / -1" }}><div className="muted" style={{ fontSize: 12 }}>{tr("ملاحظات", "Notes")}</div>{d.notes}</div>}
            </div>
          </section>
        </div>
        <aside className="hashiya">
          <div>
            <div className="row" style={{ justifyContent: "space-between" }}><h3>{tr("أولياء الأمور", "Guardians")}</h3>{can("people.guardians.link") && <button className="btn sm" onClick={() => setAddingGuardian(true)}>+</button>}</div>
            <div className="stack" style={{ gap: 10 }}>
              {(guardians.data ?? []).map((x) => (
                <div key={x.id} className="row" style={{ gap: 10 }}>
                  <Avatar name={x.name} small />
                  <div style={{ fontSize: 13.5 }}><b>{x.name}</b>{x.primary && <span className="chip" style={{ marginInlineStart: 6 }}>{tr("أساسي", "Primary")}</span>}<br /><span className="muted num" dir="ltr">{x.phone || "—"}</span></div>
                </div>
              ))}
              {guardians.data?.length === 0 && <p className="muted">{t("empty")}</p>}
            </div>
          </div>
        </aside>
      </div>
      {addingGuardian && (
        <Modal title={tr("إضافة ولي أمر", "Add guardian")} onClose={() => setAddingGuardian(false)} width={480}>
          <form className="stack" onSubmit={(e) => { e.preventDefault(); addGuardian.mutate(); }}>
            <div style={grid2}>
              <Field label={tr("الاسم", "Name")} span={2}><input className="input" value={g.display_name_ar} onChange={(e) => setG({ ...g, display_name_ar: e.target.value })} required /></Field>
              <Field label={tr("الهاتف", "Phone")}><input className="input" dir="ltr" value={g.phone} onChange={(e) => setG({ ...g, phone: e.target.value })} /></Field>
              <Field label={tr("القرابة", "Relationship")}><input className="input" value={g.relationship} onChange={(e) => setG({ ...g, relationship: e.target.value })} /></Field>
            </div>
            {addGuardian.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(addGuardian.error as Error).message}</p>}
            <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn primary" disabled={addGuardian.isPending}>{tr("حفظ", "Save")}</button></div>
          </form>
        </Modal>
      )}
    </>
  );
}
