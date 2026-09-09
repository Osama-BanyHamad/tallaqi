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

## Technology

| Layer | Choice | Notes |
|---|---|---|
| Backend | **Python 3.12 · Django 5.1 · Django REST Framework** | Modular monolith: each bounded context is a Django app under `services/*` (thin views → services → models). OpenAPI via drf-spectacular at `/api/docs/`. |
| Database | **PostgreSQL 16 with row-level security** | Shared schema, `tenant_id` on every table, `FORCE ROW LEVEL SECURITY`; the app connects as a non-superuser role so RLS applies to the application itself. Quran tables are read-only by trigger. |
| Cache / queues | **Valkey** (Redis-compatible) | Sessions, rate limits, and job queues; Celery-ready. |
| Auth | **JWT (SimpleJWT)** + `X-Tenant` header | One account can belong to several tenants; roles are per tenant with scopes (tenant · branch · Halaqah · student set · self). |
| Permissions | **Capability catalog + RBAC** (`packages/permissions`) | ~25 modules that can be switched per tenant; disabling a module makes its endpoints return 403. Every check is enforced in the backend, and every mutation is written to an immutable audit log. |
| Quran text | **Quran Core** (`packages/quran_core`) | Tanzil Uthmani text, verbatim, with a signed manifest and a per-Ayah SHA-256 snapshot; tests fail if a single letter changes. Hafs first, multi-Riwayah data model. |
| Hifz engine | **`retention/v1` + `planner/v1`** (`packages/hifz_engine`, pure Python) | Deterministic, explainable forgetting curve (FSRS-style stability) per Ayah, computed from teacher-verified recitations. The planner turns it into a daily new/near/far plan the teacher can override. No AI in the loop. |
| Admin web + site | **Next.js 15 · React 19 · TanStack Query** | Arabic-first RTL design system in plain CSS (Noto Kufi Arabic, IBM Plex Sans Arabic, Amiri Quran for the Mushaf). Public site and app share one codebase; standalone output for Docker. |
| Mobile | **Flutter 3** (`apps/mobile`) | One codebase, three role shells (teacher · student · parent). Android beta today; iOS build from the same code. |
| Live classroom | `RtcProvider` abstraction, LiveKit reference adapter (planned) | Audio-first, shared Mushaf, recording absent by design when disabled. |
| AI | Optional, `NullProvider` by default | GREEN / YELLOW / RED safety classes; type-level separation between sacred text and generated text. The platform runs fully without any AI provider. |
| Deployment | **Docker Compose + Caddy** | Single VPS: postgres, valkey, api (gunicorn), web (Next standalone), caddy with automatic TLS. `infra/scripts/deploy-do.sh` pulls, builds, migrates, and seeds. |
| Quality | pytest (tenant isolation, IDOR, capability gating, Tasmee' loop, finance), ruff, TypeScript strict, GitHub Actions CI | The Quran Core integrity test and a label gate protect `packages/quran_core/data/`. |

### How a recitation flows through the system

1. The teacher opens today's plan for a student and taps a word on the Mushaf to record a mistake, then presses Pass / Partial / Repeat.
2. `services/hifz` stores the recitation and mistake events, then calls `retention/v1` for every Ayah in the range.
3. Each Ayah's stability and next-due date are updated; the journey's materialized `juz_map` (30 × coverage, average, state) is refreshed for the strips.
4. `planner/v1` regenerates tomorrow's segments (new / near / far), pausing new memorization when the revision backlog is too large.
5. The parent portal and the supervisor dashboard read the same records, so everybody sees one truth.

## Independent learners (تَلَقِّي للأفراد)

Anyone can start alone at https://tallaqi.com/start: pick a goal, tap the Juz already memorized, choose a daily time budget, and the planner produces a daily plan. The learner gets the memory map, self-practice, and the AI recitation check, and can invite a **listener** (parent, friend, remote teacher) who records Tasmee' from the app. Technically this is a one-person tenant (`kind = solo`) with the `solo_learner` role, so isolation and every feature work unchanged, and the journey can later move to a center.

## Status

Phase 9 bootstrap + first vertical slice of the core loop:

- Quran Core (Hafs, Tanzil verbatim + CC-BY metadata) with integrity tests and read-only PostgreSQL tables
- Multi-tenancy with PostgreSQL row-level security + scoped repositories, capability system, RBAC with scopes, audit log
- Students, guardians, staff, Halaqat, enrollment, attendance
- Quran Journey, per-Ayah Memory Map with history, `retention/v1`, Learning Policy templates, `planner/v1`, Tasmee' API, supervisor dashboard
- Admin web + public site (Next.js, Arabic-first) — `apps/admin-web` (site at `/`, app at `/login`)
- Mobile app (Flutter, one codebase, role shells: teacher · student · parent · independent learner · listener) — `apps/mobile`
- Daily reading (wird): a personal Mushaf plan by pages (khatmah in N days or pages/day), today's pages, streak, history — `services/reading`, the **الورد** tab in the app and `/read` on the web
- Ayah audio: tap any ayah to hear it from a reciter registry (`/api/v1/quran/reciters`); audio is streamed per ayah from a configurable host, nothing is bundled or redistributed
- Reminders: local daily notifications on the phone for the wird, the daily plan, and the Halaqah (no push service, nothing leaves the device)

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

## Operations

- **Backups**: `infra/scripts/backup.sh` dumps PostgreSQL nightly (cron installed by the deploy script), 14-day retention in `/opt/talaqqi/backups`.
- **Statistics**: `https://<domain>/stats/` (basic auth) — visitors, page views, app downloads, and a product funnel from the database; see `docs/deployment/digitalocean.md`.
- **Rate limits**: sign-in 20/min and sign-up 10/hour per IP; the AI recitation check has a per-account daily quota (`ASR_DAILY_QUOTA`).
- **Roles and modules** are synced from the permission catalog on every deploy (`manage.py sync_roles`); new default-on modules are added to existing tenants without overriding operator choices.
- **Ayah audio**: the reciter registry defaults to verse-by-verse MP3s streamed from everyayah.com; operators can point it at their own licensed host with `AUDIO_RECITERS_JSON` (list of `{key, name_ar, name_en, base}`).
- **Deploys** build the new images first, keep the previous ones tagged `:previous`, swap, then health-gate the API and the web home page; a failed release rolls back automatically. The API restarts once for migrations (about 20 seconds); the site stays up.

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
