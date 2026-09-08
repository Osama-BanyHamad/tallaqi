# تَلَقِّي — Talaqqi · [tallaqi.com](https://tallaqi.com)

**Open-source infrastructure for Quran education.** A multi-tenant operating system for the student's Quran learning journey: Memory Map, retention engine, adaptive planner, Tasmee' workflow, live classroom, parent and supervisor loops, administration and finance. Arabic-first (RTL), English supported.

> Quran accuracy beats convenience. The Quran text ships as an immutable, checksummed release; no service, admin, or AI can write to it. See `docs/design/07-religious-ai-safety.md`.

## Live demo

| | |
|---|---|
| Public site | https://tallaqi.com |
| Web app (sign in) | https://tallaqi.com/login |
| API docs (OpenAPI) | https://tallaqi.com/api/docs/ |
| Android app (beta APK, 51 MB) | https://tallaqi.com/downloads/talaqqi-android.apk |

All demo accounts use the password **`Talaqqi@2026`** on the tenant **`demo`** (مركز النور لتحفيظ القرآن الكريم). Data is seeded and may be reset at any time.

| Role | Email | What you see |
|---|---|---|
| Owner | `owner@demo.talaqqi` | Everything: supervisor dashboard, students, Halaqat, staff, finance, reports, settings, audit |
| Quran supervisor | `supervisor@demo.talaqqi` | Dashboard and Halaqat of the main branch |
| Teacher | `teacher1@demo.talaqqi` … `teacher4@demo.talaqqi` | Own Halaqah: today's roster, attendance, Tasmee' from the Mushaf |
| Parent | `parent1@demo.talaqqi`, `parent2@demo.talaqqi` | Parent portal: the six weekly answers per child |
| Student | `student1@demo.talaqqi`, `student2@demo.talaqqi` | Today's plan, Memory Map, self-practice |
| Finance | `finance@demo.talaqqi` | Fee plans, invoices, payments |

The same accounts work in the Android app (teacher, student, and parent shells).

## Status

Phase 9 bootstrap + first vertical slice of the core loop:

- Quran Core (Hafs, Tanzil verbatim + CC-BY metadata) with integrity tests and read-only PostgreSQL tables
- Multi-tenancy with PostgreSQL row-level security + scoped repositories, capability system, RBAC with scopes, audit log
- Students, guardians, staff, Halaqat, enrollment, attendance
- Quran Journey, per-Ayah Memory Map with history, `retention/v1`, Learning Policy templates, `planner/v1`, Tasmee' API, supervisor dashboard
- Admin web + public site (Next.js, Arabic-first) — `apps/admin-web` (site at `/`, app at `/login`)
- Mobile app (Flutter, one codebase, role shells: teacher · student · parent) — `apps/mobile`

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
cd apps/mobile && flutter pub get && flutter run          # phone/emulator; web: flutter run -d web-server --web-port 3100 --dart-define=API_URL=http://localhost:8000
```

Demo logins: see **Live demo** above (same accounts locally after `seed_demo`; add `ensure_demo_students` and `ensure_demo_finance` for student logins and finance data).

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

## Contributing

`main` is protected: nobody pushes to it directly, including maintainers. All changes land through a pull request that the repository owner merges.

1. Fork (or branch, for collaborators): `git checkout -b feat/short-name`
2. Keep the Quran Core untouched. Any change under `packages/quran_core/data` needs the `quran-core-release` label and a maintainer review; the checksum tests will fail otherwise.
3. Run the checks before opening the PR:

```bash
python -m pytest -q
ruff check .
cd apps/admin-web && npx tsc --noEmit
```

4. Open the PR against `main` with a short description of what changed and why. CI runs the same checks; the owner reviews and merges (squash).

Security issues: please do not open a public issue; email the maintainer instead (see the GitHub profile).

## License

Platform code: AGPL-3.0. Quran text: Tanzil Project terms (verbatim, attributed) — see `packages/quran_core/LICENSE-DATA.md`.
