"""Recitation mismatch detection: alignment logic (pure) and the endpoint (fake provider, no network)."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from packages.quran_core import get_core
from services.ai import asr, providers, views
from services.common import context
from services.tenants.models import TenantModule
from tests.conftest import client_for

pytestmark = pytest.mark.django_db


def _range(surah, a1, a2):
    core = get_core()
    return core.ayah(f"{surah}:{a1}").ayah_index, core.ayah(f"{surah}:{a2}").ayah_index


def _plain(from_i, to_i):
    """The verified text of the range, stripped to plain letters — what a perfect transcript looks like."""
    return " ".join(w.norm for w in asr.expected_words(from_i, to_i))


def test_perfect_recitation_has_no_candidates():
    f, t = _range(103, 1, 3)  # Al-Asr
    r = asr.check_recitation(_plain(f, t), f, t)
    assert r["accuracy"] == 1.0 and r["candidates"] == [] and r["expected_words"] == 14
    assert all(a["status"] == "ok" for a in r["ayat"])


def test_omission_substitution_and_addition_are_positioned_on_verified_text():
    f, t = _range(103, 1, 3)
    words = _plain(f, t).split(" ")
    heard = words[:]
    dropped = heard.pop(3)              # omit a word in Ayah 2
    heard[5] = "كلمةغريبة"             # substitute one
    heard.insert(1, "زيادة")           # add a stray word after word 1
    r = asr.check_recitation(" ".join(heard), f, t)
    kinds = {c["kind"] for c in r["candidates"]}
    assert {"omission", "substitution", "addition"} <= kinds
    om = next(c for c in r["candidates"] if c["kind"] == "omission")
    assert om["mistake_type"] == "forgotten_word" and asr.normalize_word(om["expected"]) == dropped and om["word_position"] >= 1
    sw = next(c for c in r["candidates"] if c["kind"] == "substitution")
    assert sw["mistake_type"] == "incorrect_word"
    assert sw["heard"] == asr.normalize_word("كلمةغريبة")
    assert 0.6 < r["accuracy"] < 1.0


def test_basmalah_and_istiadha_before_the_range_are_ignored_and_spelling_noise_is_forgiven():
    f, t = _range(112, 1, 4)  # Al-Ikhlas: Tanzil keeps the basmalah inside Ayah 1; expected words must skip it
    exp = asr.expected_words(f, t)
    assert exp[0].norm == "قل" and exp[0].position == 1
    heard = "اعوذ بالله من الشيطان الرجيم بسم الله الرحمن الرحيم " + _plain(f, t).replace("احد", "أحد")
    r = asr.check_recitation(heard, f, t)
    assert r["accuracy"] == 1.0, r["candidates"]


def _enable(tenant):
    with context.platform_admin("t"):
        for k in ("hifz.asr", "ai.assist"):
            TenantModule.objects.update_or_create(tenant=tenant, module_key=k, defaults={"enabled": True})


def test_asr_endpoint_student_and_teacher(tenants, monkeypatch):
    a = tenants["a"]
    _enable(a["tenant"])
    f, t = _range(103, 1, 3)
    fake = providers.FakeProvider(transcript=_plain(f, t).replace("خسر", "خير"))
    monkeypatch.setattr(views, "get_provider", lambda: fake)
    teacher = client_for(a["accounts"]["teacher"], "alpha")
    audio = SimpleUploadedFile("r.webm", b"\x1a\x45\xdf\xa3" + b"0" * 4000, content_type="audio/webm")
    r = teacher.post("/api/v1/ai/asr-check", {"audio": audio, "from_ayah_index": f, "to_ayah_index": t}, format="multipart")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["safety"] == "YELLOW" and body["disclaimer"] and body["model"] == "fake-asr"
    assert [c["mistake_type"] for c in body["candidates"]] == ["incorrect_word"] and body["candidates"][0]["heard"] == "خير"
    assert fake.audio_calls[0][2] == "audio/webm"
    # validation
    assert teacher.post("/api/v1/ai/asr-check", {"from_ayah_index": f, "to_ayah_index": t}, format="multipart").status_code == 400
    assert teacher.post("/api/v1/ai/asr-check", {"audio": SimpleUploadedFile("r.webm", b"x" * 100), "from_ayah_index": 1, "to_ayah_index": 500}, format="multipart").status_code == 400
    # finance has no hifz.asr.use
    fin = client_for(a["accounts"]["finance"], "alpha")
    assert fin.post("/api/v1/ai/asr-check", {"audio": SimpleUploadedFile("r.webm", b"x" * 3000), "from_ayah_index": f, "to_ayah_index": t}, format="multipart").status_code == 403
    # audited without audio
    log = client_for(a["accounts"]["owner"], "alpha").get("/api/v1/audit?search=ai.asr_check").json()
    assert log["count"] >= 1 and log["results"][0]["after"]["candidates"] == 1


def test_asr_module_disabled_and_null_provider(tenants, settings):
    a = tenants["a"]
    f, t = _range(103, 1, 3)
    teacher = client_for(a["accounts"]["teacher"], "alpha")
    up = lambda: SimpleUploadedFile("r.webm", b"x" * 3000, content_type="audio/webm")  # noqa: E731
    r = teacher.post("/api/v1/ai/asr-check", {"audio": up(), "from_ayah_index": f, "to_ayah_index": t}, format="multipart")
    assert r.status_code == 403 and r.json()["code"] == "capability_disabled"
    _enable(a["tenant"])
    settings.AI_PROVIDER = "null"
    r = teacher.post("/api/v1/ai/asr-check", {"audio": up(), "from_ayah_index": f, "to_ayah_index": t}, format="multipart")
    assert r.status_code == 503 and r.json()["code"] == "ai_unavailable"


def test_multipart_encoder_is_well_formed():
    body, ctype = providers._multipart({"model": "m", "language": "ar"}, "file", "a.webm", "audio/webm", b"\x00\x01")
    boundary = ctype.split("boundary=")[1]
    assert body.count(b"--" + boundary.encode()) == 4 and b'name="file"; filename="a.webm"' in body and body.endswith(b"--\r\n")
    io.BytesIO(body)
