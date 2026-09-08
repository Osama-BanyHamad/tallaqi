"""Multi-tenant isolation, IDOR, capability gating, scoped permissions, and the Tasmee' loop end-to-end."""
import pytest
from django.db import connection

from services.common import context
from services.people.models import Student
from tests.conftest import client_for

pytestmark = pytest.mark.django_db


def test_tenant_lists_never_leak(tenants):
    a, b = tenants["a"], tenants["b"]
    ca = client_for(a["accounts"]["owner"], "alpha")
    r = ca.get("/api/v1/students")
    assert r.status_code == 200
    codes = {s["student_code"] for s in r.json()["results"]}
    assert codes == {"alpha-001", "alpha-002"}
    # searching for the other tenant's student by name returns nothing
    r = ca.get("/api/v1/students?search=beta")
    assert r.json()["count"] == 0
    # journeys and halaqat likewise
    assert {h["name"] for h in ca.get("/api/v1/halaqat").json()["results"]} == {"حلقة الفجر", "حلقة العصر"}
    assert ca.get("/api/v1/journeys").json()["count"] == 2


def test_idor_across_tenants_is_404(tenants):
    a, b = tenants["a"], tenants["b"]
    ca = client_for(a["accounts"]["owner"], "alpha")
    other = b["students"][0]
    assert ca.get(f"/api/v1/students/{other.id}").status_code == 404
    assert ca.patch(f"/api/v1/students/{other.id}", {"level": "x"}, format="json").status_code == 404
    with context.tenant(b["tenant"].id):
        assert Student.objects.get(pk=other.id).level == ""


def test_wrong_tenant_header_is_forbidden(tenants):
    a = tenants["a"]
    c = client_for(a["accounts"]["owner"], "beta")
    assert c.get("/api/v1/students").status_code == 403


def test_rls_blocks_raw_queries_without_context(tenants):
    """Even a raw query under the app role sees nothing without app.tenant_id (defense in depth)."""
    with context.use(context.TenantContext()):
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM people_student")
            assert cur.fetchone()[0] == 0
    with context.tenant(tenants["a"]["tenant"].id):
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM people_student")
            assert cur.fetchone()[0] == 2


def test_teacher_scoped_to_own_halaqah(tenants):
    a = tenants["a"]
    ct = client_for(a["accounts"]["teacher"], "alpha")
    students = ct.get("/api/v1/students").json()["results"]
    assert [s["student_code"] for s in students] == ["alpha-001"]
    s2 = a["students"][1]
    assert ct.get(f"/api/v1/students/{s2.id}").status_code == 404
    # cannot record tasmee' for a student outside scope
    j2 = s2.journey
    r = ct.post("/api/v1/recitations", {"journey": str(j2.id), "purpose": "new", "from_ayah_index": 6231, "to_ayah_index": 6236,
                                        "outcome": "pass"}, format="json")
    assert r.status_code == 404


def test_finance_cannot_read_memory_map(tenants):
    a = tenants["a"]
    cf = client_for(a["accounts"]["finance"], "alpha")
    assert cf.get("/api/v1/students").status_code == 200
    j = a["students"][0].journey
    r = cf.get(f"/api/v1/journeys/{j.id}/memory-map?level=quran")
    assert r.status_code == 403 and r.json()["code"] == "permission_denied"


def test_disabled_module_returns_capability_disabled(tenants):
    a = tenants["a"]
    ca = client_for(a["accounts"]["owner"], "alpha")
    assert ca.get("/api/v1/dashboard").status_code == 200
    r = ca.put("/api/v1/tenant/modules", {"key": "intel.intervention", "enabled": False}, format="json")
    assert r.status_code == 200
    r = ca.put("/api/v1/tenant/modules", {"key": "intel.supervisor", "enabled": False}, format="json")
    assert r.status_code == 200
    r = ca.get("/api/v1/dashboard")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"
    caps = ca.get("/api/v1/me/capabilities").json()
    assert caps["modules"]["intel.supervisor"]["enabled"] is False
    assert caps["tenant"]["locale"] == "ar"


def test_core_module_cannot_be_disabled(tenants):
    ca = client_for(tenants["a"]["accounts"]["owner"], "alpha")
    r = ca.put("/api/v1/tenant/modules", {"key": "quran.core", "enabled": False}, format="json")
    assert r.status_code == 422


def test_no_role_can_grant_ijazah(tenants):
    for acc in tenants["a"]["accounts"].values():
        caps = client_for(acc, "alpha").get("/api/v1/me/capabilities").json()
        assert "hifz.ijazah.grant" not in caps["permissions"]


def test_tasmee_loop_updates_memory_map_and_plan(tenants):
    a = tenants["a"]
    ct = client_for(a["accounts"]["teacher"], "alpha")
    s1 = a["students"][0]
    j = s1.journey
    # Surah An-Nas: ayah_index 6231..6236. New memorization passes.
    r = ct.post("/api/v1/recitations", {"journey": str(j.id), "purpose": "new", "from_ayah_index": 6231, "to_ayah_index": 6236,
                                        "outcome": "pass", "halaqah": str(a["halaqat"][0].id), "idempotency_key": "k1",
                                        "mistakes": [{"ayah_index": 6234, "mistake_type": "tajweed", "severity": "minor"}]}, format="json")
    assert r.status_code == 201, r.content
    sid = r.json()["id"]
    # idempotent replay returns the same session
    r2 = ct.post("/api/v1/recitations", {"journey": str(j.id), "purpose": "new", "from_ayah_index": 6231, "to_ayah_index": 6236,
                                         "outcome": "pass", "idempotency_key": "k1"}, format="json")
    assert r2.json()["id"] == sid
    mm = ct.get(f"/api/v1/journeys/{j.id}/memory-map?level=surah&number=114").json()
    assert mm["memorized_ayat"] == 6 and all(u["state"] == "recent" for u in mm["units"])
    jr = ct.get(f"/api/v1/journeys/{j.id}").json()
    assert jr["memorized_ayat"] == 6 and jr["current_key"]["surah"] == 113   # position moved backward to Al-Falaq
    tl = ct.get(f"/api/v1/journeys/{j.id}/timeline").json()
    assert {e["event_type"] for e in tl} >= {"journey.first_memorization", "surah.completed"}
    # a failed far revision drops the state
    r = ct.post("/api/v1/recitations", {"journey": str(j.id), "purpose": "far", "from_ayah_index": 6231, "to_ayah_index": 6236,
                                        "outcome": "repeat", "mistakes": [{"ayah_index": 6232, "mistake_type": "forgotten_word"},
                                                                          {"ayah_index": 6233, "mistake_type": "skipped_ayah"}]}, format="json")
    assert r.status_code == 201
    mm = ct.get(f"/api/v1/journeys/{j.id}/memory-map?level=page&number=604").json()
    states = {u["key"]: u["state"] for u in mm["units"]}
    assert states["114:2"] in ("weak", "critical") and states["114:3"] in ("weak", "critical")
    assert next(u for u in mm["units"] if u["key"] == "114:2")["explanation"]   # Arabic explanation present
    # plan for today includes near revision of page 604 and a new segment in Al-Falaq
    plan = ct.get(f"/api/v1/journeys/{j.id}/plan").json()
    purposes = {s["purpose"] for s in plan["segments"]}
    assert "near" in purposes and "new" in purposes
    new = next(s for s in plan["segments"] if s["purpose"] == "new")
    assert new["from_key"]["key"] == "113:1"
    # teacher override of the plan is recorded
    r = ct.post(f"/api/v1/journeys/{j.id}/plan/action", {"action": "override", "reason": "تركيز على الناس",
                                                        "segments": [{"purpose": "near", "from_ayah_index": 6231, "to_ayah_index": 6236}]}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "overridden" and len(r.json()["segments"]) == 1
    # halaqah today screen shows the roster with plan
    today = ct.get(f"/api/v1/halaqat/{a['halaqat'][0].id}/today").json()
    assert today["roster"][0]["plan"]["status"] == "overridden"
    # audit trail exists
    from services.audit.models import AuditLog
    with context.tenant(a["tenant"].id):
        assert AuditLog.objects.filter(action="assessment.recorded").count() == 2
        assert AuditLog.objects.filter(action="plan.override").exists()


def test_quran_api_is_read_only_and_attributed(tenants):
    ca = client_for(tenants["a"]["accounts"]["owner"], "alpha")
    r = ca.get("/api/v1/quran/hafs_asim/ayah/1:1")
    assert r.status_code == 200 and r.json()["text_uthmani"].startswith("بِسْمِ") and "Tanzil" in r.json()["attribution"]
    assert r["X-Quran-Core-Version"]
    page = ca.get("/api/v1/quran/hafs_asim/page/604").json()
    assert [a["key"] for a in page["ayat"]][0] == "112:1" and page["surah_starts"] == ["112:1", "113:1", "114:1"]
    with context.platform_admin("test"):
        with connection.cursor() as cur:
            with pytest.raises(Exception):
                cur.execute("INSERT INTO quran_unit (riwayah, unit_type, number, first_ayah_index, last_ayah_index) VALUES ('x','x',1,1,1)")
