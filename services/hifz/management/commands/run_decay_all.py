"""Daily retention decay + plan generation for every journey (run by cron/worker)."""
from datetime import UTC, datetime

from django.core.management.base import BaseCommand

from services.common import context
from services.hifz import services
from services.hifz.models import QuranJourney


class Command(BaseCommand):
    help = "Apply retention decay and generate today's plan for all journeys across tenants."

    def handle(self, *args, **opts):
        now = datetime.now(UTC)
        n = 0
        with context.platform_admin("daily-decay"):
            ids = list(QuranJourney.objects.unsafe_all().values_list("id", "tenant_id"))
        for jid, tid in ids:
            with context.tenant(tid):
                j = QuranJourney.objects.get(pk=jid)
                services.run_decay(j, now)
                services.generate_plan(j, now.date(), now)
                n += 1
        self.stdout.write(self.style.SUCCESS(f"decayed + planned {n} journeys"))
