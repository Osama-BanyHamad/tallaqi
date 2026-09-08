# 01 — Product Concept, Vision, and Naming

## 1.1 The one-sentence concept

**An open-source operating system for Quran education**: a multi-tenant platform whose central object is not the student record, the invoice, or the class schedule, but the **student's continuously tracked Quran learning journey**, and which connects student, teacher, parent, supervisor, and center around that journey.

Everything else in the system (administration, finance, scheduling, courses, live classrooms, notifications, reports) exists to serve the loop:

```
Student learns → practices → teacher evaluates → system records
→ retention changes → revision is scheduled → teacher reviews
→ parent sees meaningful progress → supervisor sees institutional health
→ student continues improving
```

## 1.2 Why this is not "ERP for Quran centers"

An ERP models a center as an organization: people, rooms, money, time. It answers "who is enrolled, who paid, who attended".

This platform models a center as a **learning system**. It answers questions an ERP structurally cannot:

| Question | Requires |
|---|---|
| What has this student memorized, and how strong is each part today? | A per-Ayah state model with history (the Quran Memory Map) |
| What should this student revise today, and why? | A retention model plus a policy-driven planner |
| Where does this student repeatedly confuse verses? | Mistake events linked to Ayat, Mutashabihat pairs, and confusion tracking |
| Is the student ready for more new memorization, or overloaded? | Velocity, revision compliance, and retention trend signals |
| Is this Halaqah, teacher, or branch actually producing learning outcomes? | Aggregation of the above across the org tree |
| Which students are at risk of dropping out? | An intervention engine fed by attendance, volume, mistakes, and teacher concern |

The administrative modules are still built properly, because centers will not adopt a platform that cannot handle fees and attendance. But they are **peripheral** modules around a **learning core**, and the architecture, data model, and roadmap reflect that priority.

## 1.3 Problem definition

Today, Quran centers run on a mix of:

- paper registers and teacher notebooks (the actual Hifz record lives in a teacher's head or notebook and is lost when the teacher leaves),
- generic school ERPs (attendance and fees, but "Quran progress" is one text field or "current Surah"),
- WhatsApp groups for parents (noise, no structure, privacy problems with minors),
- consumer Hifz apps (individual, not institutional; no teacher authority; some use AI in ways that make scholars nervous),
- Zoom links for online classes (no shared Mushaf, no assessment during the class, recordings retained by default, no attendance integration).

The consequences:

1. **No retention memory.** Centers track what was *memorized*, not what is *still retained*. Students finish a Juz and quietly lose it.
2. **Revision is unplanned.** The most important educational activity (Muraja'ah) is left to intuition and the student's willpower.
3. **Teacher knowledge is not portable.** A student who changes Halaqah, branch, city, or country restarts from the teacher's guess.
4. **Parents see attendance, not learning.** They cannot tell whether their child is improving.
5. **Supervisors cannot see institutional health.** They see enrollment and fees, not learning outcomes.
6. **Online classes are bolted on.** Video is a link, not a classroom.
7. **Safety is inconsistent.** Minors' audio and video are recorded and kept by default; AI features are added without a doctrinal safety boundary.

## 1.4 Primary personas

| Persona | Snapshot | What they need most |
|---|---|---|
| **Sheikh Ahmad, Halaqah teacher** | 12 students, 5 days/week, 90 minutes, tablet or phone in hand, no time for admin | A Tasmee' screen that records a recitation evaluation in seconds; automatic revision assignment |
| **Ustadha Maryam, online 1:1 teacher** | Teaches 20 students in 4 countries from home, 30-minute slots | Reliable low-bandwidth audio, shared Mushaf, instant assessment after each session, timezone-safe scheduling |
| **Yusuf, 11, student** | Memorizing Juz 29, attends a mosque center after school | A calm app that says "today: this, revise: that", plays a verified reciter, shows progress without gamification pressure |
| **Fatimah, 24, post-Hifz student** | Completed Hifz 2 years ago, worried about forgetting | A long-term revision cycle across 30 Ajza', weak-region detection, periodic full assessments |
| **Umm Yusuf, parent** | Two children in the same center, works full time | One weekly answer: did they attend, what did they memorize/revise, is it improving, what does the teacher say, is a fee due |
| **Abu Khalid, Quran supervisor** | Oversees 8 teachers, 90 students in one branch | Who is falling behind, which teacher is overloaded, which Halaqah underperforms, drill-down to a student's weak pages |
| **Sarah, center admin** | Runs enrollment, waiting lists, fees, certificates for a 400-student center | Clean ERP-style admin, reports, exports, bulk operations |
| **Dr. Hassan, organization owner** | 6 branches in 2 countries, board reporting, donor reporting | Cross-branch outcome metrics, finance roll-up, branding, module control |
| **Bilal, finance employee** | Invoices, receipts, scholarships, expense entry | Finance that works without ever exposing Quran assessment details |
| **Platform operator** | Hosts the cloud version or self-hosts for a charity federation | Tenant provisioning, Quran Core releases, observability, cost control |

## 1.5 Primary user journeys (summary)

Detailed journeys are in `03-users-and-journeys.md`. The headline journeys:

1. **Daily Halaqah loop (in person).** Teacher opens today's Halaqah → attendance → taps a student → sees assigned Sabaq/Sabqi/Manzil → student recites → teacher taps mistakes on the Mushaf → marks pass/repeat → next student. System updates the Memory Map, retention, and tomorrow's plan; the parent gets a summary that evening.
2. **Online 1:1 recitation class.** Student joins from the app → waiting room → teacher admits → shared Mushaf follows the teacher → same Tasmee' workflow inside the live class → session assessment → homework → nothing recorded when recording is off.
3. **Student self-practice.** Student opens "today" → listens to a verified reciter → practices with hints (verified text/audio only) → optional self-recording with conservative mismatch detection → uncertain items go to the teacher's review queue.
4. **Post-Hifz retention, year 3.** The planner cycles all 30 Ajza' according to the center's policy; weak pages surface; a supervisor schedules a quarterly assessment; the student never "graduates out" of the system.
5. **Parent weekly report.** Attendance, new memorization, revision, retention trend, teacher note, fee status, upcoming exam. Multiple children under one account.
6. **Supervisor intervention.** Early-warning flags a student → supervisor reviews signals → assigns action (teacher follow-up, plan change, parent contact, move Halaqah) → outcome tracked.
7. **Enrollment to first class.** Inquiry → waiting list → placement assessment → Halaqah assignment → fee plan → first session, with consent capture for minors.
8. **Institution transfer.** Student exports a portable Quran Learning Record → new institution imports it → the new teacher sees the Memory Map and history from day one.

## 1.6 Competitive landscape

See `docs/research/competitive-landscape.md` for the sourced research. Summary of the categories and their structural gaps:

| Category | Examples | What they do well | Structural gap |
|---|---|---|---|
| Arabic-market Tahfiz management SaaS | Saudi charity platforms, Halaqah management systems | Halaqah rosters, daily Sabaq/Muraja'ah logging by page, attendance, points | Progress is logged, not modeled: no per-Ayah retention state, no adaptive planner, closed source, single-country assumptions, Hafs-only |
| Consumer Hifz apps | AI-assisted recitation apps, memorization trackers | Individual practice, ASR mismatch hints, streaks | No institution, no teacher authority, no parent/supervisor layer; gamification; AI claims vary in caution |
| Online Quran academies | Tutor marketplaces and academies | Scheduling, payments, tutors | Video is Zoom, assessment is off-platform, no Memory Map, recordings retained |
| Generic school ERP / LMS | OpenEduCat, Fedena, Gibbon, Moodle, Frappe Education | Mature admin, finance, LMS | Quran is a text field; no Mushaf, no Ayah model, no retention |
| Open-source Quran data/apps | Quran.com, QUL, Quran Android, Tarteel open repos | Verified text, layouts, audio, fonts | Not institutional platforms; excellent foundations to build on |

**Nobody currently combines**: per-Ayah retention modeling + institutional multi-tenancy + teacher-authoritative workflows + portable learning record + open source + built-in non-recorded live classroom + doctrinal AI safety boundary. That combination is the product.

## 1.7 Core differentiators

1. **Quran Memory Map with history**: every Ayah has a measurable, explainable state, and the state's history is retained.
2. **Retention Engine**: deterministic, explainable, policy-driven, works without AI.
3. **Adaptive planner with a Learning Policy Builder**: centers encode their own methodology; the teacher always has the final say.
4. **Two-tap Tasmee' workflow**: recording a normal evaluation costs the teacher seconds, not the Halaqah.
5. **Sacred Content Boundary**: an immutable, versioned, checksummed Quran Core; AI can never become a source of Quran text.
6. **Live-only classroom by design**: a purpose-built Halaqah classroom with shared Mushaf and recording disabled at the platform level.
7. **Portable Quran Learning Record**: an open JSON specification so students keep their history across institutions.
8. **Open source, self-hostable, cheap to run**: single-VPS deployment for a small center.
9. **Parent experience built around six questions**, not dashboards.
10. **Multi-Riwayah architecture** with Hafs as the verified default.

## 1.8 Name suggestions

Naming criteria: short, pronounceable in Arabic and English, meaningful to the domain, not decorative, not already a large brand in the Arabic software market, available as a GitHub org, and evocative of the product's principle that Quran is received from a human teacher.

| Name | Arabic | Meaning | Fit | Risk |
|---|---|---|---|---|
| **Talaqqi** (recommended) | تَلَقِّي | "Receiving" the Quran directly from a teacher; the traditional transmission method | Encodes the product's central safety principle: technology supports human transmission, never replaces it. Distinctive. | Slightly harder for non-Arabic speakers on first read; explain once |
| Sanad | سَنَد | Chain of transmission; also "support" | Strong metaphor for continuity of a student's record across institutions | Common commercial brand name in the Arab world (finance, government services); trademark conflicts likely |
| Itqan | إتقان | Mastery, precision | Matches the retention/mastery model | Widely used by existing Tahfiz platforms and companies |
| Lawh | لَوْح | The wooden tablet used in traditional Quran schools | Short, warm, historical | Meaning is opaque outside West/North Africa and the Gulf |
| Maqra'ah | مَقْرَأة | A Quran reading school/circle | Precisely the domain | Long, harder transliteration, used by several Egyptian platforms |
| Rawi | رَاوِي | Narrator/transmitter | Short, global | Generic; used by media brands |

**Recommendation:** ship as **Talaqqi** (working repo name `talaqqi`), with the tagline *"Open-source infrastructure for Quran education"*. Tenants brand their own instance; the platform name stays in the footer and the developer ecosystem. Trademark and domain availability must be checked before public launch.

## 1.9 Quran and religious safety principles (product-level)

These are product commitments, restated technically in `07-religious-ai-safety.md`:

1. **Quran text has one source**: the read-only, versioned Quran Core. No service, admin, or model can write to it.
2. **Quran audio has one source**: verified recordings of real, named reciters with provenance. Generative TTS is never used for Quran.
3. **Authority stays human**: correctness of Tajweed and Makharij, Ijazah, religious rulings, Hadith authenticity, and authoritative Tafsir are decided by qualified people, never by the system.
4. **Metrics are educational, not religious.** A retention score describes recall stability, not the religious status of a recitation.
5. **Uncertainty means do less.** Automated systems express uncertainty and defer to teacher review rather than guess.
6. **Provenance is visible.** Every content item shows whether it is canonical text, a scholarly source, center-created material, or AI-generated assistance.
7. **AI is optional and replaceable.** The full platform operates with AI disabled.
8. **Minors are protected by default.** Minimal data, guardian consent, no unnecessary media retention, restricted messaging.

## 1.11 Language decision

The platform is **Arabic-first**: Arabic is the default UI language and RTL the base layout on every surface (admin web, mobile apps, notifications, reports, certificates). **English is fully supported** as the second language, selectable per tenant, per branch, and per user. Additional languages follow through community translation. Quran text is always rendered from the Quran Core regardless of the UI language.

## 1.10 What "done" looks like for the MVP

A small center can, on a single VPS or the managed cloud:

- enroll students and teachers, create Halaqat, take attendance,
- run daily Tasmee' with Ayah-level mistake capture on a verified Hafs Mushaf,
- see each student's Memory Map, retention, and an auto-generated Sabaq/Sabqi/Manzil plan governed by the center's policy,
- send parents a weekly report,
- give supervisors an on-track / behind / needs-attention view,
- run a live 1:1 or group class with a shared Mushaf and recording disabled,
- collect fees and issue receipts,

with everything above enforced by backend permissions and tenant isolation, and with a CI suite that fails if a single character of Quran text changes unintentionally.
