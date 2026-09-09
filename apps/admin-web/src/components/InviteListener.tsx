"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { Field, Modal } from "@/components/forms";
import { useCapabilities } from "@/components/Shell";

type Account = { membership_id: string; email: string; full_name: string; assignments: { id: string; role: string }[] };

/** For the independent learner: invite a parent, friend, or remote teacher who listens and records Tasmee' from their phone. */
export function InviteListener() {
  const tr = useT2();
  const qc = useQueryClient();
  const caps = useCapabilities();
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ full_name: "", email: "" });
  const [result, setResult] = useState<{ email: string; generated_password: string | null } | null>(null);
  const isSolo = caps.data?.roles.includes("solo_learner");
  const list = useQuery({ queryKey: ["accounts"], queryFn: () => api<Account[]>("/accounts"), enabled: !!isSolo });
  const m = useMutation({
    mutationFn: () => api<{ email: string; generated_password: string | null }>("/accounts", { method: "POST", json: { ...f, role_key: "listener", scope_type: "tenant", scope_refs: [] } }),
    onSuccess: (r) => { setResult(r); qc.invalidateQueries({ queryKey: ["accounts"] }); },
  });
  if (!isSolo) return null;
  const listeners = (list.data ?? []).filter((a) => a.assignments.some((x) => x.role === "listener"));
  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between" }}><h3>{tr("من يسمّع لك", "Your listeners")}</h3><button className="btn sm" onClick={() => { setResult(null); setOpen(true); }}>+ {tr("دعوة", "Invite")}</button></div>
      {listeners.length === 0 ? <p style={{ fontSize: 13 }}>{tr("ادعُ والدك أو صديقك أو معلمًا عن بُعد: يسجّل الدخول من هاتفه، يفتح رحلتك، ويسمّع لك بالنقر على الكلمات. التسميع الذكي يساعد، لكن الإنسان هو من يعتمد.", "Invite a parent, a friend, or a remote teacher: they sign in from their phone, open your journey, and listen while tapping mistakes. The AI check helps, but a person confirms.")}</p>
        : <div className="stack" style={{ gap: 6 }}>{listeners.map((a) => <div key={a.membership_id} style={{ fontSize: 13.5 }}><b>{a.full_name}</b> <span className="muted" dir="ltr">{a.email}</span></div>)}</div>}
      {open && (
        <Modal title={tr("دعوة مُسمِّع", "Invite a listener")} onClose={() => setOpen(false)} width={460}>
          {result ? (
            <div className="stack">
              <p style={{ margin: 0 }}>{tr("أُنشئ الحساب. أرسل هذه البيانات لمن دعوته:", "The account is ready. Send these details to the person you invited:")}</p>
              <pre dir="ltr" style={{ margin: 0, padding: 12, background: "var(--surface-2)", borderRadius: 8, fontFamily: "var(--font-mono)", fontSize: 13 }}>{`https://tallaqi.com/login\n${result.email}\n${result.generated_password ?? "(existing password)"}`}</pre>
              <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{tr("سيجد رحلتك في تبويب «طلابي» في التطبيق أو صفحة الطلاب على الويب.", "They will find your journey under My students in the app or Students on the web.")}</p>
              <button className="btn primary" onClick={() => setOpen(false)}>{tr("تم", "Done")}</button>
            </div>
          ) : (
            <form className="stack" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
              <Field label={tr("الاسم", "Name")}><input className="input" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} required /></Field>
              <Field label={tr("البريد الإلكتروني", "Email")}><input className="input" dir="ltr" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required /></Field>
              {m.error && <p style={{ margin: 0, color: "var(--s-weak)", fontSize: 13 }}>{(m.error as Error).message}</p>}
              <button className="btn primary" disabled={m.isPending}>{tr("أرسل الدعوة", "Create the invitation")}</button>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
}
