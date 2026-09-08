"""Endpoints added while completing the MVP: student create with guardian/halaqah, self-scoped student access,
guardians, attendance history, staff halaqah sync, accounts invite/revoke, reports (+CSV), audit read."""
from __future__ import annotations

import pytest

from services.common import context
from services.identity.models import Account
from services.rbac.services import assign, ensure_system_roles
from services.tenants.models import Membership
from tests.conftest import client_for

pytestmark = pytest.mark.django_db


def _student_client(tenants):
    """A student login whose membership points at student 1's person, scope=self."""
    a = tenants["a"]
    t, s1 = a["tenant"], a["students"][0]
    with context.tenant(t.id):
        roles = ensure_system_roles(t)
        acc = Account.objects.create_user(email="student@alpha.test", password="Passw0rd!Test", full_name="s")
        m = Membership.objects.create(account=acc, tenant=t, person=s1.person)
        assign(m, roles["student"], "self", [])
    return client_for(acc, "alpha"), s1


def test_student_self_scope_sees_only_own_journey_and_plan(tenants):
    c, s1 = _student_client(tenants)
    listed = c.get("/api/v1/journeys?page_size=10").json()
    assert [j["student"] for j in listed["results"]] == [str(s1.id)]
    jid = listed["results"][0]["id"]
    assert c.get(f"/api/v1/journeys/{jid}").status_code == 200, "self scope must pass the object-level check"
    assert c.get(f"/api/v1/journeys/{jid}/plan").status_code == 200
    other = tenants["a"]["students"][1]
    with context.tenant(tenants["a"]["tenant"].id):
        other_jid = other.journey.id
    assert c.get(f"/api/v1/journeys/{other_jid}").status_code == 404
    assert c.get("/api/v1/students").status_code == 403  # students never list the roster


def test_create_student_with_halaqah_and_guardian_then_manage(tenants):
    a = tenants["a"]
    c = client_for(a["accounts"]["owner"], "alpha")
    b1, h1 = a["branches"][0], a["halaqat"][0]
    r = c.post("/api/v1/students", {"person": {"first_name": "سفيان", "last_name": "الطراونة", "gender": "male"}, "branch": str(b1.id),
                                    "halaqah_id": str(h1.id), "guardian": {"display_name_ar": "خالد الطراونة", "phone": "0791"}}, format="json")
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["person"]["display_name_ar"] == "سفيان الطراونة"  # derived from first/last
    assert body["student_code"].startswith("S") and body["halaqah"]["id"] == str(h1.id)
    sid = body["id"]
    g = c.get(f"/api/v1/students/{sid}/guardians").json()
    assert [x["name"] for x in g] == ["خالد الطراونة"] and g[0]["primary"] is True
    assert c.post(f"/api/v1/students/{sid}/guardians", {"display_name_ar": "أم سفيان", "relationship": "mother"}, format="json").status_code in (200, 201)
    assert len(c.get(f"/api/v1/students/{sid}/guardians").json()) == 2
    # move to the second halaqah via PATCH halaqah_id
    h2 = a["halaqat"][1]
    r = c.patch(f"/api/v1/students/{sid}", {"halaqah_id": str(h2.id)}, format="json")
    assert r.status_code == 200 and r.json()["halaqah"]["id"] == str(h2.id)
    att = c.get(f"/api/v1/students/{sid}/attendance?days=30").json()
    assert att["records"] == [] and att["counts"] == {}
    # a teacher scoped to h1 cannot create students
    assert client_for(a["accounts"]["teacher"], "alpha").post("/api/v1/students", {"person": {"first_name": "x"}, "branch": str(b1.id)}, format="json").status_code == 403


def test_staff_halaqah_sync_and_halaqah_teacher_id(tenants):
    a = tenants["a"]
    c = client_for(a["accounts"]["owner"], "alpha")
    h1, h2 = a["halaqat"]
    r = c.post("/api/v1/staff", {"person": {"first_name": "معلم", "last_name": "جديد"}, "staff_type": "teacher", "halaqah_ids": [str(h1.id), str(h2.id)]}, format="json")
    assert r.status_code == 201, r.content
    staff_id = r.json()["id"]
    assert {h["id"] for h in r.json()["halaqat"]} == {str(h1.id), str(h2.id)}
    r = c.patch(f"/api/v1/staff/{staff_id}", {"halaqah_ids": [str(h2.id)]}, format="json")
    assert [h["id"] for h in r.json()["halaqat"]] == [str(h2.id)]
    r = c.patch(f"/api/v1/halaqat/{h1.id}", {"teacher_id": staff_id}, format="json")
    assert r.status_code == 200 and [t["id"] for t in r.json()["teachers"]] == [staff_id]
    matrix = c.get(f"/api/v1/halaqat/{h1.id}/attendance-history?days=7").json()
    assert matrix["dates"] == [] and matrix["students"][0]["name"]  # dates list only days that have records


def test_accounts_invite_revoke_and_privilege_ceiling(tenants):
    a = tenants["a"]
    owner = client_for(a["accounts"]["owner"], "alpha")
    h1 = a["halaqat"][0]
    r = owner.post("/api/v1/accounts", {"email": "new.teacher@alpha.test", "full_name": "معلمة", "role_key": "teacher", "scope_type": "halaqah", "scope_refs": [str(h1.id)]}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["generated_password"] and r.json()["email"] == "new.teacher@alpha.test"
    rows = owner.get("/api/v1/accounts").json()
    me = next(x for x in rows if x["email"] == "new.teacher@alpha.test")
    assert me["assignments"][0]["role"] == "teacher" and me["assignments"][0]["scope_type"] == "halaqah"
    # the new teacher can log in against tenant alpha but cannot invite anyone
    acc = Account.objects.get(email="new.teacher@alpha.test")
    tc = client_for(acc, "alpha")
    assert tc.get("/api/v1/me/capabilities").status_code == 200
    assert tc.post("/api/v1/accounts", {"email": "x@alpha.test", "full_name": "x", "role_key": "owner"}, format="json").status_code == 403
    # finance (has rbac.read? no) cannot list accounts; supervisor cannot grant owner
    sup = client_for(a["accounts"]["supervisor"], "alpha")
    r = sup.post("/api/v1/accounts", {"email": "y@alpha.test", "full_name": "y", "role_key": "owner"}, format="json")
    assert r.status_code in (400, 403)
    assert owner.post(f"/api/v1/accounts/{me['assignments'][0]['id']}/revoke", {}, format="json").status_code == 200
    assert not next(x for x in owner.get("/api/v1/accounts").json() if x["email"] == "new.teacher@alpha.test")["assignments"]
    # cross-tenant: beta owner never sees alpha accounts
    assert all(x["email"].endswith("beta.test") for x in client_for(tenants["b"]["accounts"]["owner"], "beta").get("/api/v1/accounts").json())


def test_reports_json_csv_and_audit(tenants):
    a = tenants["a"]
    owner = client_for(a["accounts"]["owner"], "alpha")
    r = owner.get("/api/v1/reports/hifz")
    assert r.status_code == 200 and len(r.json()["students"]) == 2
    r = owner.get("/api/v1/reports/attendance?from=2026-01-01&to=2026-01-31")
    assert r.status_code == 200 and "halaqat" in r.json()
    r = owner.get("/api/v1/reports/students?export=csv")
    assert r.status_code == 200 and r["Content-Type"].startswith("text/csv")
    assert r.content.startswith(b"\xef\xbb\xbf")  # BOM so Excel opens Arabic correctly
    # teacher has no reports permission
    assert client_for(a["accounts"]["teacher"], "alpha").get("/api/v1/reports/hifz").status_code == 403
    # audit: create something, then find it
    owner.post("/api/v1/students", {"person": {"first_name": "مدقق"}, "branch": str(a["branches"][0].id)}, format="json")
    log = owner.get("/api/v1/audit?search=student.created").json()
    assert log["count"] >= 1 and log["results"][0]["actor_email"] == "owner@alpha.test"
    assert client_for(a["accounts"]["teacher"], "alpha").get("/api/v1/audit").status_code == 403
