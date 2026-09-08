# ADR-0001 — Platform license: AGPL-3.0 (SDKs MIT)

Status: proposed (confirm before first public release) · Date: 2026-09-08

## Context
Talaqqi is a social-impact, open-source platform that will also be offered as a managed cloud. Closed SaaS forks by third parties would fragment the community and remove improvements from centers that self-host.

## Decision
- Platform code (`apps/`, `services/`, `packages/` except SDK/types): **AGPL-3.0-only**.
- API clients, shared types, design tokens, Quran Core build tools: **MIT**, so third-party apps integrate without AGPL obligations.
- Quran Core data: per-source terms (`packages/quran_core/LICENSE-DATA.md`); only redistributable sources are shipped.
- Contributions under DCO sign-off (no CLA).

## Alternatives
Apache-2.0 maximizes vendor adoption but permits closed hosted forks. Revisit only before the first public release; changing later requires every contributor's consent.
