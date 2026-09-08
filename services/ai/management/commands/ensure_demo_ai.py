"""Enable the AI assistant module for the demo tenant (idempotent). The provider itself comes from the environment."""
from django.conf import settings
from django.core.management.base import BaseCommand

from services.common import context
from services.tenants.models import Tenant, TenantModule


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", default="demo")

    def handle(self, *args, **opts):
        with context.platform_admin("demo-ai"):
            t = Tenant.objects.get(slug=opts["slug"])
            for key in ("ai.assist", "hifz.asr"):
                TenantModule.objects.update_or_create(tenant=t, module_key=key, defaults={"enabled": True})
        provider = getattr(settings, "AI_PROVIDER", "null")
        self.stdout.write(self.style.SUCCESS(f"ai.assist enabled for '{opts['slug']}' (provider: {provider}, model: {getattr(settings, 'OPENAI_MODEL', '')})"))
