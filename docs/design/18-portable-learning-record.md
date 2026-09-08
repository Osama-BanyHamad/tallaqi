# 18 — Portable Quran Learning Record (QLR) — Initial Open Specification (v0.1)

## 18.1 Purpose

A privacy-aware, signed, JSON document that lets a student carry their Quran learning history between institutions and tools without losing years of data. The record is descriptive (what was learned, assessed, and retained, and by whom it was verified), never authoritative on religious status.

## 18.2 Design rules

1. **Riwayah-explicit**: every Ayah reference carries the Riwayah and the Quran Core version used.
2. **Provenance-explicit**: every claim carries `verified_by` (institution, role) and `verification` (`teacher_verified`, `assessment`, `self_reported`, `imported`).
3. **Privacy tiers**: the exporter chooses what to include; the minimal record contains no assessments or notes.
4. **Signed**: the issuing institution signs the record (Ed25519 over the canonical JSON); verifiers can check against the institution's published key (`/.well-known/qlr.json`).
5. **Versioned schema** (`spec_version`), with JSON Schema published at `https://talaqqi.org/spec/qlr/0.1/schema.json`.
6. **Ayah ranges** use `[from_ayah_index, to_ayah_index]` within the Riwayah, plus human-readable `from`/`to` keys.

## 18.3 Structure

```json
{
  "spec_version": "0.1",
  "record_id": "qlr_01J9…",
  "issued_at": "2026-09-08T10:00:00Z",
  "issuer": {
    "name": "Al-Huda Quran Center",
    "id": "https://alhuda.example/.well-known/qlr.json#inst",
    "country": "JO",
    "platform": "talaqqi/0.5.0"
  },
  "subject": {
    "pseudonymous_id": "sha256:…",
    "display_name": "Y. A.",
    "birth_year": 2015,
    "gender": "male"
  },
  "privacy": {
    "tier": "standard",
    "includes": ["memory_map", "milestones", "assessments"],
    "excludes": ["teacher_notes", "mistake_events", "attendance"]
  },
  "quran": {
    "riwayah": "hafs_asim",
    "mushaf_type": "madani_15_line",
    "quran_core_version": "1.2.0"
  },
  "journey": {
    "started_at": "2022-09-01",
    "status": "memorizing",
    "direction": "backward",
    "current_position": {"ayah_index": 5673, "key": "67:1"},
    "level": "juz_29_30",
    "methodology": "sabaq_sabqi_manzil"
  },
  "memory_map": {
    "summary": {"memorized_ayat": 564, "strong": 410, "needs_revision": 120, "weak": 30, "critical": 4, "mastered": 0},
    "ranges": [
      {"from": "78:1", "to": "114:6", "from_index": 5673, "to_index": 6236, "state": "memorized",
       "retention_avg": 0.82, "verification": "teacher_verified", "verified_by": {"institution": "…", "role": "teacher"}, "last_verified_at": "2026-08-30"},
      {"from": "67:1", "to": "77:50", "from_index": 5242, "to_index": 5672, "state": "learning", "verification": "teacher_verified"}
    ],
    "weak_units": [{"unit": "page", "number": 585, "state": "weak", "retention_avg": 0.51}]
  },
  "milestones": [
    {"type": "surah.completed", "ref": "114", "at": "2022-10-15", "verification": "teacher_verified"},
    {"type": "juz.completed", "ref": "30", "at": "2023-06-02", "verification": "assessment"}
  ],
  "assessments": [
    {"id": "asm_…", "scope": {"unit": "juz", "number": 30}, "at": "2023-06-02", "score": 94, "result": "pass",
     "examiner": {"institution": "…", "role": "quran_supervisor"}, "rubric_ref": "juz_exam_v1"}
  ],
  "revision_history_summary": {
    "period": {"from": "2026-06-01", "to": "2026-08-31"},
    "far_revision_pages": 210, "near_revision_pages": 96, "compliance": 0.87
  },
  "certificates": [
    {"type": "hifz_milestone", "title": "Completion of Juz 30", "issued_at": "2023-06-10", "verification_url": "https://alhuda.example/verify/abc123"}
  ],
  "ijazah": [],
  "extensions": {},
  "signature": {"alg": "Ed25519", "key_id": "alhuda-2026", "value": "base64…", "canonicalization": "JCS"}
}
```

## 18.4 Privacy tiers

| Tier | Includes | Typical use |
|---|---|---|
| `minimal` | journey, memory_map summary + ranges (states only), milestones | Enrollment at a new center |
| `standard` | minimal + retention averages, assessments, certificates, revision summary | Transfer between institutions |
| `full` | standard + per-Ayah states, mistake statistics by type (no free text), attendance summary; teacher notes only if the note author consented and the guardian requested | Same organization, different branch; research with consent |

Guardian (or adult student) must approve the tier at export; the export UI lists every included section.

## 18.5 Import semantics

- Imported ranges enter the Memory Map with `verification: imported` and the issuer recorded; retention scores are seeded from `retention_avg` but decay normally.
- A verification Tasmee' upgrades imported units to `teacher_verified`.
- Ijazah entries are imported as **documentation only** with the original issuer; the receiving institution never re-issues them.
- Riwayah mismatch: the import is allowed only for matching Riwayah; otherwise it is stored as a reference document.

## 18.6 Verification

`GET https://{issuer}/.well-known/qlr.json` returns the institution's public keys and revocation list; verifiers recompute the canonical JSON (RFC 8785 JCS) and check the signature. Offline verification is possible with a cached key.

## 18.7 Governance

The spec lives in `docs/spec/qlr/` with a changelog; changes go through ADRs and a public comment period; the long-term aim is a neutral standards body with participating institutions and Quran app vendors.
