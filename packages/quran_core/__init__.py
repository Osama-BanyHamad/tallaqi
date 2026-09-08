"""Quran Core: read-only, versioned, checksummed access to verified Quran text and structure.

This package has NO write API. Application services and AI components may only read.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


class QuranCoreIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class Ayah:
    ayah_index: int
    surah: int
    ayah: int
    key: str
    text_uthmani: str
    word_count: int
    sha256: str


@dataclass(frozen=True)
class Surah:
    number: int
    ayah_count: int
    start_index: int
    name_ar: str
    name_tr: str
    name_en: str
    revelation: str
    revelation_order: int
    rukus: int


@dataclass(frozen=True)
class Unit:
    unit_type: str
    number: int
    first_ayah_index: int
    last_ayah_index: int


@dataclass(frozen=True)
class Page:
    page: int
    first_ayah_index: int
    last_ayah_index: int
    first_key: str
    juz: int


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class QuranCore:
    """In-memory accessor for one Riwayah. Verifies checksums on load; refuses to start on mismatch."""

    def __init__(self, riwayah: str = "hafs_asim", verify: bool = True):
        self.riwayah = riwayah
        self.manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
        if riwayah not in self.manifest["riwayat"]:
            raise QuranCoreIntegrityError(f"riwayah {riwayah} not in manifest")
        meta = self.manifest["riwayat"][riwayah]
        d = DATA_DIR / riwayah
        if verify:
            for rel, expected in meta["files"].items():
                body = (DATA_DIR / rel).read_text(encoding="utf-8")
                if _sha(body) != expected:
                    raise QuranCoreIntegrityError(f"checksum mismatch for {rel}")
        self.surahs: list[Surah] = [Surah(**s) for s in json.loads((d / "surahs.json").read_text(encoding="utf-8"))]
        self.ayat: list[Ayah] = [Ayah(**json.loads(line)) for line in (d / "ayat.jsonl").read_text(encoding="utf-8").splitlines()]
        self.units: list[Unit] = [Unit(**u) for u in json.loads((d / "units.json").read_text(encoding="utf-8"))]
        self.pages: list[Page] = [Page(**p) for p in json.loads((d / "pages.json").read_text(encoding="utf-8"))]
        self.markers: list[dict] = json.loads((d / "markers.json").read_text(encoding="utf-8"))
        if verify:
            root = _sha("".join(a.sha256 for a in self.ayat))
            if root != meta["text_root_sha256"]:
                raise QuranCoreIntegrityError("text root checksum mismatch")
            for a in self.ayat:
                if _sha(a.text_uthmani) != a.sha256:
                    raise QuranCoreIntegrityError(f"ayah {a.key} checksum mismatch")
        self._by_key = {a.key: a for a in self.ayat}
        self._surah_by_no = {s.number: s for s in self.surahs}
        self._page_by_no = {p.page: p for p in self.pages}
        self._page_of_index = [0] * (len(self.ayat) + 2)
        for p in self.pages:
            for i in range(p.first_ayah_index, p.last_ayah_index + 1):
                self._page_of_index[i] = p.page
        self._juz_of_index = [0] * (len(self.ayat) + 2)
        for u in self.units:
            if u.unit_type == "juz":
                for i in range(u.first_ayah_index, u.last_ayah_index + 1):
                    self._juz_of_index[i] = u.number

    # ---- lookups -------------------------------------------------------
    @property
    def ayah_count(self) -> int:
        return len(self.ayat)

    def ayah_by_index(self, ayah_index: int) -> Ayah:
        return self.ayat[ayah_index - 1]

    def ayah(self, key: str) -> Ayah:
        return self._by_key[key]

    def surah(self, number: int) -> Surah:
        return self._surah_by_no[number]

    def page(self, number: int) -> Page:
        return self._page_by_no[number]

    def page_of(self, ayah_index: int) -> int:
        return self._page_of_index[ayah_index]

    def juz_of(self, ayah_index: int) -> int:
        return self._juz_of_index[ayah_index]

    def range(self, first: int, last: int) -> list[Ayah]:
        return self.ayat[first - 1: last]

    def units_of(self, unit_type: str) -> list[Unit]:
        return [u for u in self.units if u.unit_type == unit_type]

    def unit(self, unit_type: str, number: int) -> Unit:
        return next(u for u in self.units if u.unit_type == unit_type and u.number == number)

    def page_ayat(self, page: int) -> list[Ayah]:
        p = self.page(page)
        return self.range(p.first_ayah_index, p.last_ayah_index)


@lru_cache(maxsize=4)
def get_core(riwayah: str = "hafs_asim") -> QuranCore:
    return QuranCore(riwayah)
