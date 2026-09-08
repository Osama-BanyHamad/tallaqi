"use client";
/** Shared finance types + small presentational helpers (money, status chip, modal, toast). Not a route. */
import { useCallback, useEffect, useState } from "react";
import { useI18n, type Key } from "@/lib/i18n";
import { toArabicDigits } from "@/lib/quran";

export type FeePlan = { id: string; name: string; cadence: "monthly" | "term" | "annual" | "one_time"; amount: string; currency: string; description: string;
  is_active: boolean; sibling_discount_pct: string; branch: string | null; branch_name: string; active_students: number };
export type StudentPlan = { id: string; student: string; student_name: string; student_code: string; plan: string; plan_name: string; plan_amount: string; plan_cadence: string;
  currency: string; discount_pct: string; scholarship_pct: string; scholarship_note: string; start_date: string; end_date: string | null; status: "active" | "ended" };
export type InvoiceStatus = "draft" | "issued" | "partially_paid" | "paid" | "overdue" | "void";
export type InvoiceRow = { id: string; number: string; student: string; student_name: string; student_code: string; branch_name: string; payer_name: string; issued_on: string; due_on: string;
  currency: string; subtotal: string; discount_total: string; total: string; paid_total: string; outstanding: string; status: InvoiceStatus; period_label: string; plan_name: string };
export type Line = { id: string; kind: "fee" | "discount" | "scholarship" | "adjustment"; description: string; quantity: string; unit_amount: string; amount: string };
export type Payment = { id: string; invoice: string; invoice_number: string; amount: string; currency: string; method: "cash" | "bank_transfer" | "card_manual" | "other"; reference: string;
  received_on: string; note: string; receipt_number: string; recorded_by_name: string; status: "posted" | "refunded"; refunded_at: string | null; refund_reason: string };
export type Invoice = InvoiceRow & { notes: string; created_by_name: string; lines: Line[]; payments: Payment[] };
export type Summary = { issued_total: string; paid_total: string; outstanding_total: string; overdue_count: number; by_status: Record<InvoiceStatus, number> };
export type Paged<T> = { count: number; results: T[] };

export const CURRENCY_LABEL: Record<string, { ar: string; en: string }> = { JOD: { ar: "د.أ", en: "JOD" }, SAR: { ar: "ر.س", en: "SAR" }, USD: { ar: "$", en: "USD" }, AED: { ar: "د.إ", en: "AED" } };

/** 3-decimal money in tabular mono; Arabic digits in Arabic locale. Currency label optional (omit inside tables that show it in the header). */
export function fmtMoney(v: string | number | null | undefined, locale: "ar" | "en", currency?: string, compact = false) {
  if (v == null || v === "") return "—";
  const n = Number(v);
  const digits = compact ? 0 : 3;
  const s = n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  const body = locale === "ar" ? toArabicDigits(s).replace(/,/g, "٬").replace(/\./g, "٫") : s;
  const cur = currency ? ` ${CURRENCY_LABEL[currency]?.[locale] ?? currency}` : "";
  return body + cur;
}
/** `compact` drops the fils for KPI tiles so large totals fit on one line. */
export function Money({ v, currency, strong, compact }: { v: string | number | null | undefined; currency?: string; strong?: boolean; compact?: boolean }) {
  const { locale } = useI18n();
  return <span className="num" dir="ltr" style={{ fontWeight: strong ? 700 : undefined, unicodeBidi: "isolate", fontSize: compact ? "0.8em" : undefined }}>{fmtMoney(v, locale, currency, compact)}</span>;
}

export const STATUS_DOT: Record<InvoiceStatus, string> = { draft: "var(--ink-3)", issued: "var(--lapis-3)", partially_paid: "var(--s-needs)", paid: "var(--s-strong)", overdue: "var(--s-weak)", void: "var(--rule-2)" };
export function StatusChip({ status }: { status: InvoiceStatus }) {
  const { t } = useI18n();
  const cls = status === "overdue" ? "chip bad" : status === "partially_paid" ? "chip warn" : "chip";
  return <span className={cls} style={{ ["--dot" as string]: STATUS_DOT[status], opacity: status === "void" ? 0.6 : 1 }}><i className="dot" />{t(`inv_status_${status}` as Key)}</span>;
}

export function currentPeriod() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}
export function todayIso() { return new Date().toISOString().slice(0, 10); }
export function daysLate(dueIso: string) { return Math.max(0, Math.floor((Date.now() - new Date(dueIso).getTime()) / 86_400_000)); }

/** Minimal toast: returns the node to render + a show() that auto-hides. Mirrors the `.toast` pattern used by other pages. */
export function useToast(): [React.ReactNode, (msg: string) => void] {
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => { if (!msg) return; const id = setTimeout(() => setMsg(null), 1800); return () => clearTimeout(id); }, [msg]);
  const show = useCallback((m: string) => setMsg(m), []);
  return [msg ? <div className="toast" role="status">{msg}</div> : null, show];
}

/** Centered modal on a dimmed ground. Styled inline so it stays self-contained to the finance pages. */
export function Modal({ title, onClose, children, width }: { title: string; onClose: () => void; children: React.ReactNode; width?: number }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(13,18,48,.45)", backdropFilter: "blur(2px)", zIndex: 25, display: "grid", placeItems: "center", padding: 20 }}>
      <div role="dialog" aria-modal aria-label={title} onClick={(e) => e.stopPropagation()} className="surface fade-up" style={{ width: "min(100%, " + (width ?? 520) + "px)", padding: "22px 24px 24px", borderTop: "3px solid var(--gold)", boxShadow: "var(--shadow-lg)" }}>
        <h2 style={{ fontSize: 19, marginBottom: 16 }}>{title}</h2>
        {children}
      </div>
    </div>
  );
}

export function Field({ label, children, span }: { label: string; children: React.ReactNode; span?: boolean }) {
  return <label className="stack" style={{ gap: 5, gridColumn: span ? "1 / -1" : undefined }}><span className="muted" style={{ fontSize: 12.5, fontWeight: 600 }}>{label}</span>{children}</label>;
}
