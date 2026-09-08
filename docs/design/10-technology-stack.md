# 10 — Recommended Technology Stack

Selection criteria, in order: Quran-accuracy safety, maintainability by an open-source community, cost on a single VPS, Arabic/RTL quality, and the user's Python comfort. Fashion is not a criterion.

## 10.1 Summary

| Layer | Choice | Alternatives considered | Why |
|---|---|---|---|
| Architecture | **Modular monolith** (Python) with clear domain packages, one deployable, workers, and a realtime process | Microservices | A small team and volunteers cannot operate 12 services; boundaries live in code (`packages/`, `services/` as Django apps with enforced import rules); extraction later is possible because modules communicate via internal interfaces and events |
| Backend framework | **Django 5.x + Django REST Framework** + `drf-spectacular` (OpenAPI) | FastAPI; Django Ninja | Migrations, ORM, auth, admin, i18n, and a huge contributor base; the domain is CRUD-heavy with complex permissions where Django's maturity beats FastAPI's speed; strong typing via `mypy` + `django-stubs` + Pydantic value objects in domain packages |
| Domain layer | Plain Python packages (`packages/hifz-engine`, `packages/quran-core`, `packages/permissions`) with Pydantic models and Protocols; Django apps are thin adapters | Business logic in views/serializers | Testable without a database; engines usable by CLI tools and third parties |
| Database | **PostgreSQL 16+** with row-level security for tenant isolation, JSONB for policies/settings, `pg_trgm` + full-text for search | MySQL; multi-DB | RLS gives defense in depth for multi-tenancy; one engine to operate |
| Cache / queue / realtime backplane | **Valkey** (BSD-3, Redis-compatible) | Redis 8 (tri-license), RabbitMQ | License clarity for an OSS project; one process for cache, Celery broker, Channels layer, rate limits |
| Background jobs | **Celery 5** + Celery Beat (Valkey broker) | Dramatiq, django-tasks, Temporal | Standard, well-known; schedules for daily plan generation, retention decay, weekly reports, notification fan-out |
| Realtime (control plane) | **Django Channels** (ASGI, WebSocket) for the classroom sync channel and live dashboards | Separate Node service; Centrifugo | Keeps one codebase; Centrifugo can be adopted later if fan-out grows |
| Media (video/audio) | **LiveKit** OSS self-host or LiveKit Cloud via `RtcProvider`; Jitsi second adapter | see `09` | Same SDKs self-hosted and managed; recording is absent unless egress deployed |
| Admin web | **Next.js (React) + TypeScript**, TanStack Query, design system package, `next-intl`, CSS logical properties for RTL | Vue/Nuxt; Django templates | Best ecosystem for a large admin app; SSR not required (app is authenticated) so a static export is fine for self-hosters |
| Mobile (student, teacher, parent) | **Flutter** (single codebase, role-based shells) with `drift` (SQLite) for offline, `livekit_client`, custom Mushaf renderer | React Native | Superior Arabic text shaping and custom font rendering (HarfBuzz via Skia/Impeller), consistent RTL, one codebase for iOS/Android/web/desktop, first-party LiveKit SDK, strong offline story |
| Mushaf rendering | Custom widget over Quran Core layout data; DigitalKhatt/KFGQPC fonts; overlays for pointers/highlights | WebView | Word-level tap targets and performance need native rendering |
| Storage | S3-compatible via `StorageProvider`: local FS (dev), Garage/SeaweedFS (self-host), R2/B2/Hetzner (managed) | MinIO | MinIO's community repo was archived in April 2026; Garage (AGPL) and SeaweedFS (Apache-2.0) are maintained |
| Search | PostgreSQL full-text with Arabic normalization (diacritics stripping, alef/ya/ta-marbuta folding) | Meilisearch/OpenSearch later | Sufficient for names, content library, Hadith; a `SearchProvider` interface allows a dedicated engine |
| Notifications | `NotificationChannel` adapters: FCM/APNs, email (SMTP/SES/Postmark), SMS (Twilio/regional), WhatsApp (Meta Cloud API/360dialog), in-app | Novu | Adapters are small; Novu adds a service to run |
| AI (optional) | `packages/ai-providers`: `NullProvider` default; ASR adapters (self-hosted faster-whisper/FastConformer, cloud APIs); LLM adapters (any OpenAI-compatible endpoint, Anthropic, Gemini, local vLLM) | Vendor lock | Fully optional; tenant-supplied keys |
| Auth | Django sessions for web + JWT (short-lived access, rotating refresh) for mobile; OIDC via `mozilla-django-oidc`/`django-allauth` for SSO; TOTP MFA; passkeys later | Keycloak | Avoid running an IdP for small centers; Keycloak can be plugged via OIDC for large orgs |
| i18n | **Arabic is the default UI language; English is the supported second language.** Django `gettext` (backend messages), `next-intl` (web), Flutter `intl` + ARB (mobile); source strings authored in Arabic with English as the first translation; RTL is the base layout direction and LTR the mirrored case; Crowdin/Weblate for further community languages | | Quran text presentation independent from UI language |
| Observability | `structlog` JSON logs, OpenTelemetry traces/metrics, Prometheus + Grafana (self-host) or Grafana Cloud, Sentry or GlitchTip for errors, Uptime Kuma | | Free/self-host path for every piece |
| Testing | `pytest` + `pytest-django` + `factory_boy`, `schemathesis` (API contract), Playwright (web E2E), Flutter integration tests, permission-matrix generator, Quran Core snapshot tests | | See `52` requirements in the brief |
| Quality | `ruff`, `mypy --strict` on domain packages, `black` (or ruff format), `eslint`/`prettier`, `dart analyze`, pre-commit, CodeQL + `pip-audit` + `npm audit`, Trivy for images | | |
| CI/CD | GitHub Actions: lint → type → unit → integration (PostgreSQL + Valkey services) → API contract → Quran Core integrity → build images → E2E on PR label | | |
| Deployment | Docker Compose profiles (`single-vps`, `medium`), Caddy for TLS, optional Helm chart for Kubernetes | Nomad | Kubernetes optional, never required |

## 10.2 Backend structure (Django as the shell, domain in packages)

```
apps/api/                     # Django project (settings, urls, ASGI/WSGI)
services/                     # Django apps = bounded contexts (thin: models, serializers, views, tasks)
  identity/ tenants/ people/ quran_learning/ content/ courses/ classroom/
  scheduling/ attendance/ finance/ notifications/ analytics/ audit/ portability/
packages/                     # pure Python, no Django imports
  quran-core/                 # read-only accessor + validation suite
  hifz-engine/                # retention engine, planner, policy schema
  permissions/                # capability + RBAC resolution
  ai-providers/               # Protocols + Null/local/cloud adapters
  video-provider/             # RtcProvider Protocol + adapters
  storage-provider/           # S3-compatible abstraction
  notification-channels/      # channel adapters
  shared-types/               # Pydantic models shared across services (and exported to TS/Dart)
```

Import rules (enforced by `import-linter`): `packages/*` never import `services/*` or Django; `services/*` may import `packages/*` and other services only through their public `api.py` modules; `quran_core`, `mushaf`, and `hifz.practice.hints` may not import `ai_providers`.

Requests flow: HTTP → DRF view (auth, capability check, permission check) → service function (transaction, domain call, events) → repository (scoped queryset) → PostgreSQL (RLS). Views contain no business logic.

## 10.3 Why not FastAPI

FastAPI is excellent for small, typed APIs. This product needs migrations across 100+ tables, admin tooling, a mature permission ecosystem, i18n, and thousands of CRUD endpoints with consistent pagination/filtering. Django + DRF delivers that with far less custom code, and DRF's OpenAPI output (via drf-spectacular) is good enough for the API-first requirement. Performance is not the bottleneck; the retention engine and planner are pure Python packages that run in workers regardless of the web framework.

## 10.4 Why Flutter over React Native

- Arabic and Quran typography: Flutter renders text through its own engine with HarfBuzz shaping and full control over custom fonts, line breaking, and word-level hit testing. Achieving a faithful, tappable Mushaf in React Native means native modules per platform.
- Offline: `drift` (SQLite) with reactive queries fits the "today's plan + Mushaf + audio cache" model.
- One codebase for teacher, student, and parent apps (role-based shells), plus web and desktop builds for free.
- LiveKit ships a first-party Flutter SDK (and RN); both are fine, but the typography argument decides.

The admin web stays in React because a large data-heavy admin UI benefits from the React ecosystem (tables, forms, charts) and web-only distribution.

## 10.5 Quran Core at runtime

- Server: Quran Core tables in PostgreSQL loaded from the release artifact by a management command; the application database role has `SELECT` only; a trigger raises on any write; startup verifies checksums against the manifest.
- Mobile: the same release as a SQLite file downloaded on first run (per Riwayah/Mushaf type), checksum-verified, versioned; audio index included; audio files streamed/cached separately.

## 10.6 Data flow for a Tasmee' event (end to end)

Teacher taps mistake → Flutter writes `MistakeEvent` to the local outbox (drift) → sync worker POSTs `/v1/recitations/{session}/events` (idempotency key) → DRF view checks `hifz.tasmee.record` + scope → service appends events, updates `STUDENT_AYAH_STATE` via `hifz-engine` → emits `assessment.recorded` on the outbox table → Celery relays to subscribers (planner regeneration, parent summary, supervisor aggregates) → Channels pushes live updates to open dashboards.
