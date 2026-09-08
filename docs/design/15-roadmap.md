# 15 — MVP Scope, Phase 2 Scope, and Long-Term Roadmap

The complete architecture is designed now; delivery is staged so that a small center gets real value at the end of the MVP without waiting for the full platform.

## 15.1 MVP (v0.1 → v0.5): "One center runs its Halaqat on Talaqqi"

Success criterion: a real center with in-person Halaqat and optional online 1:1 classes runs daily on the platform for a full term, and the CI proves Quran text integrity.

| Area | In MVP | Deliberately out |
|---|---|---|
| Platform | Multi-tenant (shared schema + RLS), tenant + branch settings, branding basics, Arabic default UI with English as second language, RTL-first layout, capability system, RBAC with scopes, audit log, health, structured logs | Custom domains, SSO, platform billing |
| Quran Core | Hafs 'an 'Asim text + Madani 15-line layout + units/markers, checksums, release pipeline, read API, one OFL font pack (DigitalKhatt) + operator-installable KFGQPC pack, reciter registry with license gate, audio index + ingestion tool (no bundled audio), QF API streaming adapter | Other Riwayat, page-image mode, Mutashabihat dataset (seeded manually by teachers in MVP) |
| Journey & Memory Map | Journey profile, per-Ayah state + history, aggregates (page/Surah/Juz), timeline milestones, weak-region views | Retention snapshots analytics UI beyond basics |
| Retention & Planner | `retention/v1` deterministic engine with explanations, decay job, Learning Policy Builder with 3 templates (Sabaq/Sabqi/Manzil, page-based weekly, post-Hifz cycle), daily plan proposal + teacher approve/edit/override, pause rules | AI recommendations |
| Tasmee' | Mobile/tablet Mushaf-based mistake capture (standard taxonomy + tenant custom types), pass/repeat, notes, offline outbox, edit window with audit | Voice notes transcription |
| Assessments | Juz/Surah assessment definitions, rubric scoring, results | Blind second examiner, exam scheduling UI polish |
| Practice | Today's plan, listen (verified audio), hide/reveal practice, verified hints (text/audio), deterministic quizzes | ASR mismatch detection (YELLOW, phase 2) |
| People & ops | Students, guardians (consent capture), staff, Halaqat, enrollment + waiting list, attendance, recurring schedules with conflicts, holidays, substitutions | HR, payroll, rooms equipment |
| Parent | Parent app: six questions, weekly report, multiple children, announcements | Payments in parent app (phase 2 unless gateway ready) |
| Supervisor | On-track/behind/attention lists, Halaqah performance, teacher load, drill-down, rule-based intervention flags + action workflow | Dropout risk model |
| Live classroom | 1:1 and small-group sessions via LiveKit adapter (self-host + cloud), audio-first, waiting room, shared Mushaf follow + pointers, in-class Tasmee', attendance, recording OFF only, watermark | Breakouts, chat, recording ON path, second provider |
| Finance | Fee plans, invoices, receipts (PDF), manual/bank/cash payments, discounts, scholarships, overdue reminders | Gateways (first adapter in phase 2), donations, expenses, payroll |
| Communication | Push (FCM/APNs), email adapter, in-app announcements, teacher↔guardian messaging under policy | SMS, WhatsApp |
| Reports | Hifz progress, retention, attendance, enrollment, unpaid fees; CSV export | Scheduled report delivery |
| Portability | QLR export/import v0.1 (JSON, signed) | Cross-institution verification network |
| Apps | Admin web, Flutter app with teacher/student/parent shells, offline Mushaf + today's plan | Desktop builds |
| Ops | Docker Compose `single-vps`, backups, upgrade guide, demo seed | Helm, HA guide (docs only) |

## 15.2 Phase 2 (v0.6 → v1.0): "Institutions and online academies"

- Live: group Halaqah mode (roster states, sequential Tasmee', breakouts), chat with policy, low-bandwidth tuning, second adapter (Jitsi/JaaS), recording-ON path with consent and retention, E2EE option for 1:1.
- Quran learning: Mutashabihat system (verified dataset + personal sets + exercises), Tajweed rubric, ASR mismatch detection (YELLOW) with self-hosted FastConformer/Whisper adapters and Teacher Review Queue, retention snapshots and trend analytics, `retention/v2` calibration from real data (still deterministic).
- Content: Islamic Knowledge Library with provenance model, Tafsir importer (QUL classical Arabic with attribution; QF API adapter), Hadith (Open-Hadith-Data + HadeethEnc adapters; sunnah.com API), Tajweed theory, vocabulary (QAC morphology), retrieval-first knowledge search.
- LMS: courses/modules/lessons, homework, quizzes/exams, course certificates, cohorts, learning paths.
- Finance: first gateway adapters (Stripe where available, Paymob, Safepay), donations/sponsorship, expenses, teacher payouts.
- Communication: SMS + WhatsApp adapters, notification preference center, digests.
- Platform: SSO (OIDC), custom domains, API keys + webhooks, tenant usage metrics, Helm chart, medium-profile guide.
- Riwayat: Warsh and Qalun text + layouts + fonts when verified sources and licenses are confirmed.
- Portability: QLR v1.0 with institution signatures and verification workflow.
- Managed cloud: tenant provisioning, plan → module mapping, billing integration (project-operated).

## 15.3 Long-term roadmap (v1.x → v3)

| Horizon | Themes |
|---|---|
| v1.x | HR and payroll; accounting exports; regulator export formats (e.g. Saudi MOIA registry); advanced scheduling (teacher availability optimization); office hours; women's-center presets; accessibility audit (WCAG 2.2 AA) |
| v2 | Additional Riwayat (Duri, Shu'bah) as data allows; page-image mushaf mode; Ijazah documentation workflows with institutional attestations; QLR verification network (signed records verifiable across institutions); analytics warehouse and cohort outcome studies; AI recommendation provider (YELLOW) with teacher approval; on-device ASR for practice |
| v3 | Federation between self-hosted instances for student transfers; open standard governance for QLR and the learning policy schema; certified adapter marketplace (video, payments, notifications); research partnerships on retention modeling with anonymized, consented data |

## 15.4 Sequencing rationale

1. **Quran Core and the learning loop first** because they are the differentiator and everything else references them.
2. **Tasmee' before analytics** because analytics without daily teacher data is empty.
3. **Parent and supervisor views immediately after Tasmee'** because they close the loop and drive adoption.
4. **Live classroom in MVP but audio-first and 1:1/small group only**, because online academies are a core market and LiveKit makes the basic path cheap; group mode needs the sync protocol hardened first.
5. **Finance basic in MVP** because centers will not adopt without fees, but gateways vary by country and need adapters that come later.
6. **AI last and optional**, after the deterministic baseline proves itself and consent/retention plumbing exists.

## 15.5 Milestones and epics (MVP)

| Milestone | Epics |
|---|---|
| M0 Bootstrap (Phase 9 of the brief) | Repo, CI, Docker, auth, tenants, RBAC, Quran Core load + integrity tests, design tokens, app shells |
| M1 People & Halaqat | Students, guardians, consent, staff, branches, Halaqat, enrollment, waiting list, scheduling, attendance |
| M2 Learning core | Journey, Memory Map, retention v1, policy builder, planner, Tasmee' mobile, assessments |
| M3 Loop closure | Parent app + weekly report, supervisor dashboard, intervention flags, notifications (push/email) |
| M4 Live classroom | LiveKit adapter, join tokens, sync channel, shared Mushaf, in-class Tasmee', attendance, recording OFF, watermark |
| M5 Finance & reports | Fee plans, invoices, receipts, manual payments, reports, exports |
| M6 Practice & portability | Student practice with verified hints/audio, deterministic quizzes, QLR v0.1, offline |
| M7 Hardening | Isolation/permission test suites complete, security review, single-VPS deployment guide, pilot with a real center |
