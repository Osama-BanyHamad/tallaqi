# Talaqqi — Design Package (Phase 1 deliverable)

Working name: **Talaqqi** (تَلَقِّي, "receiving the Quran from a teacher"). Tagline: *open-source infrastructure for Quran education*.

This package answers the 20 items requested before any application code is written. Research with sources and verification status is in `../research/`.

| # | Requested item | Document |
|---|---|---|
| 1 | Final product concept and name suggestions | `01-product-concept.md` |
| 2 | Ecosystem / module map | `02-ecosystem-and-modules.md` §2.1 |
| 3 | User types | `03-users-and-journeys.md` §3.1 |
| 4 | Main user journeys | `03-users-and-journeys.md` §3.3 |
| 5 | Complete module list | `02-ecosystem-and-modules.md` §2.3 |
| 6 | Modular feature-toggle architecture | `04-capability-architecture.md` |
| 7 | Quran learning architecture | `05-quran-learning-architecture.md` |
| 8 | Quran Core architecture (+ Qira'at, audio) | `06-quran-core-architecture.md` |
| 9 | Religious AI safety architecture | `07-religious-ai-safety.md` |
| 10 | Online classroom architecture (+ non-recorded classes, provider abstraction) | `08-online-classroom-architecture.md` |
| 11 | Video provider comparison with current pricing | `09-video-provider-comparison.md` (+ `../research/video-providers.md`) |
| 12 | Recommended technology stack | `10-technology-stack.md` |
| 13 | Multi-tenant architecture | `11-multi-tenancy.md` |
| 14 | High-level ERD | `12-data-model-erd.md` |
| 15 | System architecture diagrams | `13-system-architecture.md` |
| 16 | Repository structure | `14-repository-structure.md` |
| 17 | MVP scope | `15-roadmap.md` §15.1 |
| 18 | Phase 2 scope | `15-roadmap.md` §15.2 |
| 19 | Long-term roadmap | `15-roadmap.md` §15.3 |
| 20 | Risks and difficult technical areas | `16-risks.md` |
| + | Cost model (free / low-cost / scalable per dependency) | `17-cost-model.md` |
| + | Portable Quran Learning Record spec v0.1 | `18-portable-learning-record.md` |

## Research (sourced, dated 2026-09-08)

| File | Contents |
|---|---|
| `../research/video-providers.md` | LiveKit, Daily, Agora, 100ms, Cloudflare, Zoom, Vonage, Stream, Chime, Jitsi; scenario arithmetic; self-host estimates |
| `../research/infra-costs.md` | Storage, email, SMS, WhatsApp, push, ASR, LLM, databases, hosting, observability, payment gateways |
| `../research/audio-and-content-licensing.md` | Reciter audio, Quran text sources, Tafsir, Hadith, corpus datasets, with bundling verdicts |
| `../research/competitive-landscape.md` | Arabic, Malay/Indonesian, UK/US/South Asian center systems; consumer Hifz apps; academies; OSS projects; gap verification |
| `../research/fonts-and-privacy.md` | KFGQPC/QCF/DigitalKhatt/OFL fonts; child-privacy law orientation for 15 jurisdictions |

## Headline decisions

1. Modular monolith: Django + DRF (Python), PostgreSQL with row-level security, Valkey, Celery, Channels; Next.js admin; Flutter for the three mobile roles.
2. Shared-schema multi-tenancy with RLS and scoped repositories; database-per-tenant as a later option for regulated tenants.
3. Immutable, versioned, checksummed Quran Core; Hafs first; multi-Riwayah data model; no audio bundled (licensing), license-gated reciter registry.
4. Deterministic, explainable retention engine and planner; teachers always decide; AI optional and off by default.
5. Live classroom on a provider abstraction with LiveKit as the reference adapter (self-host ≈ $20–660/month for 100–10,000 students, audio-first), Cloudflare TURN, Jitsi as second adapter; recording absent by design when disabled.
6. Portable Quran Learning Record as an open JSON spec from v0.1.
7. AGPL-3.0 for the platform, MIT for SDKs/types (to be confirmed in ADR-0001).
8. Arabic is the default language of every surface (admin web, apps, notifications, documents), with RTL as the base layout; English is fully supported as the second language. Quran text rendering is independent of the UI language.

## What is intentionally not in this package

Phase 2 (full PRD with acceptance criteria), Phase 3 (screen inventory and flows), Phase 6 (API specification), Phase 7 (UX/UI specification), and Phase 8 (stories) build on these documents and follow once the concept, stack, and scope are confirmed.
