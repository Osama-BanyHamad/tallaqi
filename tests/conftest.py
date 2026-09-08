"""Shared fixtures: two seeded tenants for isolation tests, API clients per role."""
from __future__ import annotations

from datetime import date

import pytest
from rest_framework.test import APIClient

from services.common import context
from services.identity.models import Account
from services.people.models import Enrollment, Halaqah, HalaqahStaff, Person, Staff, Student
from services.rbac.services import assign, ensure_system_roles
from services.tenants.models import Branch, Membership, Tenant, TenantModule


def make_tenant(slug: str, name: str):
    with context.platform_admin("test-provision"):
        t = Tenant.objects.create(slug=slug, name=name, locales=["ar", "en"])
        for key in ("people.guardians", "people.staff", "ops.halaqat", "ops.attendance", "hifz.retention", "hifz.policy",
                    "hifz.planner", "hifz.tasmee", "hifz.assessments", "hifz.practice", "hifz.review_queue", "parent.portal",
                    "intel.supervisor", "intel.intervention", "intel.reports"):
            TenantModule.objects.create(tenant=t, module_key=key, enabled=True)
    with context.tenant(t.id):
        roles = ensure_system_roles(t)
        b1 = Branch.objects.create(tenant=t, name=f"{name} — الفرع الأول")
        b2 = Branch.objects.create(tenant=t, name=f"{name} — الفرع الثاني")
        h1 = Halaqah.objects.create(tenant=t, branch=b1, name="حلقة الفجر")
        h2 = Halaqah.objects.create(tenant=t, branch=b2, name="حلقة العصر")

        def person(n):
            return Person.objects.create(tenant=t, first_name=n, display_name_ar=n)

        def student(n, branch, halaqah, code):
            s = Student.objects.create(tenant=t, person=person(n), branch=branch, student_code=code)
            Enrollment.objects.create(tenant=t, student=s, halaqah=halaqah, start_date=date(2026, 1, 1))
            from services.hifz.models import QuranJourney
            QuranJourney.objects.create(tenant=t, student=s, started_at=date(2026, 1, 1), current_ayah_index=6231)
            return s

        s1 = student(f"طالب-1-{slug}", b1, h1, f"{slug}-001")
        s2 = student(f"طالب-2-{slug}", b2, h2, f"{slug}-002")
        teacher_person = person(f"معلم-{slug}")
        teacher = Staff.objects.create(tenant=t, person=teacher_person, branch=b1, staff_type="teacher")
        HalaqahStaff.objects.create(tenant=t, halaqah=h1, staff=teacher)

        def account(email, role_key, scope_type="tenant", refs=(), person_obj=None):
            a = Account.objects.create_user(email=email, password="Passw0rd!Test", full_name=email.split("@")[0])
            m = Membership.objects.create(account=a, tenant=t, person=person_obj)
            assign(m, roles[role_key], scope_type, list(refs))
            return a

        owner = account(f"owner@{slug}.test", "owner")
        sup = account(f"sup@{slug}.test", "quran_supervisor", "branch", [b1.id])
        tch = account(f"teacher@{slug}.test", "teacher", "halaqah", [h1.id], teacher_person)
        fin = account(f"finance@{slug}.test", "finance")
    return {"tenant": t, "branches": (b1, b2), "halaqat": (h1, h2), "students": (s1, s2), "teacher_staff": teacher,
            "accounts": {"owner": owner, "supervisor": sup, "teacher": tch, "finance": fin}}


@pytest.fixture
def tenants(db):
    return {"a": make_tenant("alpha", "مركز ألفا"), "b": make_tenant("beta", "مركز بيتا")}


def client_for(account, tenant_slug: str) -> APIClient:
    from rest_framework_simplejwt.tokens import RefreshToken
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(account).access_token}", HTTP_X_TENANT=tenant_slug)
    return c
