"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { Avatar, ErrorBox, Loading, Num, PageHead, fmtDate } from "@/components/ui";
import { useCapabilities } from "@/components/Shell";
import { Field, Modal, Money, currentPeriod, todayIso, useToast, type FeePlan, type Paged, type StudentPlan } from "../_lib";

type Branch = { id: string; name: string };
type StudentHit = { id: string; person: { display_name_ar: string; display_name_en: string }; student_code: string; branch_name: string };
type PlanForm = { name: string; cadence: FeePlan["cadence"]; amount: string; sibling_discount_pct: string; branch: string; is_active: boolean; description: string };
const CADENCES: FeePlan["cadence"][] = ["monthly", "term", "annual", "one_time"];
const emptyPlan: PlanForm = { name: "", cadence: "monthly", amount: "", sibling_discount_pct: "0", branch: "", is_active: true, description: "" };

export default function FeePlansPage() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const router = useRouter();
  const caps = useCapabilities();
  const canWrite = caps.data?.permissions.includes("finance.fees.write");
  const canIssue = caps.data?.permissions.includes("finance.invoicing.issue") && caps.data?.modules["finance.invoicing"]?.enabled;
  const [toastNode, toast] = useToast();
  const [editing, setEditing] = useState<(PlanForm & { id?: string }) | null>(null);

  const plans = useQuery({ queryKey: ["fee-plans"], queryFn: () => api<Paged<FeePlan>>("/finance/fee-plans?page_size=100") });
  const branches = useQuery({ queryKey: ["branches"], queryFn: () => api<Paged<Branch>>("/tenant/branches?page_size=100") });
  const assignments = useQuery({ queryKey: ["student-plans"], queryFn: () => api<Paged<StudentPlan>>("/finance/student-plans?status=active&page_size=200") });
  const invalidate = () => { qc.invalidateQueries({ queryKey: ["fee-plans"] }); qc.invalidateQueries({ queryKey: ["student-plans"] }); };

  const savePlan = useMutation({
    mutationFn: (f: PlanForm & { id?: string }) => {
      const json = { name: f.name, cadence: f.cadence, amount: f.amount, sibling_discount_pct: f.sibling_discount_pct || "0", branch: f.branch || null, is_active: f.is_active, description: f.description };
      return f.id ? api(`/finance/fee-plans/${f.id}`, { method: "PATCH", json }) : api("/finance/fee-plans", { method: "POST", json });
    },
    onSuccess: () => { setEditing(null); invalidate(); toast(t("saved")); },
    onError: (e) => toast((e as Error).message),
  });
  const endAssignment = useMutation({
    mutationFn: (sp: StudentPlan) => api(`/finance/student-plans/${sp.id}`, { method: "PATCH", json: { status: "ended", end_date: todayIso() } }),
    onSuccess: () => { invalidate(); toast(t("done")); },
    onError: (e) => toast((e as Error).message),
  });
  const issue = useMutation({
    mutationFn: (v: { sp: StudentPlan; period: string }) => api<{ id: string; number: string }>(`/finance/student-plans/${v.sp.id}/invoice`, { method: "POST", json: { period_label: v.period } }),
    onSuccess: (inv) => { qc.invalidateQueries({ queryKey: ["fin-invoices"] }); toast(`${t("invoice")} ${inv.number}`); router.push(`/finance/invoices/${inv.id}`); },
    onError: (e) => toast((e as Error).message),
  });

  function onIssue(sp: StudentPlan) {
    const period = window.prompt(t("fin_generate_prompt"), currentPeriod());
    if (period && period.trim()) issue.mutate({ sp, period: period.trim() });
  }
  const bn = (p: FeePlan) => p.branch_name || t("all_branches");

  return (
    <>
      <PageHead eyebrow={t("nav_finance")} title={t("fin_plans")} sub={t("fin_plans_sub")}
        actions={<>
          <Link href="/finance" className="btn">{t("invoices")}</Link>
          {canWrite && <button className="btn primary" onClick={() => setEditing({ ...emptyPlan })}>{t("fin_new_plan")}</button>}
        </>} />

      {plans.isLoading ? <Loading /> : plans.error ? <ErrorBox e={plans.error} /> : (
        <div className="tbl fade-up" style={{ marginBottom: 34 }}>
          <table>
            <thead><tr><th>{t("plan_name")}</th><th>{t("cadence")}</th><th>{t("amount")}</th><th>{t("sibling_discount")}</th><th>{t("branch")}</th><th>{t("students_count")}</th><th>{t("status")}</th>{canWrite && <th />}</tr></thead>
            <tbody>
              {plans.data!.results.length === 0 && <tr><td colSpan={8} className="muted" style={{ textAlign: "center", padding: 28 }}>{t("empty")}</td></tr>}
              {plans.data!.results.map((p) => (
                <tr key={p.id} style={{ opacity: p.is_active ? 1 : 0.6 }}>
                  <td><b>{p.name}</b>{p.description && <div className="muted" style={{ fontSize: 12.5 }}>{p.description}</div>}</td>
                  <td>{t(`cadence_${p.cadence}` as Key)}</td>
                  <td><Money v={p.amount} currency={p.currency} strong /></td>
                  <td className="num">{Number(p.sibling_discount_pct) > 0 ? `${Number(p.sibling_discount_pct)}%` : "—"}</td>
                  <td>{bn(p)}</td>
                  <td><Num v={p.active_students} /></td>
                  <td><span className="chip" style={{ ["--dot" as string]: p.is_active ? "var(--s-strong)" : "var(--ink-3)" }}><i className="dot" />{p.is_active ? t("active") : t("inactive")}</span></td>
                  {canWrite && <td style={{ textAlign: "end" }}><button className="btn sm" onClick={() => setEditing({ id: p.id, name: p.name, cadence: p.cadence, amount: p.amount, sibling_discount_pct: p.sibling_discount_pct, branch: p.branch ?? "", is_active: p.is_active, description: p.description })}>{t("edit")}</button></td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="with-margin">
        <section>
          <div className="section-title"><h2 style={{ fontSize: 18 }}>{t("fin_assignments")} {assignments.data && <span className="num muted" style={{ fontSize: 14, fontWeight: 500 }}>· <Num v={assignments.data.count} /></span>}</h2></div>
          {assignments.isLoading ? <Loading /> : assignments.error ? <ErrorBox e={assignments.error} /> : assignments.data!.results.length === 0 ? <p className="muted">{t("empty")}</p> : (
            <div className="list stagger">
              {assignments.data!.results.map((sp) => (
                <article key={sp.id} className="person-row" style={{ gridTemplateColumns: "44px minmax(150px, 1.2fr) minmax(140px, 1fr) auto auto" }}>
                  <Avatar name={sp.student_name} />
                  <div><div className="name">{sp.student_name}</div><div className="meta"><span className="num" dir="ltr">{sp.student_code}</span> · {sp.plan_name} · {t(`cadence_${sp.plan_cadence}` as Key)}</div></div>
                  <div>
                    <div style={{ fontSize: 14 }}><Money v={sp.plan_amount} currency={sp.currency} strong /></div>
                    <div className="meta">
                      {Number(sp.discount_pct) > 0 && <>{t("discount_pct")} {Number(sp.discount_pct)} · </>}
                      {Number(sp.scholarship_pct) > 0 && <>{t("scholarship_pct")} {Number(sp.scholarship_pct)}{sp.scholarship_note ? ` (${sp.scholarship_note})` : ""} · </>}
                      {t("start_date")}: {fmtDate(sp.start_date, locale)}
                    </div>
                  </div>
                  <div className="row" style={{ gap: 6 }}>
                    {canIssue && <button className="btn sm primary" onClick={() => onIssue(sp)} disabled={issue.isPending}>{t("issue_invoice")}</button>}
                    {canWrite && <button className="btn sm" onClick={() => { if (window.confirm(t("confirm_end"))) endAssignment.mutate(sp); }}>{t("end_assignment")}</button>}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
        {canWrite && <AssignPanel plans={plans.data?.results.filter((p) => p.is_active) ?? []} onDone={() => { invalidate(); toast(t("assigned")); }} onError={(m) => toast(m)} />}
      </div>

      {editing && (
        <Modal title={editing.id ? t("fin_edit_plan") : t("fin_new_plan")} onClose={() => setEditing(null)}>
          <form onSubmit={(e) => { e.preventDefault(); savePlan.mutate(editing); }} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <Field label={t("plan_name")} span><input className="input" required value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
            <Field label={t("cadence")}>
              <select className="input" value={editing.cadence} onChange={(e) => setEditing({ ...editing, cadence: e.target.value as FeePlan["cadence"] })}>
                {CADENCES.map((c) => <option key={c} value={c}>{t(`cadence_${c}` as Key)}</option>)}
              </select>
            </Field>
            <Field label={t("amount")}><input className="input num" dir="ltr" type="number" step="0.001" min="0" required value={editing.amount} onChange={(e) => setEditing({ ...editing, amount: e.target.value })} /></Field>
            <Field label={t("sibling_discount")}><input className="input num" dir="ltr" type="number" step="0.5" min="0" max="100" value={editing.sibling_discount_pct} onChange={(e) => setEditing({ ...editing, sibling_discount_pct: e.target.value })} /></Field>
            <Field label={t("branch")}>
              <select className="input" value={editing.branch} onChange={(e) => setEditing({ ...editing, branch: e.target.value })}>
                <option value="">{t("all_branches")}</option>
                {branches.data?.results.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </Field>
            <Field label={t("description")} span><textarea className="input" rows={2} value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
            <label className="row" style={{ gap: 8, gridColumn: "1 / -1" }}><input type="checkbox" checked={editing.is_active} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> {t("active")}</label>
            <div className="row" style={{ gridColumn: "1 / -1", justifyContent: "flex-end", marginTop: 6 }}>
              <button type="button" className="btn" onClick={() => setEditing(null)}>{t("cancel")}</button>
              <button type="submit" className="btn primary" disabled={savePlan.isPending}>{t("save")}</button>
            </div>
          </form>
        </Modal>
      )}
      {toastNode}
    </>
  );
}

function AssignPanel({ plans, onDone, onError }: { plans: FeePlan[]; onDone: () => void; onError: (m: string) => void }) {
  const { t, locale } = useI18n();
  const [search, setSearch] = useState("");
  const [student, setStudent] = useState<StudentHit | null>(null);
  const [form, setForm] = useState({ plan: "", discount_pct: "0", scholarship_pct: "0", scholarship_note: "", start_date: todayIso() });
  const hits = useQuery({ queryKey: ["students", search], queryFn: () => api<Paged<StudentHit>>(`/students?search=${encodeURIComponent(search)}&page_size=8`), enabled: search.trim().length > 0 && !student });
  const assign = useMutation({
    mutationFn: () => api("/finance/student-plans", { method: "POST", json: { student: student!.id, plan: form.plan || plans[0]?.id, discount_pct: form.discount_pct || "0", scholarship_pct: form.scholarship_pct || "0", scholarship_note: form.scholarship_note, start_date: form.start_date } }),
    onSuccess: () => { setStudent(null); setSearch(""); setForm((f) => ({ ...f, discount_pct: "0", scholarship_pct: "0", scholarship_note: "" })); onDone(); },
    onError: (e) => onError((e as Error).message),
  });
  const name = (s: StudentHit) => (locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar);
  return (
    <aside className="hashiya">
      <div>
        <h3>{t("fin_assign_title")}</h3>
        {student ? (
          <div className="row" style={{ gap: 10, padding: "10px 12px", border: "1px solid var(--rule)", borderRadius: 8, background: "var(--surface)" }}>
            <Avatar name={name(student)} small />
            <div className="grow"><b style={{ fontSize: 14 }}>{name(student)}</b><div className="muted num" style={{ fontSize: 12 }} dir="ltr">{student.student_code}</div></div>
            <button type="button" className="btn sm" onClick={() => setStudent(null)}>×</button>
          </div>
        ) : (
          <>
            <input className="input" placeholder={t("fin_pick_student")} value={search} onChange={(e) => setSearch(e.target.value)} />
            {hits.data && hits.data.results.length > 0 && (
              <div className="stack" style={{ gap: 4, marginTop: 8 }}>
                {hits.data.results.map((s) => (
                  <button key={s.id} type="button" onClick={() => setStudent(s)} className="row" style={{ gap: 10, textAlign: "start", border: "1px solid var(--rule)", background: "var(--surface)", borderRadius: 8, padding: "8px 10px", cursor: "pointer" }}>
                    <Avatar name={name(s)} small /><span style={{ fontSize: 13.5 }}>{name(s)}<span className="muted num" style={{ fontSize: 11.5, marginInlineStart: 6 }} dir="ltr">{s.student_code}</span></span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
      <form className="stack" style={{ gap: 12 }} onSubmit={(e) => { e.preventDefault(); if (student) assign.mutate(); }}>
        <Field label={t("plan")}>
          <select className="input" value={form.plan || plans[0]?.id || ""} onChange={(e) => setForm({ ...form, plan: e.target.value })}>
            {plans.map((p) => <option key={p.id} value={p.id}>{p.name} — {Number(p.amount)} {p.currency}</option>)}
          </select>
        </Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <Field label={t("discount_pct")}><input className="input num" dir="ltr" type="number" min="0" max="100" step="0.5" value={form.discount_pct} onChange={(e) => setForm({ ...form, discount_pct: e.target.value })} /></Field>
          <Field label={t("scholarship_pct")}><input className="input num" dir="ltr" type="number" min="0" max="100" step="0.5" value={form.scholarship_pct} onChange={(e) => setForm({ ...form, scholarship_pct: e.target.value })} /></Field>
        </div>
        <Field label={t("scholarship_note")}><input className="input" value={form.scholarship_note} onChange={(e) => setForm({ ...form, scholarship_note: e.target.value })} /></Field>
        <Field label={t("start_date")}><input className="input num" dir="ltr" type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></Field>
        <button type="submit" className="btn gold" disabled={!student || plans.length === 0 || assign.isPending}>{t("assign")}</button>
      </form>
    </aside>
  );
}
