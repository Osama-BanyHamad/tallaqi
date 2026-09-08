"""Monthly invoice run for every tenant with invoicing enabled (cron/worker). Idempotent per period."""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from services.common import context
from services.finance import services
from services.tenants.models import TenantModule


class Command(BaseCommand):
    help = "Generate monthly invoices for all active monthly plan assignments. --period YYYY-MM (default: current month)."

    def add_arguments(self, parser):
        parser.add_argument("--period", default=date.today().strftime("%Y-%m"))
        parser.add_argument("--tenant", default=None, help="Limit to one tenant slug.")

    def handle(self, *args, **opts):
        period = opts["period"]
        try:
            services.period_bounds(period)
        except Exception as e:  # DomainError is an APIException; surface as a CLI error
            raise CommandError(str(getattr(e, "detail", e))) from None
        with context.platform_admin("generate-invoices"):
            rows = TenantModule.objects.unsafe_all().filter(module_key="finance.invoicing", enabled=True).select_related("tenant")
            if opts["tenant"]:
                rows = rows.filter(tenant__slug=opts["tenant"])
            tenants = [(r.tenant_id, r.tenant.slug) for r in rows]
        total = 0
        for tid, slug in tenants:
            with context.tenant(tid):
                created = services.generate_monthly_invoices(period)
                services.mark_overdue(date.today())
            total += len(created)
            self.stdout.write(f"{slug}: {len(created)} invoices for {period}")
        self.stdout.write(self.style.SUCCESS(f"generated {total} invoices for {period}"))
