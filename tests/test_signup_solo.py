"""Independent learner: sign-up creates a solo tenant with a seeded journey and plan; a listener can be invited and record Tasmee';
login is rate limited."""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from services.common import context
from services.hifz.models import QuranJourney
from services.tenants.models import Tenant

pytestmark = pytest.mark.django_db


def _signup(payload=None):
    c = APIClient()
    body = {"full_name": "ليان الحوراني", "email": "layan@example.com", "password": "Strong-Pass-2026", "goal": "whole", "memorized_juz": [29, 30], "daily_minutes": 20, "gender": "female"}
    body.update(payload or {})
    return c, c.post("/api/v1/auth/signup", body, format="json")


def test_signup_creates_solo_tenant_journey_and_plan():
    cache.clear()
    c, r = _signup()
    assert r.status_code == 201, r.content
    j = r.json()
    assert j["memberships"][0]["roles"] == ["solo_learner"] and j["memberships"][0]["tenant_kind"] == "solo"
    assert j["memorized_ayat"] > 500 and j["journey_id"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {j['access']}", HTTP_X_TENANT=j["tenant"])
    caps = c.get("/api/v1/me/capabilities").json()
    assert "hifz.practice.use" in caps["permissions"] and caps["modules"]["hifz.asr"]["enabled"] and caps["modules"]["hifz.practice"]["enabled"]
    jr = c.get(f"/api/v1/journeys/{j['journey_id']}").json()
    assert jr["memorized_ayat"] > 500 and jr["current_ayah_index"] is not None  # Juz 29–30 known → new memorization continues below Juz 29
    plan = c.get(f"/api/v1/journeys/{j['journey_id']}/plan").json()
    assert plan["segments"], "the planner must produce revision on day one"
    # duplicate email is refused, cleanly
    _, r2 = _signup()
    assert r2.status_code == 400 and "email" in r2.json()["detail"]


def test_solo_learner_invites_listener_who_records_tasmee():
    cache.clear()
    c, r = _signup({"email": "omar@example.com", "full_name": "عمر القيسي", "goal": "keep", "memorized_juz": [30]})
    j = r.json()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {j['access']}", HTTP_X_TENANT=j["tenant"])
    inv = c.post("/api/v1/accounts", {"email": "dad@example.com", "full_name": "أبو عمر", "role_key": "listener", "scope_type": "tenant", "scope_refs": []}, format="json")
    assert inv.status_code == 201, inv.content
    pw = inv.json()["generated_password"]
    listener = APIClient()
    login = listener.post("/api/v1/auth/login", {"email": "dad@example.com", "password": pw}, format="json")
    assert login.status_code == 200
    listener.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}", HTTP_X_TENANT=j["tenant"])
    plan = listener.get(f"/api/v1/journeys/{j['journey_id']}/plan").json()
    seg = plan["segments"][0]
    rec = listener.post("/api/v1/recitations", {"journey": j["journey_id"], "purpose": seg["purpose"], "from_ayah_index": seg["from_ayah_index"], "to_ayah_index": seg["to_ayah_index"],
                                                "outcome": "pass", "mistakes": [], "plan_segment": seg["id"], "idempotency_key": "solo-1"}, format="json")
    assert rec.status_code == 201, rec.content
    # the learner cannot record their own Tasmee'
    own = c.post("/api/v1/recitations", {"journey": j["journey_id"], "purpose": "far", "from_ayah_index": seg["from_ayah_index"], "to_ayah_index": seg["to_ayah_index"], "outcome": "pass", "mistakes": []}, format="json")
    assert own.status_code == 403
    with context.platform_admin("t"):
        tenant = Tenant.objects.get(slug=j["tenant"])
        assert tenant.kind == "solo"
    with context.tenant(tenant.id):
        assert QuranJourney.objects.get(pk=j["journey_id"]).status == "revising"


def test_login_is_rate_limited():
    cache.clear()
    c = APIClient()
    codes = [c.post("/api/v1/auth/login", {"email": "nobody@example.com", "password": "x"}, format="json").status_code for _ in range(22)]
    assert codes[0] == 401 and 429 in codes
    cache.clear()
