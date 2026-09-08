"use client";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { Avatar, ErrorBox, Loading, Num, PageHead, fmtDate } from "@/components/ui";
import { useCapabilities } from "@/components/Shell";
import { Field, Money, StatusChip, daysLate, todayIso, useToast, type Invoice, type Payment } from "../../_lib";

const METHODS: Payment["method"][] = ["cash", "bank_transfer", "card_manual", "other"];
const PRINT_CSS = `
@media print {
  .spine, .no-print, .toast { display: none !important; }
  .shell { display: block !important; }
  .matn { padding: 0 !important; max-width: none !important; }
  .with-margin { grid-template-columns: 1fr !important; }
  .surface, .tbl, .kpi { box-shadow: none !important; border-color: #999 !important; }
  .fade-up, .stagger > * { animation: none !important; }
  body { background: #fff !important; color: #000 !important; font-size: 13px; }
  a { color: inherit !important; }
}`;

export default function InvoicePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const caps = useCapabilities();
  const [toastNode, toast] = useToast();
  const q = useQuery({ queryKey: ["invoice", id], queryFn: () => api<Invoice>(`/finance/invoices/${id}`) });
  const refresh = () => { qc.invalidateQueries({ queryKey: ["invoice", id] }); qc.invalidateQueries({ queryKey: ["fin-invoices"] }); qc.invalidateQueries({ queryKey: ["fin-summary"] }); };

  const [pay, setPay] = useState({ amount: "", method: "cash" as Payment["method"], reference: "", received_on: todayIso(), note: "" });
  useEffect(() => { if (q.data) setPay((p) => ({ ...p, amount: Number(q.data!.outstanding) > 0 ? q.data!.outstanding : "" })); }, [q.data]);

  const record = useMutation({
    mutationFn: () => api<Payment>("/finance/payments", { method: "POST", json: { invoice: id, ...pay } }),
    onSuccess: (p) => { toast(`${t("payment_saved")} · ${p.receipt_number}`); setPay((x) => ({ ...x, reference: "", note: "" })); refresh(); },
    onError: (e) => toast((e as Error).message),
  });
  const refund = useMutation({
    mutationFn: (v: { p: Payment; reason: string }) => api(`/finance/payments/${v.p.id}/refund`, { method: "POST", json: { reason: v.reason } }),
    onSuccess: () => { toast(t("refunded")); refresh(); },
    onError: (e) => toast((e as Error).message),
  });
  const voidInv = useMutation({
    mutationFn: (reason: string) => api(`/finance/invoices/${id}/void`, { method: "POST", json: { reason } }),
    onSuccess: () => { toast(t("inv_status_void")); refresh(); },
    onError: (e) => toast((e as Error).message),
  });

  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const inv = q.data!;
  const perms = caps.data?.permissions ?? [];
  const paymentsOn = caps.data?.modules["finance.payments"]?.enabled;
  const canRecord = paymentsOn && perms.includes("finance.payments.record");
  const canRefund = paymentsOn && perms.includes("finance.payments.refund");
  const canVoid = perms.includes("finance.invoicing.issue") && inv.status !== "void" && Number(inv.paid_total) === 0 && !inv.payments.some((p) => p.status === "posted");
  const open = inv.status !== "void" && inv.status !== "paid" && Number(inv.outstanding) > 0;
  const late = inv.status === "overdue" ? daysLate(inv.due_on) : 0;

  return (
    <>
      <style>{PRINT_CSS}</style>
      <PageHead eyebrow={`${t("nav_finance")} · ${t("invoice")}`}
        title={<span className="row" style={{ gap: 14 }}><span className="num" dir="ltr">{inv.number}</span><StatusChip status={inv.status} /></span>}
        sub={<span className="row" style={{ gap: 10 }}><Avatar name={inv.student_name} small /><span><b>{inv.student_name}</b> <span className="num muted" dir="ltr">{inv.student_code}</span> · {inv.branch_name}</span></span>}
        actions={<span className="row no-print">
          <button className="btn" onClick={() => window.print()}>{t("print")}</button>
          {canVoid && <button className="btn danger" disabled={voidInv.isPending} onClick={() => { const r = window.prompt(t("void_reason")); if (r && r.trim()) voidInv.mutate(r.trim()); }}>{t("void_invoice")}</button>}
        </span>} />

      <div className="with-margin">
        <div className="stack" style={{ gap: 22 }}>
          <section className="surface pad fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 16 }}>
            <KV k={t("payer")} v={inv.payer_name} />
            <KV k={t("period")} v={<span className="num" dir="ltr">{inv.period_label || "—"}</span>} />
            <KV k={t("issued_on")} v={fmtDate(inv.issued_on, locale)} />
            <KV k={t("due_on")} v={<>{fmtDate(inv.due_on, locale)}{late > 0 && <span className="chip bad" style={{ marginInlineStart: 8 }}><Num v={late} /> {t("days_late")}</span>}</>} />
            {inv.plan_name && <KV k={t("plan")} v={inv.plan_name} />}
            {inv.created_by_name && <KV k={t("recorded_by")} v={inv.created_by_name} />}
          </section>

          <section>
            <div className="section-title"><h2 style={{ fontSize: 17 }}>{t("lines")}</h2><small dir="ltr">{inv.currency}</small></div>
            <div className="tbl">
              <table>
                <thead><tr><th style={{ width: 90 }}>{t("kind_fee")}/{t("kind_discount")}</th><th>{t("description")}</th><th style={{ textAlign: "end" }}>{t("qty")}</th><th style={{ textAlign: "end" }}>{t("unit_price")}</th><th style={{ textAlign: "end" }}>{t("amount")}</th></tr></thead>
                <tbody>
                  {inv.lines.map((l) => {
                    const neg = l.kind === "discount" || l.kind === "scholarship";
                    return (
                      <tr key={l.id}>
                        <td><span className="chip" style={{ ["--dot" as string]: neg ? "var(--s-needs)" : "var(--lapis-3)" }}><i className="dot" />{t(`kind_${l.kind}` as Key)}</span></td>
                        <td>{l.description}</td>
                        <td className="num" style={{ textAlign: "end" }}>{Number(l.quantity)}</td>
                        <td style={{ textAlign: "end" }}><Money v={l.unit_amount} /></td>
                        <td style={{ textAlign: "end", color: neg ? "var(--s-weak)" : undefined }}>{neg ? "−" : ""}<Money v={l.amount} /></td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr><td colSpan={4} className="muted" style={{ textAlign: "end" }}>{t("subtotal")}</td><td style={{ textAlign: "end" }}><Money v={inv.subtotal} /></td></tr>
                  <tr><td colSpan={4} className="muted" style={{ textAlign: "end" }}>{t("discounts")}</td><td style={{ textAlign: "end", color: "var(--s-weak)" }}>−<Money v={inv.discount_total} /></td></tr>
                  <tr><td colSpan={4} style={{ textAlign: "end", fontWeight: 700 }}>{t("total")}</td><td style={{ textAlign: "end", fontSize: 16 }}><Money v={inv.total} currency={inv.currency} strong /></td></tr>
                  <tr><td colSpan={4} className="muted" style={{ textAlign: "end" }}>{t("paid")}</td><td style={{ textAlign: "end", color: "var(--s-strong)" }}><Money v={inv.paid_total} /></td></tr>
                  <tr style={{ background: "var(--surface-2)" }}><td colSpan={4} style={{ textAlign: "end", fontWeight: 700 }}>{t("outstanding")}</td><td style={{ textAlign: "end", fontSize: 17, color: Number(inv.outstanding) > 0 ? "var(--s-weak)" : "var(--s-strong)" }}><Money v={inv.outstanding} currency={inv.currency} strong /></td></tr>
                </tfoot>
              </table>
            </div>
          </section>

          <section>
            <div className="section-title"><h2 style={{ fontSize: 17 }}>{t("payments")}</h2><small><Num v={inv.payments.length} /></small></div>
            {inv.payments.length === 0 ? <p className="muted" style={{ margin: 0 }}>{t("empty")}</p> : (
              <div className="tbl">
                <table>
                  <thead><tr><th>{t("receipt")}</th><th>{t("received_on")}</th><th>{t("method")}</th><th>{t("reference")}</th><th style={{ textAlign: "end" }}>{t("amount")}</th><th>{t("status")}</th>{canRefund && <th className="no-print" />}</tr></thead>
                  <tbody>
                    {inv.payments.map((p) => (
                      <tr key={p.id} style={{ opacity: p.status === "refunded" ? 0.6 : 1 }}>
                        <td className="num" dir="ltr"><b>{p.receipt_number}</b>{p.recorded_by_name && <div className="muted" style={{ fontSize: 11.5, fontFamily: "var(--font-body)" }}>{p.recorded_by_name}</div>}</td>
                        <td>{fmtDate(p.received_on, locale)}</td>
                        <td>{t(`method_${p.method}` as Key)}</td>
                        <td className="num" dir="ltr">{p.reference || "—"}{p.note && <div className="muted" style={{ fontSize: 12, fontFamily: "var(--font-body)" }}>{p.note}</div>}</td>
                        <td style={{ textAlign: "end", textDecoration: p.status === "refunded" ? "line-through" : undefined }}><Money v={p.amount} /></td>
                        <td>{p.status === "refunded" ? <span className="chip warn" title={p.refund_reason}><i className="dot" style={{ background: "var(--s-needs)" }} />{t("refunded")}</span> : <span className="chip"><i className="dot" style={{ background: "var(--s-strong)" }} />{t("paid")}</span>}</td>
                        {canRefund && <td className="no-print" style={{ textAlign: "end" }}>{p.status === "posted" && <button className="btn sm" disabled={refund.isPending} onClick={() => { const r = window.prompt(t("refund_reason")); if (r && r.trim()) refund.mutate({ p, reason: r.trim() }); }}>{t("refund")}</button>}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {inv.notes && <section className="surface pad"><h3 style={{ marginBottom: 6 }}>{t("notes")}</h3><p className="muted" style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 14 }}>{inv.notes}</p></section>}
        </div>

        <aside className="hashiya no-print">
          {open && canRecord ? (
            <form className="stack" style={{ gap: 12 }} onSubmit={(e) => { e.preventDefault(); record.mutate(); }}>
              <h3>{t("record_payment")}</h3>
              <Field label={`${t("amount")} (${inv.currency})`}><input className="input num" dir="ltr" type="number" step="0.001" min="0.001" max={inv.outstanding} required value={pay.amount} onChange={(e) => setPay({ ...pay, amount: e.target.value })} style={{ fontSize: 18, fontWeight: 700 }} /></Field>
              <Field label={t("method")}>
                <select className="input" value={pay.method} onChange={(e) => setPay({ ...pay, method: e.target.value as Payment["method"] })}>
                  {METHODS.map((m) => <option key={m} value={m}>{t(`method_${m}` as Key)}</option>)}
                </select>
              </Field>
              <Field label={t("reference")}><input className="input num" dir="ltr" value={pay.reference} onChange={(e) => setPay({ ...pay, reference: e.target.value })} /></Field>
              <Field label={t("received_on")}><input className="input num" dir="ltr" type="date" required value={pay.received_on} onChange={(e) => setPay({ ...pay, received_on: e.target.value })} /></Field>
              <Field label={t("note")}><input className="input" value={pay.note} onChange={(e) => setPay({ ...pay, note: e.target.value })} /></Field>
              <button type="submit" className="btn gold" disabled={record.isPending || !pay.amount}>{t("record_payment")}</button>
              <p className="muted" style={{ fontSize: 12.5 }}>{t("outstanding")}: <Money v={inv.outstanding} currency={inv.currency} /></p>
            </form>
          ) : (
            <div>
              <h3>{t("status")}</h3>
              <StatusChip status={inv.status} />
              <dl className="kv" style={{ marginTop: 14 }}>
                <dt>{t("total")}</dt><dd><Money v={inv.total} currency={inv.currency} /></dd>
                <dt>{t("paid")}</dt><dd><Money v={inv.paid_total} /></dd>
                <dt>{t("outstanding")}</dt><dd><Money v={inv.outstanding} /></dd>
              </dl>
            </div>
          )}
          <div><Link href="/finance" className="btn sm" style={{ width: "100%" }}>{t("nav_finance")}</Link></div>
        </aside>
      </div>
      {toastNode}
    </>
  );
}

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return <div><div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{k}</div><div style={{ fontSize: 15, marginTop: 2 }}>{v}</div></div>;
}
