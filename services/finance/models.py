"""Finance: fee plans, student plan assignments, invoices (snapshot-safe), payments, per-tenant number sequences.

Money is Decimal(12, 3): JOD has three decimal places. Currency is copied from the tenant at creation time."""
from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from services.common.models import TenantModel

PCT = [MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))]


def money(**kw):
    return models.DecimalField(max_digits=12, decimal_places=3, **kw)


def pct(**kw):
    return models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"), validators=PCT, **kw)


class NumberSequence(TenantModel):
    """Per-tenant monotonically increasing counters (invoice / receipt numbers). Locked with select_for_update."""
    key = models.CharField(max_length=32)
    next_value = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "finance_number_sequence"
        unique_together = [("tenant", "key")]

    @classmethod
    def next_number(cls, key: str, prefix: str, width: int = 6) -> str:
        with transaction.atomic():
            row, _ = cls.objects.select_for_update().get_or_create(key=key)
            value = row.next_value
            row.next_value = value + 1
            row.save(update_fields=["next_value", "updated_at"])
        return f"{prefix}-{value:0{width}d}"


class FeePlan(TenantModel):
    CADENCE = [("monthly", "شهري"), ("term", "فصلي"), ("annual", "سنوي"), ("one_time", "مرة واحدة")]
    name = models.CharField(max_length=120)
    cadence = models.CharField(max_length=10, choices=CADENCE, default="monthly")
    amount = money()
    currency = models.CharField(max_length=3, default="JOD")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sibling_discount_pct = pct()
    branch = models.ForeignKey("tenants.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="fee_plans")

    class Meta:
        db_table = "finance_fee_plan"
        ordering = ["name"]

    def __str__(self):
        return self.name


class StudentFeePlan(TenantModel):
    STATUS = [("active", "نشط"), ("ended", "منتهٍ")]
    student = models.ForeignKey("people.Student", on_delete=models.CASCADE, related_name="fee_plans")
    plan = models.ForeignKey(FeePlan, on_delete=models.PROTECT, related_name="assignments")
    discount_pct = pct()
    scholarship_pct = pct()
    scholarship_note = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUS, default="active")

    class Meta:
        db_table = "finance_student_fee_plan"
        unique_together = [("student", "plan", "start_date")]
        ordering = ["-start_date"]


class Invoice(TenantModel):
    STATUS = [("draft", "مسودة"), ("issued", "صادرة"), ("partially_paid", "مدفوعة جزئيًا"), ("paid", "مدفوعة"),
              ("overdue", "متأخرة"), ("void", "ملغاة")]
    OPEN_STATUSES = ("issued", "partially_paid", "overdue")
    number = models.CharField(max_length=20)
    student = models.ForeignKey("people.Student", on_delete=models.PROTECT, related_name="invoices")
    payer_name = models.CharField(max_length=200, blank=True)
    issued_on = models.DateField()
    due_on = models.DateField()
    currency = models.CharField(max_length=3, default="JOD")
    subtotal = money(default=Decimal("0"))
    discount_total = money(default=Decimal("0"))
    total = money(default=Decimal("0"))
    paid_total = money(default=Decimal("0"))
    status = models.CharField(max_length=16, choices=STATUS, default="issued", db_index=True)
    notes = models.TextField(blank=True)
    source_plan = models.ForeignKey(StudentFeePlan, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices")
    period_label = models.CharField(max_length=20, blank=True, db_index=True)
    created_by = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "finance_invoice"
        unique_together = [("tenant", "number")]
        ordering = ["-issued_on", "-number"]

    def __str__(self):
        return self.number

    @property
    def outstanding(self) -> Decimal:
        return max(Decimal("0"), self.total - self.paid_total)


class InvoiceLine(TenantModel):
    KIND = [("fee", "رسوم"), ("discount", "خصم"), ("scholarship", "منحة"), ("adjustment", "تسوية")]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1"))
    unit_amount = money()
    amount = money()
    kind = models.CharField(max_length=12, choices=KIND, default="fee")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "finance_invoice_line"
        ordering = ["order", "created_at"]


class Payment(TenantModel):
    METHOD = [("cash", "نقدًا"), ("bank_transfer", "تحويل بنكي"), ("card_manual", "بطاقة (يدوي)"), ("other", "أخرى")]
    STATUS = [("posted", "مسجلة"), ("refunded", "مستردة")]
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = money()
    currency = models.CharField(max_length=3, default="JOD")
    method = models.CharField(max_length=16, choices=METHOD, default="cash")
    reference = models.CharField(max_length=120, blank=True)
    received_on = models.DateField()
    note = models.CharField(max_length=300, blank=True)
    receipt_number = models.CharField(max_length=20)
    recorded_by = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    status = models.CharField(max_length=10, choices=STATUS, default="posted", db_index=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "finance_payment"
        unique_together = [("tenant", "receipt_number")]
        ordering = ["-received_on", "-created_at"]

    def __str__(self):
        return self.receipt_number
