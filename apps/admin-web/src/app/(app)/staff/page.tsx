"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { Avatar, ErrorBox, Loading, PageHead } from "@/components/ui";
import { Field, Modal, Select, grid2 } from "@/components/forms";
import { useCapabilities } from "@/components/Shell";

type S = { id: string; person: { first_name: string; last_name: string; display_name_ar: string; display_name_en: string; phone: string; email: string; gender: string }; branch: string | null; staff_type: string; riwayat: string[]; halaqat: { id: string; name: string; role: string }[]; is_active: boolean; account_email: string | null };
type H = { id: string; name: string };
const TYPE: Record<string, [string, string]> = { teacher: ["معلم", "Teacher"], assistant: ["معلم مساعد", "Assistant"], supervisor: ["مشرف", "Supervisor"], admin: ["إداري", "Admin"], finance: ["مالية", "Finance"], hr: ["موارد بشرية", "HR"], instructor: ["مدرب", "Instructor"], support: ["دعم", "Support"] };
const ROLE_FOR_TYPE: Record<string, string> = { teacher: "teacher", assistant: "assistant_teacher", supervisor: "quran_supervisor", admin: "center_admin", finance: "finance", support: "support" };

export default function StaffPage() {
  const { t, locale } = useI18n();
  const tr = useT2();
  const qc = useQueryClient();
  const caps = useCapabilities();
  const [editing, setEditing] = useState<Partial<S> | null>(null);
  const [inviting, setInviting] = useState<S | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["staff"], queryFn: () => api<{ results: S[] }>("/staff?page_size=100") });
  const halaqat = useQuery({ queryKey: ["halaqat-all"], queryFn: () => api<{ results: H[] }>("/halaqat?page_size=200") });
  const branches = useQuery({ queryKey: ["branches"], queryFn: () => api<{ results: H[] }>("/branches?page_size=100") });
  const can = (p: string) => caps.data?.permissions.includes(p);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={t("nav_staff")} title={t("nav_staff")} actions={can("people.staff.write") && <button className="btn primary" onClick={() => setEditing({ person: { first_name: "", last_name: "", display_name_ar: "", display_name_en: "", phone: "", email: "", gender: "male" }, staff_type: "teacher", riwayat: ["hafs_asim"], halaqat: [], is_active: true, branch: null, account_email: null })}>+ {tr("معلم / موظف جديد", "New staff member")}</button>} />
      <div className="list stagger">
        {q.data!.results.map((s) => {
          const name = locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar;
          return (
            <div key={s.id} className="person-row" style={{ gridTemplateColumns: "44px 1.2fr 1fr auto auto" }}>
              <Avatar name={name} />
              <div><div className="name">{name}</div><div className="meta">{s.halaqat.map((h) => h.name).join("، ") || "—"}{s.account_email ? ` · ${s.account_email}` : ""}</div></div>
              <div className="muted" style={{ fontSize: 13 }}>{s.riwayat.length ? "حفص عن عاصم" : "—"}{s.person.phone ? ` · ${s.person.phone}` : ""}</div>
              <span className="chip">{locale === "en" ? TYPE[s.staff_type]?.[1] : TYPE[s.staff_type]?.[0]}</span>
              <div className="row" style={{ gap: 6 }}>
                {can("people.staff.write") && <button className="btn sm" onClick={() => setEditing(s)}>{tr("تعديل", "Edit")}</button>}
                {can("platform.rbac.assign") && !s.account_email && <button className="btn sm" onClick={() => setInviting(s)}>{tr("إنشاء حساب", "Create login")}</button>}
              </div>
            </div>);
        })}
      </div>
      {editing && <StaffForm initial={editing} halaqat={halaqat.data?.results ?? []} branches={branches.data?.results ?? []} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); qc.invalidateQueries({ queryKey: ["staff"] }); }} />}
      {inviting && <InviteForm staff={inviting} onClose={() => setInviting(null)} onDone={(msg) => { setInviting(null); setToast(msg); qc.invalidateQueries({ queryKey: ["staff"] }); setTimeout(() => setToast(null), 12000); }} />}
      {toast && <div className="toast" role="status" style={{ maxWidth: 560 }}>{toast}</div>}
    </>
  );
}

function StaffForm({ initial, halaqat, branches, onClose, onSaved }: { initial: Partial<S>; halaqat: H[]; branches: H[]; onClose: () => void; onSaved: () => void }) {
  const tr = useT2();
  const [f, setF] = useState<Partial<S>>(initial);
  const [ids, setIds] = useState<string[]>((initial.halaqat ?? []).map((h) => h.id));
  const save = useMutation({
    mutationFn: () => {
      const body = { person: f.person, branch: f.branch || null, staff_type: f.staff_type, riwayat: f.riwayat ?? ["hafs_asim"], is_active: f.is_active ?? true, halaqah_ids: ids };
      return f.id ? api(`/staff/${f.id}`, { method: "PATCH", json: body }) : api("/staff", { method: "POST", json: body });
    },
    onSuccess: onSaved,
  });
  const p = f.person!;
  const setP = (k: keyof S["person"], v: string) => setF({ ...f, person: { ...p, [k]: v } });
  return (
    <Modal title={f.id ? tr("تعديل", "Edit") : tr("معلم / موظف جديد", "New staff member")} onClose={onClose}>
      <form className="stack" style={{ gap: 18 }} onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
        <div style={grid2}>
          <Field label={tr("الاسم الأول", "First name")}><input className="input" value={p.first_name} onChange={(e) => setP("first_name", e.target.value)} required /></Field>
          <Field label={tr("اسم العائلة", "Family name")}><input className="input" value={p.last_name} onChange={(e) => setP("last_name", e.target.value)} /></Field>
          <Field label={tr("الهاتف", "Phone")}><input className="input" dir="ltr" value={p.phone} onChange={(e) => setP("phone", e.target.value)} /></Field>
          <Field label={tr("البريد", "Email")}><input className="input" dir="ltr" type="email" value={p.email} onChange={(e) => setP("email", e.target.value)} /></Field>
          <Field label={tr("النوع", "Type")}><Select value={f.staff_type ?? "teacher"} onChange={(v) => setF({ ...f, staff_type: v })} options={Object.entries(TYPE).map(([k, v]) => ({ value: k, label: tr(v[0], v[1]) }))} /></Field>
          <Field label={tr("الفرع", "Branch")}><Select value={f.branch ?? ""} onChange={(v) => setF({ ...f, branch: v })} placeholder={tr("كل الفروع", "All branches")} options={branches.map((b) => ({ value: b.id, label: b.name }))} /></Field>
        </div>
        <Field label={tr("الحلقات", "Halaqat")}>
          <div className="row" style={{ gap: 6 }}>
            {halaqat.map((h) => <button type="button" key={h.id} className={`chip ${ids.includes(h.id) ? "warn" : ""}`} onClick={() => setIds(ids.includes(h.id) ? ids.filter((x) => x !== h.id) : [...ids, h.id])}>{h.name}</button>)}
          </div>
        </Field>
        {save.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(save.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button type="button" className="btn" onClick={onClose}>{tr("إلغاء", "Cancel")}</button><button className="btn primary" disabled={save.isPending}>{tr("حفظ", "Save")}</button></div>
      </form>
    </Modal>
  );
}

function InviteForm({ staff, onClose, onDone }: { staff: S; onClose: () => void; onDone: (msg: string) => void }) {
  const tr = useT2();
  const [email, setEmail] = useState(staff.person.email || "");
  const [role, setRole] = useState(ROLE_FOR_TYPE[staff.staff_type] ?? "teacher");
  const scopeType = role === "teacher" || role === "assistant_teacher" ? "halaqah" : role === "quran_supervisor" && staff.branch ? "branch" : "tenant";
  const refs = scopeType === "halaqah" ? staff.halaqat.map((h) => h.id) : scopeType === "branch" ? [staff.branch] : [];
  const inv = useMutation({
    mutationFn: () => api<{ email: string; generated_password: string | null }>("/accounts", { method: "POST", json: { email, full_name: staff.person.display_name_ar, person_id: staff.person ? undefined : undefined, role_key: role, scope_type: scopeType, scope_refs: refs } }),
    onSuccess: (r) => onDone(r.generated_password ? tr(`تم إنشاء الحساب ${r.email} — كلمة المرور المؤقتة: ${r.generated_password}`, `Account ${r.email} created — temporary password: ${r.generated_password}`) : tr(`تمت إضافة الدور للحساب ${r.email}`, `Role added to ${r.email}`)),
  });
  return (
    <Modal title={tr("إنشاء حساب دخول", "Create login")} onClose={onClose} width={480}>
      <form className="stack" onSubmit={(e) => { e.preventDefault(); inv.mutate(); }}>
        <Field label={tr("البريد الإلكتروني", "Email")}><input className="input" dir="ltr" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></Field>
        <Field label={tr("الدور", "Role")}><Select value={role} onChange={setRole} options={[["teacher", "معلم", "Teacher"], ["assistant_teacher", "معلم مساعد", "Assistant"], ["quran_supervisor", "مشرف القرآن", "Quran supervisor"], ["center_admin", "مدير المركز", "Center admin"], ["finance", "مالية", "Finance"], ["support", "دعم", "Support"]].map(([v, a, e]) => ({ value: v, label: tr(a, e) }))} /></Field>
        <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{tr(`النطاق: ${scopeType === "halaqah" ? "حلقاته فقط" : scopeType === "branch" ? "فرعه" : "المؤسسة كاملة"}`, `Scope: ${scopeType}`)}</p>
        {inv.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(inv.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn primary" disabled={inv.isPending}>{tr("إنشاء", "Create")}</button></div>
      </form>
    </Modal>
  );
}
