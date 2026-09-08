"""AI assist: module gating, provider fallbacks, guardrails, scope. Never hits the network."""
import pytest

from services.ai import providers, services
from services.common import context
from services.tenants.models import TenantModule
from tests.conftest import client_for

pytestmark = pytest.mark.django_db


def _enable(tenant):
    with context.platform_admin("t"):
        TenantModule.objects.update_or_create(tenant=tenant, module_key="ai.assist", defaults={"enabled": True})


def test_disabled_module_returns_capability_disabled(tenants):
    a = tenants["a"]
    c = client_for(a["accounts"]["teacher"], "alpha")
    r = c.post("/api/v1/ai/weekly-note", {"student_id": str(a["students"][0].id)}, format="json")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"


def test_null_provider_gives_503(tenants, settings):
    a = tenants["a"]
    _enable(a["tenant"])
    settings.AI_PROVIDER = "null"
    c = client_for(a["accounts"]["teacher"], "alpha")
    assert c.get("/api/v1/ai/status").json()["configured"] is False
    r = c.post("/api/v1/ai/weekly-note", {"student_id": str(a["students"][0].id)}, format="json")
    assert r.status_code == 503 and r.json()["code"] == "ai_unavailable"


def test_fake_provider_draft_is_labeled_and_prompt_has_no_quran_text(tenants, settings, monkeypatch):
    a = tenants["a"]
    _enable(a["tenant"])
    fake = providers.FakeProvider("أحسن الطالب هذا الأسبوع في سورة النبأ ١ إلى ١٥. ﴿عَمَّ يَتَسَاءَلُونَ﴾ نوصي بمراجعة يومية.")
    monkeypatch.setattr(providers, "get_provider", lambda: fake)
    monkeypatch.setattr(services, "get_provider", lambda: fake)
    c = client_for(a["accounts"]["teacher"], "alpha")
    r = c.post("/api/v1/ai/weekly-note", {"student_id": str(a["students"][0].id)}, format="json")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["source"] == "ai" and body["safety"] == "YELLOW" and body["disclaimer"]
    assert "﴿" not in body["text"] and "يَتَسَاءَلُونَ" not in body["text"], "quoted verse must be stripped"
    assert "النبأ" in body["text"]  # surah names are fine
    system, user = fake.calls[0]
    assert "لا تقتبس" in system and "الطالب:" in user and "﴿" not in user
    # audit trail, no prompt content stored
    r = client_for(a["accounts"]["owner"], "alpha").get("/api/v1/audit?search=ai.weekly_note")
    assert r.json()["count"] >= 1


def test_explain_journey_and_scope(tenants, settings, monkeypatch):
    a = tenants["a"]
    _enable(a["tenant"])
    fake = providers.FakeProvider("شرح تجريبي.")
    monkeypatch.setattr(services, "get_provider", lambda: fake)
    teacher = client_for(a["accounts"]["teacher"], "alpha")
    with context.tenant(a["tenant"].id):
        own = a["students"][0].journey.id
        other = a["students"][1].journey.id  # second branch / other halaqah
    assert teacher.post("/api/v1/ai/explain-journey", {"journey_id": str(own)}, format="json").status_code == 200
    assert teacher.post("/api/v1/ai/explain-journey", {"journey_id": str(other)}, format="json").status_code == 404
    # students and finance never get the assistant
    assert client_for(a["accounts"]["finance"], "alpha").post("/api/v1/ai/weekly-note", {"journey_id": str(own)}, format="json").status_code == 403


def test_sanitize_strips_verse_like_content():
    s = services.sanitize("قال المعلم: ﴿إِنَّ الْإِنسَانَ لَفِي خُسْرٍ﴾ ثم بسم الله الرحمن الرحيم — راجع سورة العصر ١ إلى ٣.")
    assert "﴿" not in s and "خُسْرٍ" not in s and "بسم الله" not in s and "العصر ١ إلى ٣" in s
