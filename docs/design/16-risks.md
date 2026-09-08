# 16 — Risks and Difficult Technical Areas

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **Quran text error in a release** (wrong character, missing mark, layout mismatch) | Low with pipeline, catastrophic without | Very high (trust, religious) | Verified sources only, deterministic builds, checksum snapshots, count/structure validators, two-reviewer sign-off, read-only runtime, public "Quran text issue" template routed to the review board, startup checksum verification |
| 2 | **Audio licensing**: no famous reciter recording has a documented redistribution license (research confirmed) | High | High (legal, reputational) | Ship no audio; license-gated reciter registry; QF API streaming adapter under its terms; commission or obtain written permission for a default reciter; operators import what they have rights to |
| 3 | **Content licensing** (Tafsir/Hadith datasets mostly unlicensed or restricted) | High | Medium | Ship provenance model + importers; bundle only cleared datasets (Open-Hadith-Data, HadeethEnc verbatim, Pickthall/Yusuf Ali, QAC, Lane); API adapters with attribution; per-item license fields |
| 4 | **Font licensing** (KFGQPC no-derivatives; me_quran non-commercial) | Medium | Medium | DigitalKhatt (OFL) as default; KFGQPC as unmodified operator pack with notice; never subset/convert |
| 5 | **Retention model credibility**: teachers distrust a score that disagrees with their judgment | Medium | High (adoption) | Explanations on every score; teacher overrides recorded; calibrate v2 from real data; UI language "educational metric"; never blocks teacher decisions |
| 6 | **Tasmee' UX too slow** in a real Halaqah | Medium | Very high | Interaction budget (≤ 4 taps), tablet/phone field testing before M2 exit, offline outbox, one-handed layout, default-present attendance |
| 7 | **Live audio quality on poor networks** | Medium | High | Audio-first defaults, Opus with FEC/DTX, TURN near users (Cloudflare anycast), adaptive downgrade, reconnect with state, region hints |
| 8 | **Video cost surprises** at scale on managed providers | Medium | Medium | Audio-only default; cost dashboard per tenant; self-host path documented with numbers; provider abstraction to switch |
| 9 | **Self-hosting operational burden** for small centers | High | Medium | Single-VPS Compose with backups and upgrade script; managed cloud option; Coolify/Dokploy compatibility; health checks and a "doctor" command |
| 10 | **Multi-tenant leakage bug** | Low–medium | Very high | Scoped repositories + RLS + isolation tests on every list/search endpoint + IDOR tests; security review before pilot |
| 11 | **Child privacy compliance across jurisdictions** (different ages, transfer licensing in Egypt, localization in Indonesia public sector, UAE regs pending) | High | High | Consent model per jurisdiction, self-hosting for strict regimes, DPIA template, minimal data, no ads/profiling, retention jobs; explicit "not legal advice" and a compliance checklist per country |
| 12 | **ASR overclaiming** (students or centers treating detector output as correctness) | Medium | High (religious) | Copy rules enforced in code, YELLOW class off by default, review queue, retention not updated by ASR, consent for minors, publish limitations |
| 13 | **LLM contamination of religious content** | Low with boundary | Very high | Type-level separation, storage class constraints, n-gram Quran match rejection, visible labels, retrieval-first assistant, no LLM in MVP |
| 14 | **Scope explosion** (the platform is large) | High | High | Staged roadmap; vertical slices; module toggles let centers ignore what they do not need; MVP exit criteria tied to a real pilot |
| 15 | **Arabic typography defects** (line breaking, mark placement, RTL bugs in web tables) | Medium | Medium | Flutter renderer with DigitalKhatt/KFGQPC; visual regression tests on Mushaf pages; RTL-first CSS with logical properties; Arabic-native reviewers |
| 16 | **Offline conflict resolution** for teacher assessments (two devices, edits) | Medium | Medium | Append-only events with idempotency keys; last-writer-wins only for session metadata; conflicts surfaced to the teacher; server is source of truth for state |
| 17 | **Payment gateway fragmentation** (no gateway covers Jordan, Saudi, Egypt, Pakistan together; Stripe unavailable in most core markets) | High | Medium | Manual/bank/cash first-class; adapter interface; per-country adapters added by community; merchant-of-record options evaluated for software-only sales |
| 18 | **Notification costs and regulation** (SMS into JO/EG/PK 20–50× local prices; sender-ID registration; WhatsApp template rules) | High | Medium | Push and in-app first; WhatsApp utility templates; local SMS aggregators via adapters; per-tenant channel budgets |
| 19 | **Community and scholar governance** (who decides Mutashabihat data, Tajweed taxonomy, Riwayah readiness) | Medium | High | Quran Core review board in GOVERNANCE.md; provenance and review status on every dataset; conservative defaults |
| 20 | **Recording promise misunderstood** as "impossible to record" | Medium | Medium | Exact wording in UI and docs; deterrence controls documented honestly |
| 21 | **Performance of per-Ayah state at scale** (10k students × 6,236 rows = 62M rows) | Medium | Medium | Rows created lazily (only touched Ayat), partitioning, aggregates materialized, daily decay in batches, snapshots for trends |
| 22 | **Maintainer bandwidth** | High | High | Modular monolith, strong CI, documentation-first, DCO, clear module ownership, funding through the managed cloud and institutional sponsors |

## Difficult technical areas (where to spend senior time)

1. **Mushaf renderer with word-level hit testing** across Mushaf types and fonts (Flutter + web).
2. **Retention engine calibration** and explanation quality.
3. **Planner correctness under real policies** (edge cases: pauses, carry-forward, partial passes, teacher overrides, post-Hifz cycles, direction changes).
4. **Classroom sync + media integration** (token grants, reconnect, roster states, breakout scoping).
5. **Tenant isolation with RLS** in Django (connection context, Celery, Channels).
6. **Offline-first mobile sync** with idempotent event outboxes.
7. **Quran Core build pipeline** (deterministic, validated, reproducible, multi-Riwayah numbering maps).
8. **Arabic search normalization** in PostgreSQL.
9. **Portable record signing and verification**.
