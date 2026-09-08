"""Flip issued / partially paid invoices past their due date to overdue (daily cron)."""
from datetime import date

from django.core.management.base import BaseCommand

from services.common import context
from services.finance import services
from services.tenants.models import TenantModule


class Command(BaseCommand):
    help = "Mark past-due invoices as overdue for every tenant with invoicing enabled."

    def handle(self, *args, **opts):
        with context.platform_admin("mark-overdue"):
            tenants = list(TenantModule.objects.unsafe_all().filter(module_key="finance.invoicing", enabled=True).values_list("tenant_id", flat=True))
        n = 0
        for tid in tenants:
            with context.tenant(tid):
                n += services.mark_overdue(date.today())
        self.stdout.write(self.style.SUCCESS(f"marked {n} invoices overdue"))
