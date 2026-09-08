# Research — Competitive Landscape (accessed 2026-09-08)

Facts come from fetched pages or search snippets (flagged); vendor-authored comparisons are named as such. Items not verifiable are listed at the end.

## A. Halaqah / Quran-center management systems

### Arabic market (Gulf, Maghreb)

| Product | Vendor / market | Model | Quran-progress granularity | Retention/revision engine | Parent portal | Live built-in | Finance | Pricing | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Utrujja الأترجة (utrujja.com) | Claims 500+ orgs, 30+ countries | SaaS | "memorization & revision monitoring"; page/ayah level not stated | Manual logging, tests | n/s | Yes (virtual classroom) + course e-commerce | Course sales | Demo | Broadest Arabic vendor found; "لبيب" AI help assistant |
| Tahfez تحفيظ (tahfez.net) | Nuzum Al-Asr; KSA/UAE/EG/JO | SaaS | Digital records; granularity n/s | "المحفظ الذاتي" self-recitation helper (details n/s) | Yes | Zoom/WhatsApp integration | n/s | Not public | Homepage counters at 0 |
| Injaazy إنجازي | KSA/KW/UAE | SaaS + 3 apps | Listening/review plans; ayah n/s | Plan-based counting | Guardian app | n/f | n/s | Not public | 25 circles / 233 students shown |
| Halqaat حلقات | Mosques/waqf | SaaS + Android | Daily amount + revision + grade + note | Manual; reports; honor boards | Yes | n/f | n/f | Not public | QR check-in |
| Mue3n مُعِين (mue3n.com) | Saudi | SaaS | Daily new + revision entries with rating | Manual; points; competitions | WhatsApp notifications | n/f | n/f | **SAR 150/mo (1 circle) · 400 (5) · 800 (unlimited)** | Only Arabic vendor with public pricing |
| Rased راصد | In-house, Zulfi Tahfiz charity | Internal | Daily records | Manual | Yes | n/f | n/s | Not sold | Charities still build in-house |
| MOIA Quran Associations system (moia.gov.sa) | Saudi ministry | Government registry | Associations, circles, students, exams, inspections | None | No | No | No | N/A | Regulator registry; no vendor integrates with it |
| Itqan Maqra'ah (itqan-quran.com) | Maknoon charity academy | Academy, not SaaS | Programs incl. ijazah track | Teacher-led | Registration | Remote circles | Donations | Symbolic | "منصة إتقان" is an academy, not a platform |
| Quraan.me قرآني | US-registered, Arabic B2C | Academy w/ own platform | Personalized plan, per-session reports | AI tutor "رُؤًى" (details n/s) | Family account | **In-platform video, auto-recorded** | Subscriptions | Not public | Closest Arabic "custom classroom + AI progress" |
| VP Developer (Algeria) | Quran associations | Web + iOS/Android | Levels & achievement | Manual | Yes | n/f | **Yes** (subscriptions, receipts, revenue/expense) | 1 month free then quote | Strongest finance module among Arabic tools |
| IBIZA Dev (Algeria) | Free desktop + cloud sync | Free, not open source | Daily amount, review, grade, by surah/juz | Manual | Web portal + WhatsApp | No | Yes | Free | AR/FR/EN "free incumbent" in Maghreb |

Unverified/empty: Ethaaf, الحلقة الذكية (qrattel.com), نظام تاج.

### Malaysia / Indonesia

| Product | Model | Notes |
|---|---|---|
| SIATA (siakadtahfidz.com) | SaaS, 100+ pesantren | Setoran/muroja'ah logs, exams, tuition + non-tuition finance, parent real-time |
| Shafwah | SaaS, 15+ pesantren | **IDR 99k/mo (≤500 santri) · 199k (≤1,000) · 499k (≤2,000)**; setoran logging, ranking |
| SIPond | SaaS + parent app, 50+ pesantren | Finance-led (virtual accounts, SPP, allowances) with tahfidz module |
| Tahfiz Hub (tahfizhub.com) | **Multi-tenant SaaS** (isolated tenant per school) | **Sabaq/sabqi/manzil with grades; "every ayah, page and juz recorded"**; proprietary; pricing not public. Closest purpose-built multi-tenant tahfiz SIS |
| Tahfiz Online AKMAL | Academy | Zoom; RM1,200/mo full-time |
| Research note | ResearchGate 2024 | Malaysian tahfiz institutions increasingly use Moodle, Padlet, Kahoot (generic tools) |

### UK / North America / South Asia

| Product | Market | Hifz granularity | Finance | Pricing |
|---|---|---|---|---|
| IlmFlow (ilmflow.co.uk) | UK, new | **Sabak / Sabak Para / Dhor daily with juz, portion, mistake count, quality rating**; cross-year Juz-30 tracking | Fees + Stripe; **UK payroll (PAYE/NI/pensions)** | **£0.25/active student/mo, £15 min** |
| MaktabMate | UK | Juz-by-juz with sabaq/sabqi/manzil + formal juz tests | Invoices, sibling discounts | £4.99 (10) · £12.49 (100) · £19.99 (unlimited) |
| IBEAMS (ibeuk.org) | UK, **200+ institutions** | "Student Diary" add-on | Fees, invoicing, expenses | £15/£30/£60 per month + £10 diary (per IlmFlow guide) |
| MadrasahConnect | UK/intl | Daily Sabaq/Sabaq Para/Dhor with line counts, mistakes (snippet) | Fees | n/s |
| Ilmify (ilmify.app) | India; India/UAE/KSA; 100+ institutions | Hifz & Nazra tracking; claims 3-stream | Fee collection, scholarships, zakat/donations | **$35 or $70/institute/mo; $1 or $3/student/mo** |
| Qaf School (qaf.app) | US, 8 countries | Quran homework with audio submissions (≤10 min) | Payment tracking | Free (proprietary) |
| Hidayah, e-Maktab, MadrasaSIMS, Alif Cloud, Labbaik, Raziil, Sudoor | UK | Various; Sudoor "Sabaq/Sabqi/Manzil" (vendor guide only) | DD/Stripe | Various |
| Masjidbox, My-Masjid | Mosque suites | **No hifz module** | Donations | Free–€62/mo |

## B. Consumer Hifz apps

| App | Core | Retention/SRS | Teacher/parent side | Pricing | AI posture |
|---|---|---|---|---|---|
| **Tarteel** | ASR listens while reciting; mistake detection (missed/incorrect/skipped words); hide-verse; historical mistakes; journey planning; Test Mode (v5.81.1, Aug 2026) | Planning + mistake history; **no forgetting-curve/SRS claimed** | **None found** (no institutional plan) | US IAP $12.99/mo, $99/yr; regional pricing; family plan | Non-generative ASR; accuracy "paramount" but no published error rates or tajweed claims; Islamweb fatwa 510187: permissible if endorsed by qualified reciters; non-Hafs support not found |
| Quran Companion (quranacademy.io) | Daily new ayat + scheduled reviews; group challenges | **Yes — ayah-level spaced repetition** | None | Free reading; lifetime purchase | — |
| SABR | Duolingo-style path; ~20 reps/ayah | Yes (ayah-level) | None; SABR's blog: "No app offers integrated teacher/parent monitoring dashboards" | Free + premium | Claims "AI recitation coach… tajweed scoring" without validation |
| Sadr (sadr.app) | Sabaq / Sabqi (3–21 d) / Manzil (>21 d) scheduler | **Yes, explicit intervals** | None | Free | Voice "pronunciation feedback" |
| Retain Quran | AI mistake detection + SRS flashcards | Yes | None | Free | — |
| Al Muhaffiz | Traditional sabaq–sabqi–manzil workflow | Method-based | None | Free | No AI |
| Ayat (King Saud University) | Mushaf Madina, Tajweed, **Warsh** text + audio | No SRS | None | Free | Official/academic |
| Quranly | Habit tracker | No memorization tracker | None | $4.99/mo | No AI |
| Mahfuz (OSS, MIT, 110★) | Reader + hifz tracker + SRS + khatm groups | Basic | None | Free | — |

## C. Online academies — stack and price

| Academy | Live stack | Pricing |
|---|---|---|
| Qutor | Own credit-based classroom | Tutor hourly rate; platform fee 20% or $1 min |
| Studio Arabiya | **Zoom** + portal | 1:1 from $55; K-12 $375/semester |
| Riwaq Al Quran | n/s | $32/mo for 8×30 min (≈ $4/class) |
| Quran Oasis | unspecified | $38–83/mo |
| Al Quran Companion (academy) | n/s; **sells class recordings** | $25.99–55.99/mo |
| Quraan.me | In-platform, auto-recorded | Not public |
| Bayyinah TV | VOD | $12/mo |

Takeaway: every academy found runs on Zoom or an unspecified white-label, bills per 30-minute slot (commodity ≈ $4–7 per 30-min 1:1), and treats recording as a feature. None advertises a no-recording or audio-only-for-women mode.

## D. Generic OSS SIS/LMS and Quran forks

Frappe Education (628★, active): no tahfiz app. Moodle: only a "Quran Recitation" audio block; no hifz-tracking plugin. OpenEduCat, Gibbon, RosarioSIS: no Quran forks. Purpose-built OSS attempts (Qara-a, Hifztrack, Alhalaqa, Website-Tahfiz-Al-Hafiz, QuickTahfizh) are ≤ 2★ hobby projects.

## E. Open-source Quran projects worth building on

| Repo | Stars | License | Covers |
|---|---|---|---|
| quran/quran_android | 2.4k | GPL-3.0 | Reader; Qaloon & Naskh flavors; separate Warsh app |
| quran/quran.com-frontend-next | 1.9k | MIT | Quran.com web; bundles QCF v1/v2/v4 fonts |
| quran/quran-ios (QuranEngine) | 586 | Apache-2.0 | iOS reader engine |
| TarteelAI/quranic-universal-library (QUL) | 1.0k | MIT (code) | Scripts, mushaf layouts, translations, tafsir, word-level audio segments, mutashabihat, morphology; audit logs on corrections |
| DigitalKhatt (madinafont, indopakfont, alshamiyafont) | — | OFL-1.1 fonts; AGPL tooling | Parametric Madinah/IndoPak mushaf fonts |
| cpfair/quran-align | 257 | MIT + CC BY 4.0 data | Word timestamps |
| yazinsai/quran-validator | 177 | MIT | Validates LLM-quoted ayat against Uthmani text |
| yayaiu6/Real-Time-Quran-recitation-tracker-System | 134 | MIT | Real-time word alignment + error detection |
| theilgaz/mahfuz | 110 | MIT | Reader + hifz tracker + SRS |
| adelpro/open-mushaf, open-tarteel | small | MIT | KFGQPC page images; reciter filter by Hafs/Warsh/Qalun |

GitHub topics: `hifz` 23 repos, `quran-memorization` 7, `tahfidz` 4, `tahfiz` 0; none above 7★.

## F. AI safety positioning and incidents

- Tarteel: ASR/alignment, not generation; no published accuracy or tajweed claims; declines model details citing IP.
- Quran.com / Quran Foundation: Quran MCP "to ground AI assistants in canonical text"; quran.ai and Maani (AI tadabbur "grounded in classical tafsir… under supervision of scholars"). Posture is grounding, not a stated prohibition.
- SABR and Quraan.me claim AI evaluation without published limits.
- Evidence: IslamicMMLU (arXiv 2603.23750, 2026): Quran-track accuracy across 26 LLMs ranged 32.4%–99.3%; RAG in Quranic Studies (arXiv 2503.16581): ungrounded responses deviate from sources; Journal of Digital Islamicate Research 3(1) 2025: chatbots misattribute verses/hadith; "Fabricating Holiness" (arXiv 2508.07845): fabricated hadith a leading misinformation category; quran-validator exists because LLMs "subtly change words, miss diacritics, or combine verses".
- Text-integrity incidents: Muslim World League warning on free Quran apps with missing letters (2016); Pakistan PTA blocked ~21 Quran apps/sites for fake content (Feb 2023); Pakistan MoRA warnings under the 1973 Act (2023); Jordan pulled misprinted copies.

## G. Gap verification

| Claimed gap | Verdict |
|---|---|
| Per-ayah retention modeling inside an institutional system | **Confirmed**: institutional tools log amounts and grades manually; consumer SRS apps have no teacher/parent side; nobody bridges both |
| Portable learning record | **Confirmed**: no export standard found; Quran.com OAuth syncs only among its own connected apps |
| Open-source multi-tenant Halaqah management | **Confirmed**: only multi-tenant product (Tahfiz Hub) is proprietary; OSS candidates are hobby-scale |
| Riwayat beyond Hafs in memorization/management | **Partly confirmed**: text/audio/fonts exist (quran_android, Ayat, DigitalKhatt, QUL); no memorization or management product states non-Hafs support |
| Non-recorded / privacy-first live classes | **Confirmed as unmarketed**: all academies use Zoom or auto-record |
| Finance/payroll for Arabic centers | Partial: most Arabic tools lack finance; only IlmFlow does payroll (UK) |
| Regulator integration (MOIA registry) | Confirmed gap |
| Published AI accuracy/verification policy | Confirmed gap; Quran.com MCP grounding is the nearest |
| Offline-first | Partial: only Ilmify claims offline |

## H. Names that could not be verified

نافس, منصة الحلقات, برنامج مقرأة (software), حافظ (SaaS), منصة زادي, Mishkat, رتل (management SaaS), Moaalem, eTahfiz (Malaysia), Alfa Khidmat, Mosque Suite, MyMasjid (hifz), Islamic School ERP, Skolera, Hafizon, Wird (hifz), Hadi, HifzTracker (commercial), Quran Host, QuranLive, Salam Tutor, Ilm Hub, "Tarteel for institutions".

## Sources (accessed 2026-09-08)

utrujja.com/ar/coteries; tahfez.net; injaazy.com; halqaat.com; mue3n.com; rased.qz.org.sa; moia.gov.sa/Systems/QuranAssociations; itqan-quran.com; quraan.me; vpdeveloper.dz/quran-association/; ibizadev.com/quran.html; siakadtahfidz.com; shafwah.tsirwah.com; sipond.id; tahfizhub.com; tahfizonline.com; ilmflow.co.uk (+ resources guide); maktabmate.co.uk; ibeuk.org; madrasahconnect.com; ilmify.app (+ blog); thendorsement.com comparison; qaf.app; masjidbox.com/pricing; my-masjid.com; apps.apple.com Tarteel listing; support.tarteel.ai premium articles; tarteel.ai/blog (mistake detection; ML journey); islamweb.net/en/fatwa/510187; quranacademy.io/blog; get-sabr.com (+ blog); sadr.app; Retain Quran App Store; Quranly App Store; Al Muhaffiz App Store; simplyislam.sg; play.google.com Ayat; quran.ksu.edu.sa; qutor.com/pricing; studioarabiya.com; riwaqalquran.com/pricing/; quranoasis.com; alqurancompanion.com/pricing; bayyinah.com; github.com/frappe/education; github.com/orgs/quran/repositories; github.com/TarteelAI/quranic-universal-library; github.com/DigitalKhatt; github.com/cpfair/quran-align; github.com/yayaiu6/Real-Time-Quran-recitation-tracker-System; github.com/yazinsai/quran-validator; github.com/theilgaz/mahfuz; github.com/adelpro/open-mushaf; github.com/topics/{hifz,tahfidz,quran-memorization}; quran.com/developers; quran.ai; maani.tech; arxiv.org/abs/2603.23750; arxiv.org/abs/2503.16581; arxiv.org/html/2508.07845v1; thejamiat.co.za (Dec 2025); aa.com.tr (Dec 2016); techx.pk PTA block; app.com.pk MoRA warning; gulfnews.com Jordan misprint.
