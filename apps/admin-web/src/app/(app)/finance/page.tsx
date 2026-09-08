"use client";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { Avatar, ErrorBox, Kpi, Loading, Num, PageHead, fmtDate } from "@/components/ui";
import { useCapabilities } from "@/components/Shell";
import { Money, StatusChip, currentPeriod, daysLate, useToast, type InvoiceRow, type InvoiceStatus, type Paged, type Summary } from "./_lib";

const FILTERS = ["open", "overdue", "partially_paid", "issued", "paid"] as const;
type Filter = (typeof FILTERS)[number];

export default function FinanceOverview() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const caps = useCapabilities();
  const [toastNode, toast] = useToast();
  const [filter, setFilter] = useState<Filter>("open");
  const [search, setSearch] = useState("");

  const summary = useQuery({ queryKey: ["fin-summary"], queryFn: () => api<Summary>("/finance/invoices/summary") });
  const listPath = filter === "open" ? "/finance/invoices?open=1&ordering=due_on" : `/finance/invoices?status=${filter}&ordering=-issued_on`;
  const invoices = useQuery({ queryKey: ["fin-invoices", filter, search], queryFn: () => api<Paged<InvoiceRow>>(`${listPath}&search=${encodeURIComponent(search)}&page_size=100`) });

  const generate = useMutation({
    mutationFn: (period: string) => api<{ created: number }>("/finance/invoices/generate", { method: "POST", json: { period_label: period } }),
    onSuccess: (r) => { toast(`${t("fin_generated")}: ${r.created}`); qc.invalidateQueries({ queryKey: ["fin-invoices"] }); qc.invalidateQueries({ queryKey: ["fin-summary"] }); },
    onError: (e) => toast((e as Error).message),
  });
  const canIssue = caps.data?.permissions.includes("finance.invoicing.issue");
  const currency = invoices.data?.results[0]?.currency ?? "JOD";
  const s = summary.data;

  function onGenerate() {
    const period = window.prompt(t("fin_generate_prompt"), currentPeriod());
    if (period && /^\d{4}-\d{2}$/.test(period.trim())) generate.mutate(period.trim());
  }

  return (
    <>
      <PageHead eyebrow={t("nav_finance")} title={t("fin_title")} sub={t("fin_sub")}
        actions={<>
          <Link href="/finance/plans" className="btn">{t("fin_plans")}</Link>
          {canIssue && <button className="btn primary" onClick={onGenerate} disabled={generate.isPending}>{t("fin_generate_month")}</button>}
        </>} />

      {summary.error ? <ErrorBox e={summary.error} /> : (
        <div className="kpis stagger">
          <Kpi accent label={t("fin_issued")} value={<Money v={s?.issued_total} compact />} unit={currency} sub={s ? <><Num v={(s.by_status.issued ?? 0) + (s.by_status.partially_paid ?? 0) + (s.by_status.paid ?? 0) + (s.by_status.overdue ?? 0)} /> {t("invoices")}</> : "…"} />
          <Kpi label={t("fin_paid")} value={<Money v={s?.paid_total} compact />} unit={currency} tone="ok" sub={s ? <><Num v={s.by_status.paid ?? 0} /> {t("inv_status_paid")}</> : "…"} />
          <Kpi label={t("fin_outstanding")} value={<Money v={s?.outstanding_total} compact />} unit={currency} tone={s && Number(s.outstanding_total) > 0 ? "behind" : undefined} sub={s ? <><Num v={s.by_status.partially_paid ?? 0} /> {t("inv_status_partially_paid")}</> : "…"} />
          <Kpi label={t("fin_overdue")} value={<Num v={s?.overdue_count} />} tone={s && s.overdue_count > 0 ? "attention" : "ok"} sub={t("due")} />
        </div>
      )}

      <div className="section-title">
        <h2 style={{ fontSize: 18 }}>{t("fin_open_invoices")} {invoices.data && <span className="num muted" style={{ fontSize: 14, fontWeight: 500 }}>· <Num v={invoices.data.count} /></span>}</h2>
        <div className="row" style={{ gap: 10 }}>
          <input className="input" style={{ width: 240, height: 36 }} placeholder={t("search")} value={search} onChange={(e) => setSearch(e.target.value)} />
          <div className="seg-btns" role="radiogroup" aria-label={t("status")}>
            {FILTERS.map((f) => <button key={f} role="radio" aria-checked={filter === f} onClick={() => setFilter(f)}>{f === "open" ? t("filter_all_open") : t(`inv_status_${f}` as Key)}</button>)}
          </div>
        </div>
      </div>

      {invoices.isLoading ? <Loading /> : invoices.error ? <ErrorBox e={invoices.error} /> : invoices.data!.results.length === 0 ? (
        <div className="surface pad" style={{ textAlign: "center", padding: "40px 20px" }}>
          <p className="muted" style={{ margin: 0 }}>{filter === "open" ? t("fin_no_open") : t("empty")}</p>
        </div>
      ) : (
        <div className="list stagger">
          {invoices.data!.results.map((inv) => {
            const late = (inv.status as InvoiceStatus) === "overdue" ? daysLate(inv.due_on) : 0;
            return (
              <Link key={inv.id} href={`/finance/invoices/${inv.id}`} className="person-row" style={{ gridTemplateColumns: "44px minmax(160px, 1.3fr) minmax(140px, 1fr) minmax(120px, 1fr) auto" }}>
                <Avatar name={inv.student_name} />
                <div>
                  <div className="name">{inv.student_name}</div>
                  <div className="meta"><span className="num" dir="ltr">{inv.number}</span> · {inv.period_label || inv.plan_name || "—"} · {inv.payer_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: 13.5 }}>{t("due_on")}: <b>{fmtDate(inv.due_on, locale)}</b></div>
                  <div className="meta">{late > 0 ? <span style={{ color: "var(--s-weak)", fontWeight: 600 }}><Num v={late} /> {t("days_late")}</span> : `${t("issued_on")}: ${fmtDate(inv.issued_on, locale)}`}</div>
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700 }}><Money v={inv.outstanding} currency={inv.currency} /></div>
                  <div className="meta">{t("total")} <Money v={inv.total} /> · {t("paid")} <Money v={inv.paid_total} /></div>
                </div>
                <div className="tail"><StatusChip status={inv.status} /></div>
              </Link>
            );
          })}
        </div>
      )}
      {toastNode}
    </>
  );
}
