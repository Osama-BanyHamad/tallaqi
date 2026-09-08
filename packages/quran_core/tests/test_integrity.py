"""Quran Core integrity tests. These MUST fail if a single character of Quran text changes
without an intentional, reviewed release (manifest + snapshot updated together)."""
import hashlib
import json

import pytest

from packages.quran_core import DATA_DIR, QuranCore, QuranCoreIntegrityError, get_core

SNAPSHOT = DATA_DIR / "snapshots" / "hafs_asim_ayah_sha256.txt"


@pytest.fixture(scope="module")
def core() -> QuranCore:
    return get_core("hafs_asim")


def test_counts(core):
    assert core.ayah_count == 6236
    assert len(core.surahs) == 114
    assert len(core.pages) == 604
    assert len(core.units_of("juz")) == 30
    assert len(core.units_of("hizb")) == 60
    assert len(core.units_of("rub")) == 240
    assert len(core.units_of("manzil")) == 7
    assert len(core.markers) == 15


def test_surah_ayah_counts(core):
    for s in core.surahs:
        assert sum(1 for a in core.ayat if a.surah == s.number) == s.ayah_count
    assert core.surah(2).ayah_count == 286 and core.surah(114).ayah_count == 6


def test_indices_are_contiguous(core):
    for i, a in enumerate(core.ayat, start=1):
        assert a.ayah_index == i
    for name in ("juz", "hizb", "rub", "manzil"):
        units = core.units_of(name)
        assert units[0].first_ayah_index == 1 and units[-1].last_ayah_index == 6236
        for u, v in zip(units, units[1:]):
            assert v.first_ayah_index == u.last_ayah_index + 1
    assert core.pages[0].first_ayah_index == 1 and core.pages[-1].last_ayah_index == 6236
    for p, q in zip(core.pages, core.pages[1:]):
        assert q.first_ayah_index == p.last_ayah_index + 1


def test_every_ayah_matches_committed_snapshot(core):
    """Golden snapshot: any textual change fails here unless the snapshot was deliberately regenerated."""
    lines = SNAPSHOT.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6236
    for a, line in zip(core.ayat, lines):
        idx, key, digest = line.split()
        assert int(idx) == a.ayah_index and key == a.key
        assert hashlib.sha256(a.text_uthmani.encode("utf-8")).hexdigest() == digest == a.sha256


def test_manifest_matches_files(core):
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    meta = manifest["riwayat"]["hafs_asim"]
    for rel, expected in meta["files"].items():
        body = (DATA_DIR / rel).read_text(encoding="utf-8")
        assert hashlib.sha256(body.encode("utf-8")).hexdigest() == expected, rel
    root = hashlib.sha256("".join(a.sha256 for a in core.ayat).encode()).hexdigest()
    assert root == meta["text_root_sha256"]


def test_tampering_is_detected(tmp_path, monkeypatch):
    """Simulate a modified ayat file: loading must refuse."""
    import shutil

    import packages.quran_core as qc
    fake = tmp_path / "data"
    shutil.copytree(DATA_DIR, fake)
    p = fake / "hafs_asim" / "ayat.jsonl"
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("ٱلْحَمْدُ", "الحمد", 1), encoding="utf-8")
    monkeypatch.setattr(qc, "DATA_DIR", fake)
    with pytest.raises(QuranCoreIntegrityError):
        QuranCore("hafs_asim")


def test_known_ayat(core):
    assert core.ayah("1:1").text_uthmani.startswith("بِسْمِ")
    # Tanzil prefixes the Basmalah to the first Ayah of each Surah (except 1 and 9); kept verbatim.
    assert core.ayah("112:1").text_uthmani.startswith("بِسْمِ") and core.ayah("112:1").text_uthmani.endswith("أَحَدٌ")
    assert not core.ayah("9:1").text_uthmani.startswith("بِسْمِ")   # At-Tawbah has no Basmalah
    assert core.page_of(core.ayah("2:255").ayah_index) == 42
    assert core.juz_of(core.ayah("78:1").ayah_index) == 30
    assert core.page(1).first_key == "1:1" and core.page(604).first_key == "112:1"
