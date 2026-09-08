"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { Avatar, ErrorBox, Loading, PageHead, fmtDate } from "@/components/ui";
import { Field, Modal, Select, grid2 } from "@/components/forms";

type A = { membership_id: string; email: string; full_name: string; status: string; is_active: boolean; person_name: string | null; last_login: string | null; assignments: { id: string; role: string; role_name: string; scope_type: string; scope_refs: string[] }[] };
type Role = { id: string; key: string; name_ar: string; name_en: string; permissions: string[] };
const SCOPE: Record<string, [string, string]> = { tenant: ["المؤسسة كاملة", "Whole organization"], branch: ["فرع", "Branch"], halaqah: ["حلقات محددة", "Specific Halaqat"], student_set: ["طلاب محددون", "Specific students"], self: ["نفسه", "Self"] };

export default function AccountsPage() {
  const { locale } = useI18n();
  const tr = useT2();
  const qc = useQueryClient();
  const [inviting, setInviting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["accounts"], queryFn: () => api<A[]>("/accounts") });
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => api<{ results: Role[] }>("/roles?page_size=50") });
  const revoke = useMutation({ mutationFn: (id: string) => api(`/accounts/${id}/revoke`, { method: "POST", json: {} }), onSuccess: () => qc.invalidateQueries({ queryKey: ["accounts"] }) });
  const reset = useMutation({ mutationFn: (id: string) => api<{ email: string; generated_password: string }>(`/accounts/${id}/reset-password`, { method: "POST", json: {} }), onSuccess: (r) => { setToast(tr(`كلمة مرور مؤقتة لـ ${r.email}: ${r.generated_password}`, `Temporary password for ${r.email}: ${r.generated_password}`)); setTimeout(() => setToast(null), 15000); } });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={tr("الإعدادات", "Settings")} title={tr("الحسابات والأدوار", "Accounts & roles")} sub={tr("كل صلاحية تُفرض في الخادم حسب الدور ونطاقه.", "Every permission is enforced by the backend by role and scope.")}
        actions={<button className="btn primary" onClick={() => setInviting(true)}>+ {tr("دعوة مستخدم", "Invite user")}</button>} />
      <div className="list stagger">
        {q.data!.map((a) => (
          <div key={a.membership_id} className="person-row" style={{ gridTemplateColumns: "44px 1.1fr 1.4fr auto" }}>
            <Avatar name={a.full_name || a.email} />
            <div><div className="name">{a.full_name}</div><div className="meta" dir="ltr" style={{ textAlign: "start" }}>{a.email}</div>{a.last_login && <div className="meta">{tr("آخر دخول", "Last login")}: {fmtDate(a.last_login, locale)}</div>}</div>
            <div className="row" style={{ gap: 6 }}>
              {a.assignments.map((r) => <span key={r.id} className="chip" title={r.scope_refs.join(", ")}><i className="dot" style={{ background: "var(--lapis)" }} />{locale === "en" ? r.role : r.role_name} · {locale === "en" ? SCOPE[r.scope_type]?.[1] : SCOPE[r.scope_type]?.[0]}<button className="btn sm" style={{ height: 20, padding: "0 6px", marginInlineStart: 4 }} onClick={() => confirm(tr("إلغاء هذا الدور؟", "Revoke this role?")) && revoke.mutate(r.id)}>×</button></span>)}
              {a.assignments.length === 0 && <span className="muted">{tr("بلا دور", "No role")}</span>}
            </div>
            <button className="btn sm" onClick={() => reset.mutate(a.membership_id)}>{tr("إعادة تعيين كلمة المرور", "Reset password")}</button>
          </div>
        ))}
      </div>
      {inviting && <Invite roles={roles.data?.results ?? []} onClose={() => setInviting(false)} onDone={(m) => { setInviting(false); setToast(m); qc.invalidateQueries({ queryKey: ["accounts"] }); setTimeout(() => setToast(null), 15000); }} />}
      {toast && <div className="toast" role="status" style={{ maxWidth: 600 }}>{toast}</div>}
    </>
  );
}

function Invite({ roles, onClose, onDone }: { roles: Role[]; onClose: () => void; onDone: (m: string) => void }) {
  const tr = useT2();
  const [f, setF] = useState({ email: "", full_name: "", password: "", role_key: "teacher", scope_type: "tenant", scope_refs: [] as string[] });
  const branches = useQuery({ queryKey: ["branches"], queryFn: () => api<{ results: { id: string; name: string }[] }>("/branches?page_size=100") });
  const halaqat = useQuery({ queryKey: ["halaqat-all"], queryFn: () => api<{ results: { id: string; name: string }[] }>("/halaqat?page_size=200") });
  const inv = useMutation({ mutationFn: () => api<{ email: string; generated_password: string | null }>("/accounts", { method: "POST", json: f }), onSuccess: (r) => onDone(r.generated_password ? tr(`تم إنشاء ${r.email} — كلمة المرور المؤقتة: ${r.generated_password}`, `${r.email} created — temporary password: ${r.generated_password}`) : tr(`تمت إضافة الدور إلى ${r.email}`, `Role added to ${r.email}`)) });
  const opts = f.scope_type === "branch" ? branches.data?.results ?? [] : f.scope_type === "halaqah" ? halaqat.data?.results ?? [] : [];
  return (
    <Modal title={tr("دعوة مستخدم", "Invite user")} onClose={onClose} width={560}>
      <form className="stack" style={{ gap: 16 }} onSubmit={(e) => { e.preventDefault(); inv.mutate(); }}>
        <div style={grid2}>
          <Field label={tr("الاسم الكامل", "Full name")}><input className="input" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} required /></Field>
          <Field label={tr("البريد الإلكتروني", "Email")}><input className="input" dir="ltr" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required /></Field>
          <Field label={tr("كلمة المرور", "Password")} hint={tr("تُولَّد إن تُركت فارغة", "Generated if empty")}><input className="input" dir="ltr" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
          <Field label={tr("الدور", "Role")}><Select value={f.role_key} onChange={(v) => setF({ ...f, role_key: v })} options={roles.map((r) => ({ value: r.key, label: tr(r.name_ar, r.name_en || r.key) }))} /></Field>
          <Field label={tr("النطاق", "Scope")}><Select value={f.scope_type} onChange={(v) => setF({ ...f, scope_type: v, scope_refs: [] })} options={Object.entries(SCOPE).map(([k, v]) => ({ value: k, label: tr(v[0], v[1]) }))} /></Field>
        </div>
        {opts.length > 0 && (
          <Field label={tr("اختر", "Choose")}>
            <div className="row" style={{ gap: 6 }}>{opts.map((o) => <button type="button" key={o.id} className={`chip ${f.scope_refs.includes(o.id) ? "warn" : ""}`} onClick={() => setF({ ...f, scope_refs: f.scope_refs.includes(o.id) ? f.scope_refs.filter((x) => x !== o.id) : [...f.scope_refs, o.id] })}>{o.name}</button>)}</div>
          </Field>
        )}
        {inv.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(inv.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button type="button" className="btn" onClick={onClose}>{tr("إلغاء", "Cancel")}</button><button className="btn primary" disabled={inv.isPending}>{tr("دعوة", "Invite")}</button></div>
      </form>
    </Modal>
  );
}
