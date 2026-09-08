"""Finance module: fee plans, invoice generation, payments, overdue, isolation, capability gating."""
# ruff: noqa: F811  (the `tenants` fixture is imported from the shared conftest and then used as a parameter)
from datetime import date, timedelta
from decimal import Decimal

import pytest

from services.common import context
from services.people.models import Guardian, GuardianLink, Person
from tests.conftest import client_for, tenants  # noqa: F401  (fixture reused from the shared conftest)

pytestmark = pytest.mark.django_db

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=20)).isoformat()


def enable_finance(owner_client, payments=True):
    for key in ("finance.fees", "finance.invoicing") + (("finance.payments",) if payments else ()):
        r = owner_client.put("/api/v1/tenant/modules", {"key": key, "enabled": True}, format="json")
        assert r.status_code == 200, r.content


def make_plan(c, **kw):
    body = {"name": "رسوم شهرية", "cadence": "monthly", "amount": "100.000", "sibling_discount_pct": "10", **kw}
    r = c.post("/api/v1/finance/fee-plans", body, format="json")
    assert r.status_code == 201, r.content
    return r.json()


def assign(c, student, plan_id, **kw):
    body = {"student": str(student.id), "plan": plan_id, "start_date": "2026-01-01", **kw}
    r = c.post("/api/v1/finance/student-plans", body, format="json")
    assert r.status_code == 201, r.content
    return r.json()


def issue(c, sp_id, period="2026-09", **kw):
    r = c.post(f"/api/v1/finance/student-plans/{sp_id}/invoice", {"period_label": period, "due_on": FUTURE, **kw}, format="json")
    assert r.status_code == 201, r.content
    return r.json()


@pytest.fixture
def fin(tenants):
    a = tenants["a"]
    owner = client_for(a["accounts"]["owner"], "alpha")
    enable_finance(owner)
    return {"t": a, "owner": owner, "finance": client_for(a["accounts"]["finance"], "alpha")}


def test_fee_plan_crud(fin):
    c = fin["finance"]
    p = make_plan(c, branch=str(fin["t"]["branches"][0].id))
    assert p["currency"] == "JOD" and p["branch_name"].startswith("مركز ألفا")
    assert c.get("/api/v1/finance/fee-plans").json()["count"] == 1
    r = c.patch(f"/api/v1/finance/fee-plans/{p['id']}", {"amount": "120.500", "is_active": False}, format="json")
    assert r.status_code == 200 and r.json()["amount"] == "120.500" and r.json()["is_active"] is False
    assert c.get(f"/api/v1/finance/fee-plans/{p['id']}").json()["amount"] == "120.500"
    assert c.delete(f"/api/v1/finance/fee-plans/{p['id']}").status_code == 204
    assert c.get("/api/v1/finance/fee-plans").json()["count"] == 0
    # validation: percentage out of range
    r = c.post("/api/v1/finance/fee-plans", {"name": "x", "amount": "1", "sibling_discount_pct": "150"}, format="json")
    assert r.status_code == 400


def test_invoice_generation_from_plan(fin):
    c = fin["finance"]
    s1 = fin["t"]["students"][0]
    plan = make_plan(c)
    sp = assign(c, s1, plan["id"], discount_pct="10", scholarship_pct="25", scholarship_note="أيتام")
    assert sp["student_name"] == s1.person.display_name_ar and sp["plan_amount"] == "100.000"
    inv = issue(c, sp["id"])
    assert inv["number"] == "INV-000001" and inv["status"] == "issued" and inv["period_label"] == "2026-09"
    assert inv["payer_name"] == s1.person.display_name_ar   # no guardian → student is the payer
    kinds = {ln["kind"]: Decimal(ln["amount"]) for ln in inv["lines"]}
    assert kinds == {"fee": Decimal("100.000"), "discount": Decimal("10.000"), "scholarship": Decimal("25.000")}
    assert inv["subtotal"] == "100.000" and inv["discount_total"] == "35.000" and inv["total"] == "65.000" and inv["outstanding"] == "65.000"
    # same period twice is rejected
    r = c.post(f"/api/v1/finance/student-plans/{sp['id']}/invoice", {"period_label": "2026-09"}, format="json")
    assert r.status_code == 422 and r.json()["code"] == "domain_error"
    # detail carries lines and (empty) payments; list filter by student and period
    d = c.get(f"/api/v1/finance/invoices/{inv['id']}").json()
    assert len(d["lines"]) == 3 and d["payments"] == []
    assert c.get(f"/api/v1/finance/invoices?student={s1.id}&period_label=2026-09").json()["count"] == 1
    assert c.get("/api/v1/finance/invoices?search=INV-000001").json()["count"] == 1
    # audit trail
    from services.audit.models import AuditLog
    with context.tenant(fin["t"]["tenant"].id):
        assert AuditLog.objects.filter(action="invoice.issued", object_id=inv["id"]).exists()


def test_sibling_discount_and_bulk_monthly_generation(fin):
    c = fin["finance"]
    t = fin["t"]
    s1, s2 = t["students"]
    with context.tenant(t["tenant"].id):
        g = Guardian.objects.create(person=Person.objects.create(first_name="أبو", display_name_ar="أبو أحمد"))
        GuardianLink.objects.create(guardian=g, student=s1, primary=True)
        GuardianLink.objects.create(guardian=g, student=s2, primary=True)
    plan = make_plan(c, sibling_discount_pct="10")
    assign(c, s1, plan["id"])
    assign(c, s2, plan["id"])
    r = c.post("/api/v1/finance/invoices/generate", {"period_label": "2026-10"}, format="json")
    assert r.status_code == 201 and r.json()["created"] == 2
    invs = r.json()["invoices"]
    assert all(i["payer_name"] == "أبو أحمد" for i in invs)
    assert all(i["total"] == "90.000" and i["discount_total"] == "10.000" for i in invs)
    assert {i["number"] for i in invs} == {"INV-000001", "INV-000002"}
    # idempotent
    r = c.post("/api/v1/finance/invoices/generate", {"period_label": "2026-10"}, format="json")
    assert r.status_code == 200 and r.json()["created"] == 0
    assert c.get("/api/v1/finance/invoices?period_label=2026-10").json()["count"] == 2
    # bad period label
    assert c.post("/api/v1/finance/invoices/generate", {"period_label": "Sept"}, format="json").status_code == 422
    # management command is also idempotent and scoped to tenants with invoicing enabled
    from django.core.management import call_command
    call_command("generate_invoices", period="2026-10")
    call_command("generate_invoices", period="2026-11", tenant="alpha")
    assert c.get("/api/v1/finance/invoices?period_label=2026-10").json()["count"] == 2
    assert c.get("/api/v1/finance/invoices?period_label=2026-11").json()["count"] == 2


def test_full_payment_settles_invoice(fin):
    c = fin["finance"]
    plan = make_plan(c)
    sp = assign(c, fin["t"]["students"][0], plan["id"])
    inv = issue(c, sp["id"])
    r = c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "100.000", "method": "cash", "note": "دفع كامل"}, format="json")
    assert r.status_code == 201, r.content
    p = r.json()
    assert p["receipt_number"] == "RCPT-000001" and p["status"] == "posted" and p["currency"] == "JOD"
    d = c.get(f"/api/v1/finance/invoices/{inv['id']}").json()
    assert d["status"] == "paid" and d["paid_total"] == "100.000" and d["outstanding"] == "0.000"
    assert d["payments"][0]["receipt_number"] == "RCPT-000001"
    # cannot overpay / pay a settled invoice
    r = c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "1"}, format="json")
    assert r.status_code == 422
    # cannot void a paid invoice
    r = c.post(f"/api/v1/finance/invoices/{inv['id']}/void", {"reason": "x"}, format="json")
    assert r.status_code == 422
    # refund reopens it
    r = c.post(f"/api/v1/finance/payments/{p['id']}/refund", {"reason": "خطأ في الإدخال"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "refunded" and r.json()["refund_reason"] == "خطأ في الإدخال"
    d = c.get(f"/api/v1/finance/invoices/{inv['id']}").json()
    assert d["status"] == "issued" and d["paid_total"] == "0.000"
    # refund twice is rejected; now voiding works
    assert c.post(f"/api/v1/finance/payments/{p['id']}/refund", {"reason": "x"}, format="json").status_code == 422
    r = c.post(f"/api/v1/finance/invoices/{inv['id']}/void", {"reason": "أُلغي الاشتراك"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "void"
    assert c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "1"}, format="json").status_code == 422


def test_partial_payment_and_validation(fin):
    c = fin["finance"]
    plan = make_plan(c)
    sp = assign(c, fin["t"]["students"][0], plan["id"])
    inv = issue(c, sp["id"])
    r = c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "40.250", "method": "bank_transfer", "reference": "TRX-9"}, format="json")
    assert r.status_code == 201
    d = c.get(f"/api/v1/finance/invoices/{inv['id']}").json()
    assert d["status"] == "partially_paid" and d["paid_total"] == "40.250" and d["outstanding"] == "59.750"
    for bad in ("0", "-5", "59.751"):
        assert c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": bad}, format="json").status_code in (400, 422)
    r = c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "59.750"}, format="json")
    assert r.status_code == 201 and r.json()["receipt_number"] == "RCPT-000002"
    assert c.get(f"/api/v1/finance/invoices/{inv['id']}").json()["status"] == "paid"
    assert c.get(f"/api/v1/finance/payments?invoice={inv['id']}").json()["count"] == 2
    assert c.get(f"/api/v1/finance/payments?invoice__student={fin['t']['students'][0].id}").json()["count"] == 2
    assert c.get(f"/api/v1/finance/payments?invoice__student={fin['t']['students'][1].id}").json()["count"] == 0


def test_overdue_listing_and_summary(fin):
    c = fin["finance"]
    s1, s2 = fin["t"]["students"]
    plan = make_plan(c)
    sp1, sp2 = assign(c, s1, plan["id"]), assign(c, s2, plan["id"])
    past = (TODAY - timedelta(days=30)).isoformat()
    late = c.post(f"/api/v1/finance/student-plans/{sp1['id']}/invoice", {"period_label": "2026-08", "issued_on": past, "due_on": past}, format="json").json()
    assert late["status"] == "issued"       # generation never marks overdue by itself
    ok = issue(c, sp2["id"])
    c.post("/api/v1/finance/payments", {"invoice": ok["id"], "amount": "30"}, format="json")
    r = c.get("/api/v1/finance/invoices?status=overdue")
    assert r.status_code == 200 and [i["number"] for i in r.json()["results"]] == [late["number"]]
    assert c.get("/api/v1/finance/invoices?open=1").json()["count"] == 2
    assert c.get("/api/v1/finance/invoices?ordering=due_on").json()["results"][0]["number"] == late["number"]
    s = c.get("/api/v1/finance/invoices/summary").json()
    assert s["issued_total"] == "200.000" and s["paid_total"] == "30.000" and s["outstanding_total"] == "170.000"
    assert s["overdue_count"] == 1 and s["by_status"]["overdue"] == 1 and s["by_status"]["partially_paid"] == 1
    # paying the overdue invoice in full settles it
    c.post("/api/v1/finance/payments", {"invoice": late["id"], "amount": "100"}, format="json")
    assert c.get(f"/api/v1/finance/invoices/{late['id']}").json()["status"] == "paid"
    from django.core.management import call_command
    call_command("mark_overdue_invoices")


def test_tenant_isolation_and_idor(tenants):
    a, b = tenants["a"], tenants["b"]
    oa, ob = client_for(a["accounts"]["owner"], "alpha"), client_for(b["accounts"]["owner"], "beta")
    enable_finance(oa)
    enable_finance(ob)
    fa, fb = client_for(a["accounts"]["finance"], "alpha"), client_for(b["accounts"]["finance"], "beta")
    pa, pb = make_plan(fa), make_plan(fb, name="رسوم بيتا")
    spa, spb = assign(fa, a["students"][0], pa["id"]), assign(fb, b["students"][0], pb["id"])
    ia, ib = issue(fa, spa["id"]), issue(fb, spb["id"])
    assert ia["number"] == ib["number"] == "INV-000001"    # sequences are per tenant
    assert {i["id"] for i in fa.get("/api/v1/finance/invoices").json()["results"]} == {ia["id"]}
    assert {p["id"] for p in fa.get("/api/v1/finance/fee-plans").json()["results"]} == {pa["id"]}
    assert fa.get("/api/v1/finance/invoices?search=بيتا").json()["count"] == 0
    # IDOR: alpha cannot read, pay, or void beta's invoice; cannot assign beta's student or plan
    assert fa.get(f"/api/v1/finance/invoices/{ib['id']}").status_code == 404
    assert fa.post(f"/api/v1/finance/invoices/{ib['id']}/void", {"reason": "x"}, format="json").status_code == 404
    assert fa.post("/api/v1/finance/payments", {"invoice": ib["id"], "amount": "1"}, format="json").status_code == 404
    assert fa.get(f"/api/v1/finance/student-plans/{spb['id']}").status_code == 404
    r = fa.post("/api/v1/finance/student-plans", {"student": str(b["students"][0].id), "plan": pa["id"], "start_date": "2026-01-01"}, format="json")
    assert r.status_code == 400
    r = fa.post("/api/v1/finance/student-plans", {"student": str(a["students"][1].id), "plan": pb["id"], "start_date": "2026-01-01"}, format="json")
    assert r.status_code == 400
    pay = fb.post("/api/v1/finance/payments", {"invoice": ib["id"], "amount": "5"}, format="json").json()
    assert fa.get(f"/api/v1/finance/payments/{pay['id']}").status_code == 404
    assert fa.post(f"/api/v1/finance/payments/{pay['id']}/refund", {"reason": "x"}, format="json").status_code == 404
    with context.tenant(b["tenant"].id):
        from services.finance.models import Invoice
        assert Invoice.objects.get(pk=ib["id"]).status == "partially_paid"


def test_teacher_and_supervisor_forbidden(fin):
    t = fin["t"]
    for who in ("teacher", "supervisor"):
        c = client_for(t["accounts"][who], "alpha")
        for path in ("/api/v1/finance/fee-plans", "/api/v1/finance/student-plans", "/api/v1/finance/invoices",
                     "/api/v1/finance/invoices/summary", "/api/v1/finance/payments"):
            r = c.get(path)
            assert r.status_code == 403 and r.json()["code"] == "permission_denied", (who, path, r.content)
        assert c.post("/api/v1/finance/fee-plans", {"name": "x", "amount": "1"}, format="json").status_code == 403
    # the finance role never receives hifz permissions
    caps = fin["finance"].get("/api/v1/me/capabilities").json()
    assert not any(p.startswith("hifz.") for p in caps["permissions"])
    assert {"finance.payments.read", "finance.payments.record", "finance.payments.refund"} <= set(caps["permissions"])


def test_disabling_payments_module_returns_capability_disabled(fin):
    c, owner = fin["finance"], fin["owner"]
    plan = make_plan(c)
    sp = assign(c, fin["t"]["students"][0], plan["id"])
    inv = issue(c, sp["id"])
    assert c.get("/api/v1/finance/payments").status_code == 200
    r = owner.put("/api/v1/tenant/modules", {"key": "finance.payments", "enabled": False}, format="json")
    assert r.status_code == 200
    r = c.get("/api/v1/finance/payments")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"
    r = c.post("/api/v1/finance/payments", {"invoice": inv["id"], "amount": "1"}, format="json")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"
    # invoicing still works; dependents block disabling fees
    assert c.get("/api/v1/finance/invoices").status_code == 200
    assert owner.put("/api/v1/tenant/modules", {"key": "finance.fees", "enabled": False}, format="json").status_code == 422


def test_finance_modules_disabled_by_default(tenants):
    c = client_for(tenants["a"]["accounts"]["finance"], "alpha")
    r = c.get("/api/v1/finance/fee-plans")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"
