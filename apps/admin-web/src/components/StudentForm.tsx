"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { Field, Modal, Select, grid2 } from "@/components/forms";

type Branch = { id: string; name: string };
type Halaqah = { id: string; name: string; branch: string };
export type StudentInput = {
  id?: string; person: { first_name: string; last_name: string; display_name_ar?: string; date_of_birth?: string | null; gender?: string; phone?: string; email?: string };
  branch: string; student_code?: string; level?: string; status?: string; is_minor?: boolean; notes?: string; halaqah_id?: string | null;
  guardian?: { display_name_ar: string; phone?: string; relationship?: string };
};

export function StudentForm({ initial, onClose, onSaved }: { initial?: StudentInput; onClose: () => void; onSaved: (s: { id: string }) => void }) {
  const tr = useT2();
  const qc = useQueryClient();
  const [f, setF] = useState<StudentInput>(initial ?? { person: { first_name: "", last_name: "", gender: "male", date_of_birth: "" }, branch: "", level: "", status: "active", is_minor: true, halaqah_id: "", guardian: { display_name_ar: "", phone: "", relationship: "parent" } });
  const branches = useQuery({ queryKey: ["branches"], queryFn: () => api<{ results: Branch[] }>("/branches?page_size=100") });
  const halaqat = useQuery({ queryKey: ["halaqat-all"], queryFn: () => api<{ results: Halaqah[] }>("/halaqat?page_size=200") });
  const save = useMutation({
    mutationFn: () => {
      const body: StudentInput = { ...f, person: { ...f.person, date_of_birth: f.person.date_of_birth || null }, halaqah_id: f.halaqah_id || null };
      if (!body.guardian?.display_name_ar) delete body.guardian;
      return f.id ? api<{ id: string }>(`/students/${f.id}`, { method: "PATCH", json: body }) : api<{ id: string }>("/students", { method: "POST", json: body });
    },
    onSuccess: (s) => { qc.invalidateQueries({ queryKey: ["students"] }); qc.invalidateQueries({ queryKey: ["student", s.id] }); onSaved(s); },
  });
  const p = f.person;
  const setP = (k: keyof StudentInput["person"], v: string) => setF({ ...f, person: { ...p, [k]: v } });
  return (
    <Modal title={f.id ? tr("تعديل بيانات الطالب", "Edit student") : tr("طالب جديد", "New student")} onClose={onClose}>
      <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }} className="stack" style={{ gap: 18 }}>
        <div style={grid2}>
          <Field label={tr("الاسم الأول", "First name")}><input className="input" value={p.first_name} onChange={(e) => setP("first_name", e.target.value)} required /></Field>
          <Field label={tr("اسم العائلة", "Family name")}><input className="input" value={p.last_name} onChange={(e) => setP("last_name", e.target.value)} /></Field>
          <Field label={tr("تاريخ الميلاد", "Date of birth")}><input className="input" type="date" value={p.date_of_birth ?? ""} onChange={(e) => setP("date_of_birth", e.target.value)} /></Field>
          <Field label={tr("الجنس", "Gender")}><Select value={p.gender ?? ""} onChange={(v) => setP("gender", v)} options={[{ value: "male", label: tr("ذكر", "Male") }, { value: "female", label: tr("أنثى", "Female") }]} /></Field>
          <Field label={tr("الفرع", "Branch")}><Select value={f.branch} onChange={(v) => setF({ ...f, branch: v })} placeholder={tr("اختر الفرع", "Choose branch")} options={(branches.data?.results ?? []).map((b) => ({ value: b.id, label: b.name }))} /></Field>
          <Field label={tr("الحلقة", "Halaqah")}><Select value={f.halaqah_id ?? ""} onChange={(v) => setF({ ...f, halaqah_id: v })} placeholder={tr("بدون حلقة", "No Halaqah")} options={(halaqat.data?.results ?? []).filter((h) => !f.branch || h.branch === f.branch).map((h) => ({ value: h.id, label: h.name }))} /></Field>
          <Field label={tr("رقم الطالب", "Student code")} hint={tr("يُولَّد تلقائيًا إن تُرك فارغًا", "Generated if empty")}><input className="input" dir="ltr" value={f.student_code ?? ""} onChange={(e) => setF({ ...f, student_code: e.target.value })} /></Field>
          <Field label={tr("المستوى", "Level")}><input className="input" value={f.level ?? ""} onChange={(e) => setF({ ...f, level: e.target.value })} /></Field>
          <Field label={tr("الحالة", "Status")}><Select value={f.status ?? "active"} onChange={(v) => setF({ ...f, status: v })} options={[{ value: "active", label: tr("نشط", "Active") }, { value: "paused", label: tr("متوقف", "Paused") }, { value: "applicant", label: tr("متقدم", "Applicant") }, { value: "left", label: tr("منسحب", "Left") }, { value: "alumni", label: tr("خريج", "Alumni") }]} /></Field>
          <Field label={tr("قاصر", "Minor")}><Select value={f.is_minor ? "1" : "0"} onChange={(v) => setF({ ...f, is_minor: v === "1" })} options={[{ value: "1", label: tr("نعم", "Yes") }, { value: "0", label: tr("لا", "No") }]} /></Field>
        </div>
        {!f.id && (
          <div className="surface pad" style={{ background: "var(--surface-2)" }}>
            <h3 style={{ marginBottom: 10 }}>{tr("ولي الأمر (اختياري)", "Guardian (optional)")}</h3>
            <div style={grid2}>
              <Field label={tr("الاسم", "Name")}><input className="input" value={f.guardian?.display_name_ar ?? ""} onChange={(e) => setF({ ...f, guardian: { ...f.guardian!, display_name_ar: e.target.value } })} /></Field>
              <Field label={tr("الهاتف", "Phone")}><input className="input" dir="ltr" value={f.guardian?.phone ?? ""} onChange={(e) => setF({ ...f, guardian: { ...f.guardian!, phone: e.target.value } })} /></Field>
            </div>
          </div>
        )}
        <Field label={tr("ملاحظات", "Notes")}><textarea className="input" rows={2} value={f.notes ?? ""} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
        {save.error && <p role="alert" style={{ color: "var(--s-weak)", margin: 0 }}>{(save.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button type="button" className="btn" onClick={onClose}>{tr("إلغاء", "Cancel")}</button>
          <button className="btn primary" disabled={save.isPending || !f.branch}>{tr("حفظ", "Save")}</button>
        </div>
      </form>
    </Modal>
  );
}
