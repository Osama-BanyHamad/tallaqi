"""Product funnel for the /stats/ page (no personal data): tenants, sign-ups, active learners, recitations, AI usage.
Prints JSON; infra/scripts/stats.sh writes it next to the report."""
import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from services.audit.models import AuditLog
from services.common import context
from services.hifz.models import QuranJourney, RecitationSession
from services.identity.models import Account
from services.tenants.models import Membership, Tenant


class Command(BaseCommand):
    def handle(self, *args, **opts):
        now = timezone.now()
        d1, d7, d30 = now - timedelta(days=1), now - timedelta(days=7), now - timedelta(days=30)
        with context.platform_admin("funnel"):
            tenants = dict(Tenant.objects.values_list("kind").annotate(n=Count("id")).values_list("kind", "n"))
            accounts = Account.objects.count()
            signups = {"24h": Account.objects.filter(created_at__gte=d1).count(), "7d": Account.objects.filter(created_at__gte=d7).count(), "30d": Account.objects.filter(created_at__gte=d30).count()}
            solo = Tenant.objects.filter(kind="solo").count()
            solo_signups_7d = Tenant.objects.filter(kind="solo", created_at__gte=d7).count() if hasattr(Tenant, "created_at") else None
            journeys = QuranJourney.objects.unsafe_all().count()
            sessions = RecitationSession.objects.unsafe_all()
            active_7d = sessions.filter(started_at__gte=d7).values("journey_id").distinct().count()
            recitations = {"24h": sessions.filter(started_at__gte=d1).count(), "7d": sessions.filter(started_at__gte=d7).count(), "30d": sessions.filter(started_at__gte=d30).count()}
            logs = AuditLog.objects.unsafe_all()
            ai = {"asr_7d": logs.filter(action="ai.asr_check", created_at__gte=d7).count(), "drafts_7d": logs.filter(action__in=["ai.weekly_note", "ai.explain_journey"], created_at__gte=d7).count(),
                  "asr_30d": logs.filter(action="ai.asr_check", created_at__gte=d30).count()}
            logins_7d = logs.filter(action="auth.login", created_at__gte=d7).count()
            members = Membership.objects.unsafe_all().count()
        out = {"generated_at": now.isoformat(), "tenants": tenants, "solo_tenants": solo, "solo_signups_7d": solo_signups_7d, "accounts": accounts, "memberships": members,
               "signups": signups, "journeys": journeys, "active_learners_7d": active_7d, "recitations": recitations, "ai": ai, "logins_7d": logins_7d}
        self.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
