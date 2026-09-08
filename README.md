# تَلَقِّي — Talaqqi

**Open-source infrastructure for Quran education.** A multi-tenant operating system for the student's Quran learning journey: Memory Map, retention engine, adaptive planner, Tasmee' workflow, live classroom, parent and supervisor loops, administration and finance. Arabic-first (RTL), English supported.

> Quran accuracy beats convenience. The Quran text ships as an immutable, checksummed release; no service, admin, or AI can write to it. See `docs/design/07-religious-ai-safety.md`.

## Status

Phase 9 bootstrap + first vertical slice of the core loop:

- Quran Core (Hafs, Tanzil verbatim + CC-BY metadata) with integrity tests and read-only PostgreSQL tables
- Multi-tenancy with PostgreSQL row-level security + scoped repositories, capability system, RBAC with scopes, audit log
- Students, guardians, staff, Halaqat, enrollment, attendance
- Quran Journey, per-Ayah Memory Map with history, `retention/v1`, Learning Policy templates, `planner/v1`, Tasmee' API, supervisor dashboard
- Admin web (Next.js, Arabic-first) — see `apps/admin-web`

## Run locally (Windows/macOS/Linux)

Requirements: Python 3.12, Node 22 + pnpm, PostgreSQL 16+ (local or `docker compose --profile dev up -d`).

```bash
cp .env.example .env
psql -U postgres -f infra/scripts/init-db.sql          # creates role talaqqi_app (non-superuser) + db
pip install ".[dev]"
python apps/api/manage.py migrate
python apps/api/manage.py load_quran_core               # verifies checksums, loads read-only tables
python apps/api/manage.py seed_demo                     # demo tenant "demo" with Arabic data + simulated history
python apps/api/manage.py runserver                     # http://localhost:8000/api/docs/
cd apps/admin-web && pnpm install && pnpm dev           # http://localhost:3000
```

Demo logins (`/demo` tenant, password `Talaqqi@2026`): `owner@demo.talaqqi`, `supervisor@demo.talaqqi`, `teacher1@demo.talaqqi` … `teacher4@`, `parent1@`, `finance@`.

## Tests

```bash
python -m pytest -q            # unit + integration (tenant isolation, IDOR, capability gating, Tasmee' loop)
```

`packages/quran_core/tests/test_integrity.py` fails if a single Ayah changes without a reviewed release (manifest + snapshot). CI additionally blocks PRs touching `packages/quran_core/data/` unless labeled `quran-core-release`.

## Layout

```
apps/api          Django project (settings, urls)
apps/admin-web    Next.js admin (Arabic-first, RTL)
services/*        Django apps = bounded contexts (thin views → services → models)
packages/*        pure Python: quran_core, hifz_engine, permissions (no Django, no AI imports)
docs/design       design package · docs/research sourced research
infra/            docker, compose profiles, caddy, garage
```

## License

Platform code: AGPL-3.0. Quran text: Tanzil Project terms (verbatim, attributed) — see `packages/quran_core/LICENSE-DATA.md`.
