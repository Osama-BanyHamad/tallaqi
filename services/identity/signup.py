"""Self-serve sign-up for an independent learner (تَلَقِّي للأفراد).

One person, one tenant: the learner gets their own organization (kind "solo") behind the scenes, so row-level security,
the journey, the memory map, the planner, self-practice and the AI check all work unchanged. They can invite a listener
(parent, friend, remote teacher) through the normal accounts API, and later move to a center with their record.
"""
from __future__ import annotations

import re
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from packages.permissions.catalog import MODULES
from packages.quran_core import get_core
from services.common import context
from services.hifz import services as hifz
from services.hifz.models import QuranJourney, StudentAyahState
from services.identity.models import Account
from services.people.models import Person, Student
from services.rbac.services import assign, ensure_system_roles
from services.tenants.models import Branch, Membership, Tenant, TenantModule

from .views import memberships_for

SOLO_MODULES = ("hifz.retention", "hifz.policy", "hifz.planner", "hifz.tasmee", "hifz.practice", "hifz.review_queue", "hifz.asr", "hifz.assessments")


class SignupIn(serializers.Serializer):
    full_name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)
    locale = serializers.ChoiceField(choices=["ar", "en"], default="ar")
    goal = serializers.ChoiceField(choices=["juz30", "juz_29_30", "whole", "keep"], default="juz30")
    memorized_juz = serializers.ListField(child=serializers.IntegerField(min_value=1, max_value=30), default=list, max_length=30)
    daily_minutes = serializers.IntegerField(min_value=5, max_value=240, default=20)
    gender = serializers.ChoiceField(choices=["male", "female"], default="male")

    def validate_email(self, v):
        v = v.lower().strip()
        with context.platform_admin("signup-check"):
            if Account.objects.filter(email=v).exists():
                raise serializers.ValidationError("هذا البريد مسجّل من قبل. سجّل الدخول بدلًا من ذلك.")
        return v

    def validate_password(self, v):
        if v.isdigit() or v.lower() in ("password", "12345678", "talaqqi"):
            raise serializers.ValidationError("اختر كلمة مرور أقوى.")
        return v


def _slug(full_name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", full_name.lower().encode("ascii", "ignore").decode() or "learner").strip("-")[:20] or "learner"
    return f"solo-{base}-{secrets.token_hex(3)}"


def seed_memorized(journey: QuranJourney, juz_numbers: list[int], now) -> int:
    """Marks whole Juz as memorized at a 'needs revision' baseline, so the planner starts with revision and the
    learner's real recitations calibrate the map. Returns the number of Ayat marked."""
    core = get_core(journey.riwayah)
    rows, pages = [], set()
    for n in sorted(set(juz_numbers)):
        u = core.unit("juz", n)
        for i in range(u.first_ayah_index, u.last_ayah_index + 1):
            rows.append(StudentAyahState(tenant_id=journey.tenant_id, journey=journey, ayah_index=i, state="needs_revision", retention_score=0.7,
                                         stability_days=14, memorized_at=now - timedelta(days=60), last_recited_at=now - timedelta(days=14),
                                         last_passed_at=now - timedelta(days=14), success_count=3, consecutive_successes=2, next_due_at=now))
            pages.add(core.page_of(i))
    if rows:
        StudentAyahState.objects.bulk_create(rows, batch_size=2000)
        journey.memorized_pages_order = sorted(pages, reverse=True)
        journey.save(update_fields=["memorized_pages_order"])
    return len(rows)


def next_new_ayah(goal: str, memorized: set[int]) -> int | None:
    """Where new memorization starts: Juz 30 backwards is the common path; 'keep' means revision only."""
    core = get_core()
    order = {"juz30": [30], "juz_29_30": [30, 29], "whole": list(range(30, 0, -1)), "keep": []}[goal]
    for n in order:
        if n not in memorized:
            return core.unit("juz", n).first_ayah_index
    return None


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "signup"

    @transaction.atomic
    def post(self, request):
        s = SignupIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        now = timezone.now()
        first = d["full_name"].split(" ")[0]
        with context.platform_admin("signup"):
            account = Account.objects.create_user(email=d["email"], password=d["password"], full_name=d["full_name"], locale=d["locale"])
            tenant = Tenant.objects.create(slug=_slug(d["full_name"]), name=f"رحلة {first} مع القرآن", name_en=f"{first}'s Quran journey", kind="solo",
                                           locales=["ar", "en"], default_locale=d["locale"], branding={"app_name": "تَلَقِّي"})
            for key in SOLO_MODULES:
                if key in MODULES and not MODULES[key].core:
                    TenantModule.objects.create(tenant=tenant, module_key=key, enabled=True)
        with context.tenant(tenant.id):
            roles = ensure_system_roles(tenant)
            branch = Branch.objects.create(tenant=tenant, name="منزلي", name_en="Home", code="HOME")
            person = Person.objects.create(tenant=tenant, first_name=first, last_name=" ".join(d["full_name"].split(" ")[1:]), display_name_ar=d["full_name"], gender=d["gender"], email=d["email"])
            student = Student.objects.create(tenant=tenant, person=person, branch=branch, student_code="ME", status="active", is_minor=False)
            memorized = set(d["memorized_juz"])
            nxt = next_new_ayah(d["goal"], memorized)
            journey = QuranJourney.objects.create(tenant=tenant, student=student, started_at=now.date(), current_ayah_index=nxt,
                                                  policy_overrides={"daily_minutes": d["daily_minutes"], "goal": d["goal"]},
                                                  status="memorizing" if nxt is not None else "revising")
            marked = seed_memorized(journey, list(memorized), now)
            hifz.refresh_aggregates(journey)
            hifz.generate_plan(journey, now.date(), now)
            membership = Membership.objects.create(account=account, tenant=tenant, person=person)
            assign(membership, roles["solo_learner"], "tenant", [])
        refresh = RefreshToken.for_user(account)
        return Response({
            "access": str(refresh.access_token), "refresh": str(refresh),
            "account": {"id": account.id, "email": account.email, "full_name": account.full_name, "locale": account.locale},
            "memberships": memberships_for(account),
            "tenant": tenant.slug, "journey_id": journey.id, "memorized_ayat": marked,
        }, status=status.HTTP_201_CREATED)
