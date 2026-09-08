"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { Field, Modal, Select, grid2 } from "@/components/forms";

type H = { id?: string; name: string; branch: string; kind: string; gender_policy: string; capacity: number; policy_key: string; schedule_summary: string; teachers?: { id: string; name: string }[]; teacher_id?: string | null };

export function HalaqahForm({ initial, onClose, onSaved }: { initial: H; onClose: () => void; onSaved: (h: { id: string }) => void }) {
  const tr = useT2();
  const [f, setF] = useState<H>({ ...initial, teacher_id: initial.teachers?.[0]?.id ?? "" });
  const branches = useQuery({ queryKey: ["branches"], queryFn: () => api<{ results: { id: string; name: string }[] }>("/branches?page_size=100") });
  const staff = useQuery({ queryKey: ["staff"], queryFn: () => api<{ results: { id: string; person: { display_name_ar: string }; staff_type: string }[] }>("/staff?page_size=200") });
  const policies = useQuery({ queryKey: ["policies"], queryFn: () => api<{ key: string; name_ar: string; name_en: string }[]>("/policies") });
  const save = useMutation({
    mutationFn: () => { const body = { ...f, teacher_id: f.teacher_id || null }; delete body.teachers; return f.id ? api<{ id: string }>(`/halaqat/${f.id}`, { method: "PATCH", json: body }) : api<{ id: string }>("/halaqat", { method: "POST", json: body }); },
    onSuccess: onSaved,
  });
  return (
    <Modal title={f.id ? tr("إعدادات الحلقة", "Halaqah settings") : tr("حلقة جديدة", "New Halaqah")} onClose={onClose}>
      <form className="stack" style={{ gap: 18 }} onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
        <div style={grid2}>
          <Field label={tr("الاسم", "Name")} span={2}><input className="input" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required /></Field>
          <Field label={tr("الفرع", "Branch")}><Select value={f.branch} onChange={(v) => setF({ ...f, branch: v })} placeholder={tr("اختر", "Choose")} options={(branches.data?.results ?? []).map((b) => ({ value: b.id, label: b.name }))} /></Field>
          <Field label={tr("المعلم", "Teacher")}><Select value={f.teacher_id ?? ""} onChange={(v) => setF({ ...f, teacher_id: v })} placeholder={tr("بدون", "None")} options={(staff.data?.results ?? []).filter((s) => ["teacher", "assistant", "supervisor"].includes(s.staff_type)).map((s) => ({ value: s.id, label: s.person.display_name_ar }))} /></Field>
          <Field label={tr("النوع", "Kind")}><Select value={f.kind} onChange={(v) => setF({ ...f, kind: v })} options={[{ value: "in_person", label: tr("حضوري", "In person") }, { value: "online", label: tr("عن بُعد", "Online") }, { value: "hybrid", label: tr("مدمج", "Hybrid") }]} /></Field>
          <Field label={tr("الفئة", "Gender")}><Select value={f.gender_policy} onChange={(v) => setF({ ...f, gender_policy: v })} options={[{ value: "male", label: tr("ذكور", "Male") }, { value: "female", label: tr("إناث", "Female") }, { value: "mixed", label: tr("مختلط (أطفال)", "Mixed (children)") }]} /></Field>
          <Field label={tr("السعة", "Capacity")}><input className="input" type="number" min={1} value={f.capacity} onChange={(e) => setF({ ...f, capacity: Number(e.target.value) })} /></Field>
          <Field label={tr("منهجية الحفظ", "Learning policy")}><Select value={f.policy_key} onChange={(v) => setF({ ...f, policy_key: v })} options={(policies.data ?? []).map((p) => ({ value: p.key, label: tr(p.name_ar, p.name_en || p.key) }))} /></Field>
          <Field label={tr("المواعيد", "Schedule")} span={2}><input className="input" value={f.schedule_summary} onChange={(e) => setF({ ...f, schedule_summary: e.target.value })} placeholder={tr("السبت–الخميس 6:00–7:30", "Sat–Thu 6:00–7:30")} /></Field>
        </div>
        {save.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(save.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button type="button" className="btn" onClick={onClose}>{tr("إلغاء", "Cancel")}</button><button className="btn primary" disabled={save.isPending || !f.branch}>{tr("حفظ", "Save")}</button></div>
      </form>
    </Modal>
  );
}

export function EnrollDialog({ halaqahId, onClose, onDone }: { halaqahId: string; onClose: () => void; onDone: () => void }) {
  const tr = useT2();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const q = useQuery({ queryKey: ["students", search], queryFn: () => api<{ results: { id: string; person: { display_name_ar: string }; student_code: string; halaqah: { name: string } | null }[] }>(`/students?search=${encodeURIComponent(search)}&page_size=20`), enabled: search.length > 1 });
  const enroll = useMutation({ mutationFn: (student_id: string) => api(`/halaqat/${halaqahId}/enroll`, { method: "POST", json: { student_id } }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["today", halaqahId] }); onDone(); } });
  return (
    <Modal title={tr("إضافة طالب إلى الحلقة", "Enroll a student")} onClose={onClose} width={520}>
      <input className="input" autoFocus placeholder={tr("ابحث بالاسم أو الرقم", "Search by name or code")} value={search} onChange={(e) => setSearch(e.target.value)} />
      <div className="stack" style={{ gap: 6, marginTop: 12 }}>
        {(q.data?.results ?? []).map((s) => (
          <div key={s.id} className="row" style={{ justifyContent: "space-between", padding: "8px 10px", border: "1px solid var(--rule)", borderRadius: 8 }}>
            <span>{s.person.display_name_ar} <span className="muted num" dir="ltr">{s.student_code}</span>{s.halaqah && <span className="muted"> · {s.halaqah.name}</span>}</span>
            <button className="btn sm primary" disabled={enroll.isPending} onClick={() => enroll.mutate(s.id)}>{s.halaqah ? tr("نقل", "Move") : tr("إضافة", "Add")}</button>
          </div>
        ))}
        {search.length > 1 && q.data?.results.length === 0 && <p className="muted">{tr("لا نتائج", "No results")}</p>}
      </div>
    </Modal>
  );
}
