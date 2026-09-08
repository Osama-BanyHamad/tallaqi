"""Re-sync system roles from the permission catalog for every tenant (idempotent, additive).

Role permissions live in the database per tenant; when the catalog gains a permission or a role gains a grant,
existing tenants only pick it up through this command. Runs on every deploy after migrations.
"""
from django.core.management.base import BaseCommand

from services.common import context
from services.rbac.services import ensure_system_roles
from services.tenants.models import Tenant


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", default=None, help="Only this tenant")

    def handle(self, *args, **opts):
        with context.platform_admin("sync-roles"):
            tenants = list(Tenant.objects.filter(slug=opts["slug"]) if opts["slug"] else Tenant.objects.all())
        for t in tenants:
            with context.tenant(t.id):
                roles = ensure_system_roles(t)
            self.stdout.write(f"{t.slug}: {len(roles)} system roles synced")
        self.stdout.write(self.style.SUCCESS(f"synced {len(tenants)} tenant(s)"))
