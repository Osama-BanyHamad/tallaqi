"""Daily reading (wird): plan, today's pages, logging advances the position, streak, reciters registry."""
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db(transaction=True)


def _signup(email="reader@example.com"):
    c = APIClient()
    r = c.post("/api/v1/auth/signup", {"full_name": "قارئ", "email": email, "password": "Secret@12345", "goal": "keep", "memorized_juz": [], "daily_minutes": 10}, format="json")
    assert r.status_code == 201, r.content
    j = r.json()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {j['access']}", HTTP_X_TENANT=j["tenant"])
    return c


def test_plan_today_log_and_history():
    c = _signup()
    assert c.get("/api/v1/reading/today").status_code == 404
    r = c.post("/api/v1/reading/plan", {"kind": "khatmah", "target_days": 30, "start_page": 1, "reminder_time": "05:30"}, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["plan"]["pages_per_day"] == 21 and d["today"]["from_page"] == 1 and d["today"]["to_page"] == 21
    assert d["today"]["from_key"] == "1:1" and d["today"]["done"] is False and d["streak"] == 0
    r = c.post("/api/v1/reading/log", {"from_page": 1, "to_page": 21, "minutes": 40}, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["plan"]["current_page"] == 22 and d["today"]["done"] is True and d["streak"] == 1 and d["today"]["from_page"] == 22
    # update the daily amount, position stays
    r = c.patch("/api/v1/reading/plan", {"pages_per_day": 2}, format="json")
    assert r.status_code == 200 and r.json()["pages_per_day"] == 2 and r.json()["current_page"] == 22
    h = c.get("/api/v1/reading/history?days=7").json()
    assert h["days"][0]["pages"] == 21 and h["days"][0]["minutes"] == 40
    # finishing the Mushaf counts a khatmah and wraps
    c.patch("/api/v1/reading/plan", {"current_page": 604}, format="json")
    d = c.post("/api/v1/reading/log", {"from_page": 604, "to_page": 604}, format="json").json()
    assert d["plan"]["khatmat"] == 1 and d["plan"]["current_page"] == 1


def test_reciters_registry():
    c = _signup("r2@example.com")
    r = c.get("/api/v1/quran/reciters")
    assert r.status_code == 200, r.content
    d = r.json()
    assert d["pattern"] == "{surah:03d}{ayah:03d}.mp3" and any(x["key"] == "husary" for x in d["reciters"])
    assert all(x["base"].startswith("https://") for x in d["reciters"])


def test_plans_are_private_per_person():
    a = _signup("a@example.com")
    b = _signup("b@example.com")
    a.post("/api/v1/reading/plan", {"pages_per_day": 3}, format="json")
    assert b.get("/api/v1/reading/today").status_code == 404
