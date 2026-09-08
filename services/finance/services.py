"""Finance business rules. Views call these; nothing here recomputes an issued invoice's lines.

Totals are derived only from lines (subtotal/discounts) and posted payments (paid_total)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from services.audit.models import AuditLog
from services.common.exceptions import DomainError
from services.people.models import GuardianLink

from .models import FeePlan, Invoice, InvoiceLine, NumberSequence, Payment, StudentFeePlan

ZERO = Decimal("0")
Q3 = Decimal("0.001")
DEFAULT_TERMS_DAYS = 14


def q3(v: Decimal) -> Decimal:
    return Decimal(v).quantize(Q3, rounding=ROUND_HALF_UP)


def _user(request):
    u = getattr(request, "user", None) if request is not None else None
    return u if u is not None and getattr(u, "is_authenticated", False) else None


# ---- period helpers ------------------------------------------------------------------------
def period_bounds(period_label: str) -> tuple[date, date]:
    """'YYYY-MM' → (first day, last day). Raises DomainError for anything else."""
    try:
        y, m = period_label.split("-")
        first = date(int(y), int(m), 1)
    except (ValueError, AttributeError):
        raise DomainError("period_label must be YYYY-MM.") from None
    nxt = date(first.year + (first.month == 12), 1 if first.month == 12 else first.month + 1, 1)
    return first, nxt - timedelta(days=1)


def plan_active_on(sp: StudentFeePlan, first: date, last: date) -> bool:
    return sp.status == "active" and sp.start_date <= last and (sp.end_date is None or sp.end_date >= first)


# ---- invoice construction ------------------------------------------------------------------
def payer_name_for(student) -> str:
    links = list(GuardianLink.objects.filter(student=student, active=True).select_related("guardian__person").order_by("-primary"))
    if links:
        return links[0].guardian.person.display_name_ar
    return student.person.display_name_ar


def sibling_count(student, on: date) -> int:
    """Distinct students (including this one) sharing an active guardian and holding an active plan on `on`."""
    guardian_ids = list(GuardianLink.objects.filter(student=student, active=True).values_list("guardian_id", flat=True))
    if not guardian_ids:
        return 1
    student_ids = set(GuardianLink.objects.filter(guardian_id__in=guardian_ids, active=True).values_list("student_id", flat=True))
    student_ids.add(student.id)
    with_plans = StudentFeePlan.objects.filter(student_id__in=student_ids, status="active", start_date__lte=on)
    with_plans = with_plans.filter(end_date__isnull=True) | with_plans.filter(end_date__gte=on)
    return with_plans.values("student_id").distinct().count()


def recompute_invoice(invoice: Invoice, *, today: date | None = None, save: bool = True) -> Invoice:
    """Totals from lines + posted payments; status from money state. Void is terminal."""
    lines = list(invoice.lines.all())
    subtotal = sum((ln.amount for ln in lines if ln.kind in ("fee", "adjustment")), ZERO)
    discounts = sum((ln.amount for ln in lines if ln.kind in ("discount", "scholarship")), ZERO)
    paid = invoice.payments.filter(status="posted").aggregate(s=Sum("amount"))["s"] or ZERO
    invoice.subtotal, invoice.discount_total = q3(subtotal), q3(discounts)
    invoice.total = q3(max(ZERO, subtotal - discounts))
    invoice.paid_total = q3(paid)
    if invoice.status != "void" and invoice.status != "draft":
        if invoice.paid_total >= invoice.total:
            invoice.status = "paid"
        elif invoice.paid_total > ZERO:
            invoice.status = "partially_paid"
        else:
            invoice.status = "issued"
        if invoice.status in ("issued", "partially_paid") and invoice.due_on < (today or date.today()):
            invoice.status = "overdue"
    if save:
        invoice.save()
    return invoice


@transaction.atomic
def generate_invoice(student_plan: StudentFeePlan, period_label: str, issued_on: date | None = None, due_on: date | None = None,
                     user=None, request=None) -> Invoice:
    """One invoice from one plan assignment: fee line, student discount, scholarship, sibling discount."""
    plan: FeePlan = student_plan.plan
    student = student_plan.student
    issued_on = issued_on or date.today()
    due_on = due_on or issued_on + timedelta(days=DEFAULT_TERMS_DAYS)
    if due_on < issued_on:
        raise DomainError("due_on cannot be before issued_on.")
    if student_plan.status != "active":
        raise DomainError("Plan assignment is not active.")
    if Invoice.objects.filter(source_plan=student_plan, period_label=period_label).exclude(status="void").exists():
        raise DomainError(f"An invoice for {period_label} already exists for this plan.")

    base = q3(plan.amount)
    lines: list[dict] = [{"kind": "fee", "description": f"{plan.name} — {period_label}", "unit_amount": base, "amount": base}]
    if student_plan.discount_pct > ZERO:
        d = q3(base * student_plan.discount_pct / 100)
        lines.append({"kind": "discount", "description": f"خصم {student_plan.discount_pct:g}%", "unit_amount": d, "amount": d})
    if student_plan.scholarship_pct > ZERO:
        s = q3(base * student_plan.scholarship_pct / 100)
        desc = f"منحة {student_plan.scholarship_pct:g}%" + (f" — {student_plan.scholarship_note}" if student_plan.scholarship_note else "")
        lines.append({"kind": "scholarship", "description": desc, "unit_amount": s, "amount": s})
    if plan.sibling_discount_pct > ZERO and sibling_count(student, issued_on) >= 2:
        sd = q3(base * plan.sibling_discount_pct / 100)
        lines.append({"kind": "discount", "description": f"خصم الإخوة {plan.sibling_discount_pct:g}%", "unit_amount": sd, "amount": sd})

    inv = Invoice.objects.create(
        number=NumberSequence.next_number("invoice", "INV"), student=student, payer_name=payer_name_for(student),
        issued_on=issued_on, due_on=due_on, currency=plan.currency, status="issued", source_plan=student_plan,
        period_label=period_label, created_by=user or _user(request))
    for i, ln in enumerate(lines):
        InvoiceLine.objects.create(invoice=inv, order=i, quantity=Decimal("1"), **ln)
    recompute_invoice(inv, today=issued_on)
    AuditLog.record(request, "invoice.issued", "Invoice", inv.id,
                    after={"number": inv.number, "student": str(student.id), "period": period_label, "total": str(inv.total)},
                    actor_type="user" if _user(request) else "system")
    return inv


def generate_monthly_invoices(period_label: str, request=None) -> list[Invoice]:
    """Idempotent: every active monthly assignment without a live invoice for the period gets one."""
    first, last = period_bounds(period_label)
    existing = set(Invoice.objects.filter(period_label=period_label).exclude(status="void").values_list("source_plan_id", flat=True))
    qs = StudentFeePlan.objects.filter(status="active", plan__cadence="monthly", plan__is_active=True, student__status="active") \
        .select_related("plan", "student__person").order_by("created_at")
    out = []
    for sp in qs:
        if sp.id in existing or not plan_active_on(sp, first, last):
            continue
        out.append(generate_invoice(sp, period_label, request=request))
    return out


# ---- payments ------------------------------------------------------------------------------
@transaction.atomic
def record_payment(invoice: Invoice, amount: Decimal, method: str = "cash", reference: str = "", received_on: date | None = None,
                   note: str = "", user=None, request=None) -> Payment:
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    amount = q3(amount)
    if invoice.status == "void":
        raise DomainError("Cannot pay a void invoice.")
    if invoice.status == "draft":
        raise DomainError("Invoice is not issued yet.")
    if amount <= ZERO:
        raise DomainError("Amount must be greater than zero.")
    outstanding = invoice.outstanding
    if outstanding <= ZERO:
        raise DomainError("Invoice is already settled.")
    if amount > outstanding:
        raise DomainError(f"Amount exceeds the outstanding balance ({outstanding}).")
    if method not in dict(Payment.METHOD):
        raise DomainError("Unknown payment method.")
    p = Payment.objects.create(invoice=invoice, amount=amount, currency=invoice.currency, method=method, reference=reference or "",
                               received_on=received_on or date.today(), note=note or "",
                               receipt_number=NumberSequence.next_number("receipt", "RCPT"), recorded_by=user or _user(request))
    before = {"status": invoice.status, "paid_total": str(invoice.paid_total)}
    recompute_invoice(invoice)
    AuditLog.record(request, "payment.recorded", "Payment", p.id,
                    before=before, after={"receipt": p.receipt_number, "invoice": invoice.number, "amount": str(amount), "method": method,
                                          "invoice_status": invoice.status, "paid_total": str(invoice.paid_total)})
    return p


@transaction.atomic
def refund_payment(payment: Payment, reason: str = "", user=None, request=None) -> Payment:
    if payment.status == "refunded":
        raise DomainError("Payment is already refunded.")
    if not (reason or "").strip():
        raise DomainError("A refund reason is required.")
    payment.status, payment.refunded_at, payment.refund_reason = "refunded", timezone.now(), reason.strip()
    payment.save(update_fields=["status", "refunded_at", "refund_reason", "updated_at"])
    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
    before = {"status": invoice.status, "paid_total": str(invoice.paid_total)}
    recompute_invoice(invoice)
    AuditLog.record(request, "payment.refunded", "Payment", payment.id, before=before,
                    after={"receipt": payment.receipt_number, "reason": payment.refund_reason, "invoice_status": invoice.status,
                           "paid_total": str(invoice.paid_total)})
    return payment


# ---- invoice lifecycle ---------------------------------------------------------------------
def mark_overdue(today: date | None = None, request=None) -> int:
    today = today or date.today()
    qs = Invoice.objects.filter(status__in=("issued", "partially_paid"), due_on__lt=today)
    ids = list(qs.values_list("id", flat=True))
    n = qs.update(status="overdue") if ids else 0
    if n:
        AuditLog.record(request, "invoice.overdue", "Invoice", "", after={"count": n, "as_of": str(today)},
                        actor_type="user" if _user(request) else "system")
    return n


@transaction.atomic
def void_invoice(invoice: Invoice, reason: str = "", user=None, request=None) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == "void":
        raise DomainError("Invoice is already void.")
    if invoice.paid_total > ZERO or invoice.payments.filter(status="posted").exists():
        raise DomainError("Only invoices with no posted payments can be voided. Refund payments first.")
    if not (reason or "").strip():
        raise DomainError("A void reason is required.")
    before = {"status": invoice.status}
    invoice.status = "void"
    invoice.notes = (invoice.notes + "\n" if invoice.notes else "") + f"[void] {reason.strip()}"
    invoice.save(update_fields=["status", "notes", "updated_at"])
    AuditLog.record(request, "invoice.voided", "Invoice", invoice.id, before=before, after={"status": "void", "reason": reason.strip()})
    return invoice


def summary(queryset) -> dict:
    """Tenant/scope totals for the overview KPIs. Excludes void invoices from money totals."""
    live = queryset.exclude(status="void")
    agg = live.aggregate(issued=Sum("total"), paid=Sum("paid_total"))
    issued, paid = q3(agg["issued"] or ZERO), q3(agg["paid"] or ZERO)
    by_status = {s: 0 for s, _ in Invoice.STATUS}
    for row in queryset.values("status").annotate(n=Count("id")):
        by_status[row["status"]] = row["n"]
    return {"issued_total": str(issued), "paid_total": str(paid), "outstanding_total": str(q3(max(ZERO, issued - paid))),
            "overdue_count": by_status.get("overdue", 0), "by_status": by_status}
