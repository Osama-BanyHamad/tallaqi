# ADR-0006 — Quran Core is immutable, versioned, and checksummed

Status: accepted · Date: 2026-09-08

## Decision
- Quran text and structure live in `packages/quran_core/data/` as a built release (`manifest.json` with SHA-256 per file, a text-root hash, and a per-Ayah golden snapshot).
- The accessor verifies every checksum on load and refuses to start on mismatch; `/readyz` exposes the verification.
- CI runs `packages/quran_core/tests/test_integrity.py`; PRs that touch `packages/quran_core/data/` are blocked unless labeled `quran-core-release` and approved by two members of the review board (CODEOWNERS).
- Runtime tables (`quran_*`) reject writes via trigger; the only write path is `manage.py load_quran_core`.
- No AI, TTS, or admin has any write path. `SacredText` is never produced from generated content (import-linter contract).

## Source
Tanzil Uthmani text (verbatim, attributed; modification prohibited) + Tanzil metadata (CC-BY). The Basmalah is part of the first Ayah of each Surah in this source and is split only at presentation time.
