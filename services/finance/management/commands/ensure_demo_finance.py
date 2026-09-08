"""Idempotently enable finance for the demo tenant and seed a plan, assignments, two months of invoices, and realistic payments."""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from services.common import context
from services.finance import services as fin
from services.finance.models import FeePlan, Invoice, StudentFeePlan
from services.people.models import Student
from services.tenants.models import Tenant, TenantModule


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", default="demo")

    def handle(self, *args, **opts):
        random.seed(11)
        with context.platform_admin("demo-finance"):
            t = Tenant.objects.get(slug=opts["slug"])
            for key in ("finance.fees", "finance.invoicing", "finance.payments"):
                TenantModule.objects.update_or_create(tenant=t, module_key=key, defaults={"enabled": True})
        with context.tenant(t.id), transaction.atomic():
            plan, _ = FeePlan.objects.get_or_create(
                tenant=t, name="الاشتراك الشهري", defaults=dict(cadence="monthly", amount=Decimal("25.000"), currency=t.currency, sibling_discount_pct=Decimal("10"), description="رسوم الحلقة الشهرية شاملة المتابعة"))
            today = date.today()
            start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)  # first day of previous month
            students = list(Student.objects.filter(status="active").order_by("student_code"))
            created = 0
            for i, st in enumerate(students):
                sp, was_new = StudentFeePlan.objects.get_or_create(student=st, plan=plan, start_date=start, defaults={"tenant": t})
                if was_new and i % 9 == 0:
                    sp.scholarship_pct = Decimal("50")
                    sp.scholarship_note = "منحة حفظ متميز"
                    sp.save()
                created += was_new
            self.stdout.write(f"plan assignments: {created} new, {len(students)} total")
            for period_start, pay_prob in ((start, 0.85), (today.replace(day=1), 0.45)):
                label = period_start.strftime("%Y-%m")
                invoices = [inv for inv in (self._invoice(sp, label, period_start) for sp in StudentFeePlan.objects.filter(plan=plan, status="active")) if inv]
                paid = 0
                for inv in invoices:
                    if inv.status in ("issued", "overdue") and random.random() < pay_prob:
                        amt = inv.outstanding if random.random() < 0.8 else fin.q3(inv.outstanding / 2)
                        fin.record_payment(inv, amt, method=random.choice(["cash", "cash", "bank_transfer"]), received_on=period_start + timedelta(days=random.randint(1, 12)))
                        paid += 1
                self.stdout.write(f"{label}: {len(invoices)} new invoices, {paid} payments")
            fin.mark_overdue()
        self.stdout.write(self.style.SUCCESS("demo finance ready"))

    @staticmethod
    def _invoice(sp: StudentFeePlan, label: str, period_start: date) -> Invoice | None:
        if Invoice.objects.filter(source_plan=sp, period_label=label).exclude(status="void").exists():
            return None
        return fin.generate_invoice(sp, label, issued_on=period_start, due_on=period_start + timedelta(days=14))
