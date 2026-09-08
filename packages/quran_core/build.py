"""Deterministic Quran Core build from verified sources.

Sources (see LICENSE-DATA.md):
  - Tanzil Uthmani text (quran-uthmani.txt): verbatim copies permitted with attribution and
    link to tanzil.net; CHANGING THE TEXT IS NOT ALLOWED. We never modify it.
  - Tanzil metadata (quran-data.xml, CC-BY): surahs, juz, hizb quarters, Madani pages, sajdas.

Output: packages/quran_core/data/hafs_asim/*.json(l), snapshots/ayah_sha256.txt, manifest.json.
The build is byte-reproducible for identical inputs.

Usage: python -m packages.quran_core.build <quran-uthmani.txt> <quran-data.xml>
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "hafs_asim"
SNAP = HERE / "data" / "snapshots"
RIWAYAH = "hafs_asim"


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read_text(path: Path) -> list[tuple[int, int, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        s, a, text = line.split("|", 2)
        rows.append((int(s), int(a), text))
    return rows


def build(text_path: Path, meta_path: Path) -> dict:
    rows = read_text(text_path)
    assert len(rows) == 6236, f"expected 6236 ayat, got {len(rows)}"

    root = ET.parse(meta_path).getroot()
    surahs = []
    for el in root.find("suras"):
        surahs.append({
            "number": int(el.get("index")),
            "ayah_count": int(el.get("ayas")),
            "start_index": int(el.get("start")) + 1,  # 1-based global ayah index
            "name_ar": el.get("name"),
            "name_tr": el.get("tname"),
            "name_en": el.get("ename"),
            "revelation": el.get("type").lower(),
            "revelation_order": int(el.get("order")),
            "rukus": int(el.get("rukus")),
        })
    assert len(surahs) == 114
    by_surah = {s["number"]: s for s in surahs}

    ayat = []
    idx = 0
    for s, a, text in rows:
        idx += 1
        assert by_surah[s]["start_index"] + a - 1 == idx, f"index mismatch at {s}:{a}"
        words = text.split(" ")
        ayat.append({
            "ayah_index": idx,
            "surah": s,
            "ayah": a,
            "key": f"{s}:{a}",
            "text_uthmani": text,
            "word_count": len(words),
            "sha256": sha256(text),
        })
    for s in surahs:
        assert sum(1 for x in ayat if x["surah"] == s["number"]) == s["ayah_count"]

    def ayah_index(surah: int, ayah: int) -> int:
        return by_surah[surah]["start_index"] + ayah - 1

    def ranges(tag: str, unit_type: str) -> list[dict]:
        els = list(root.find(tag))
        out = []
        for i, el in enumerate(els):
            first = ayah_index(int(el.get("sura")), int(el.get("aya")))
            if i + 1 < len(els):
                nxt = els[i + 1]
                last = ayah_index(int(nxt.get("sura")), int(nxt.get("aya"))) - 1
            else:
                last = 6236
            out.append({"unit_type": unit_type, "number": int(el.get("index")),
                        "first_ayah_index": first, "last_ayah_index": last})
        return out

    juzs = ranges("juzs", "juz")
    quarters = ranges("hizbs", "rub")  # Tanzil "hizbs" = 240 hizb quarters
    assert len(juzs) == 30 and len(quarters) == 240
    hizbs = []
    for h in range(60):
        q = quarters[h * 4: h * 4 + 4]
        hizbs.append({"unit_type": "hizb", "number": h + 1,
                      "first_ayah_index": q[0]["first_ayah_index"], "last_ayah_index": q[-1]["last_ayah_index"]})
    manzils = ranges("manzils", "manzil")
    assert len(manzils) == 7

    pages = ranges("pages", "page")
    assert len(pages) == 604
    page_rows = []
    for p in pages:
        first = ayat[p["first_ayah_index"] - 1]
        juz = next(j["number"] for j in juzs if j["first_ayah_index"] <= p["first_ayah_index"] <= j["last_ayah_index"])
        page_rows.append({"page": p["number"], "first_ayah_index": p["first_ayah_index"],
                          "last_ayah_index": p["last_ayah_index"], "first_key": first["key"], "juz": juz})

    sajdas = []
    for el in root.find("sajdas"):
        sajdas.append({"ayah_index": ayah_index(int(el.get("sura")), int(el.get("aya"))),
                       "marker_type": "sajdah", "value": el.get("type")})
    assert len(sajdas) == 15

    DATA.mkdir(parents=True, exist_ok=True)
    SNAP.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj) -> str:
        p = DATA / name
        if name.endswith(".jsonl"):
            body = "".join(json.dumps(o, ensure_ascii=False, sort_keys=True) + "\n" for o in obj)
        else:
            body = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
        p.write_text(body, encoding="utf-8")
        return sha256(body)

    files = {
        "surahs.json": dump("surahs.json", surahs),
        "ayat.jsonl": dump("ayat.jsonl", ayat),
        "units.json": dump("units.json", juzs + hizbs + quarters + manzils),
        "pages.json": dump("pages.json", page_rows),
        "markers.json": dump("markers.json", sajdas),
    }
    snapshot = "".join(f"{a['ayah_index']:04d} {a['key']:>7} {a['sha256']}\n" for a in ayat)
    (SNAP / f"{RIWAYAH}_ayah_sha256.txt").write_text(snapshot, encoding="utf-8")
    text_root = sha256("".join(a["sha256"] for a in ayat))

    manifest = {
        "schema": "talaqqi.quran-core/1",
        "riwayat": {
            RIWAYAH: {
                "reader": "ʿĀṣim ibn Abī al-Najūd", "transmitter": "Ḥafṣ ibn Sulaymān",
                "available": True, "ayah_count": 6236, "surah_count": 114, "page_layout": "madani_604",
                "text_root_sha256": text_root,
                "files": {f"hafs_asim/{k}": v for k, v in files.items()},
            }
        },
        "sources": [
            {"name": "Tanzil Quran Text (Uthmani)", "url": "https://tanzil.net/download/",
             "license": "Tanzil terms: verbatim copies only, attribution and link required, no modification",
             "sha256": sha256(text_path.read_text(encoding="utf-8"))},
            {"name": "Tanzil Quran Metadata", "url": "https://tanzil.net/res/text/metadata/quran-data.xml",
             "license": "CC-BY (Tanzil.info)", "sha256": sha256(meta_path.read_text(encoding="utf-8"))},
        ],
        "reviewers": [],
        "built_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "0.1.0",
    }
    (HERE / "data" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    m = build(Path(sys.argv[1]), Path(sys.argv[2]))
    print("built quran-core", m["version"], "text_root", m["riwayat"][RIWAYAH]["text_root_sha256"][:16])
