# Research — Arabic/Quran Fonts and Child-Privacy Law (accessed 2026-09-08)

## Part 1 — Fonts

### KFGQPC (King Fahd Complex) fonts

Caveat: every qurancomplex.gov.sa host refused connections during research; the official terms page could not be read. Findings rely on the embedded font license string (ScanCode LicenseDB `kfgqpc-uthmanic-script-hafs`, category "Proprietary Free"), the "Usage Rights" clause quoted from the official Hafs font page in Wikimedia Phabricator T301871, and mirrors.

- Current developer package (mirrors of qurancomplex.gov.sa/en/techquran/dev/): Unicode fonts + text (CSV/JSON/SQL/XML) for 9 narrations: Hafs Smart v8, Hafs (UthmanicHafs1 Ver18), Warsh v10, Shouba v8, Qaloon v10, Doori v9, Soosi v9, Bazzi v7, Qumbul v7. Older set: KFGQPC Uthman Taha Naskh, KFGQPC Uthmanic Script HAFS, per-page QCF fonts (QCF_P001–P604).
- Embedded license string: "This Font is the property of King Fahd Glorious Quran Printing Complex, and may not be reproduced, modified without the express written approval of King Fahd Glorious Quran Printing Complex."
- Official "Usage Rights" (quoted): "available for copying, distribution and usage free of charge in the personal, commercial and all individual fields, as well as, government bodies, entities and civil organizations works."
- Wikimedia declined to add the fonts (2023) because they lack an open-source license.

Verdict: free, commercial OK, redistribute **unmodified**; no modification/subsetting/conversion; not OSI-free. Bundle in a clearly marked `fonts/kfgqpc/` folder with `LICENSE-KFGQPC.txt`, or load from the operator's CDN. Confirm with the live terms page or by email before shipping.

### QCF per-page fonts and QUL

QUL lists 22 font resources (QPC V1/V2/V4 Tajweed, QPC Hafs, me_quran, Indopak Nastaleeq, KFGQPC Nastaleeq, Digital Khatt V1/V2/Indopak, QPC Warsh/Douri/Sousi/Qaloun/Shuba) and 12 mushaf layouts. **No license field on any font page**; QUL is a redistribution point, each font keeps its upstream license. quran.com-frontend-next (MIT) bundles QCF v1/v2/v4 and UthmanicHafs1Ver18 without a font-specific notice (precedent, not clearance). quran_android bundles UthmanTN1Ver10 and Kitab; its data note says content is "typically CC BY-NC-ND".

### Open and semi-open Quran text fonts

| Font | License | Uthmani suitability | Verdict |
|---|---|---|---|
| Amiri / Amiri Quran / Amiri Quran Colored (aliftype/amiri; Google Fonts) | OFL | Full Quranic annotation marks (Unicode 6.0); dedicated Quran face; COLR/CPAL colored marks | **Yes** |
| Scheherazade New (SIL) v4.500 | OFL | Complete Arabic Unicode coverage; `cv76` superscript alef sizes, `cv78` sukun forms, `cv80` end-of-ayah styles | **Yes** |
| Harmattan (SIL) | OFL | Warsh-style (West Africa); same feature set | **Yes** (best OFL choice for Warsh display) |
| Kitab (nuqayah/kitab-font) | OFL | Scheherazade-based, full Arabic repertoire, Quran-oriented | **Yes** |
| Noto Naskh Arabic / Noto Sans Arabic | OFL 1.1 | General text / UI; no Quran-specific alternates documented | **Yes** (not for mushaf fidelity) |
| Lateef, Katibeh | OFL | Secondary / headings | **Yes** |
| **DigitalKhatt Madina** (madinafont; also oldmadinafont, alshamiyafont, indopakfont) | **OFL-1.1** (tooling AGPL/MIT) | Parametric CFF2 variable font matching the 1421H Madinah mushaf; renders with plain `@font-face`; page-faithful justification needs digitalkhatt-js (MIT) + WASM HarfBuzz | **Yes** (glyphs production-grade; layout integration heavier) |
| me_quran (Meor Ridzuan) | Non-commercial; "contact author" | Mimics 1405H mushaf | **No** without permission |
| Uthman Taha Naskh (KFGQPC) | KFGQPC terms | Naskh text font | Attribution-only / no-derivatives |
| AlQuran IndoPak (marwan/indopak-quran-text) | "DO NOT SELL, MANIPULATE, DISTRIBUTE WITHOUT CREDITS OR TAMPER" | Indopak with pause marks | Attribution-only / no-derivatives |
| Noorehuda / Noorehira (noorehidayat.org) | "No Copyright Notice… feel free to download and use"; link appreciated | Indopak Unicode | Yes (document the quote in NOTICE) |
| PDMS Saleem Quran, Al Qalam Quran Majeed, Mehr Nastaliq | No license text found | Indopak / Nastaliq | **Unclear — do not bundle** |

Unicode reference for Uthmani features: U+0670 superscript alef; U+0671 alef wasla; U+06D6–06DC pause marks; U+06DD end of ayah; U+06DE rub el hizb; U+06E5/06E6 small waw/yeh; U+06E9 sajdah; U+08E2 disputed end of ayah. Only QCF page fonts and DigitalKhatt reproduce Madinah page layout; OFL text fonts shape Unicode correctly but do not replicate the printed page.

### UI Arabic fonts with Latin pairing (all OFL, verified in google/fonts METADATA.pb)

IBM Plex Sans Arabic; Noto Sans Arabic (variable); Cairo (variable, slant); Tajawal; Readex Pro (variable); Rubik (variable + italic, Hebrew/Cyrillic); Vazirmatn (variable); Almarai; Baloo Bhaijaan 2; Alexandria; Changa; Markazi Text; Harmattan.

### Recommendation

1. Default Uthmani text font: DigitalKhatt Madina (fully open) as the repo default; KFGQPC Hafs Smart/UthmanicHafs as an operator-installable pack with its own NOTICE.
2. Page-faithful mushaf mode: QCF v1/v2/v4 loaded from the operator's CDN with `LICENSE-KFGQPC.txt`, never subset or converted.
3. Fallbacks: Amiri Quran (+Colored), Scheherazade New, Kitab, Harmattan (Warsh).
4. Avoid bundling: me_quran, PDMS Saleem, Al Qalam, Mehr Nastaliq; AlQuran IndoPak only unmodified with credits.
5. UI: IBM Plex Sans Arabic or Readex Pro for Arabic UI, paired with a Latin sans; Noto Naskh Arabic for long-form Arabic reading.

## Part 2 — Child-privacy law orientation (not legal advice)

Legend: [V] verified on regulator/primary/major law-firm page; [S] secondary only; [?] unverified/conflicting.

| Jurisdiction | Law | In force | Child age / consent | DPO | Breach notice | Cross-border / localization |
|---|---|---|---|---|---|---|
| USA | COPPA Rule as amended (FR 22 Apr 2025) | Eff. 23 Jun 2025; comply by 22 Apr 2026 [V] | <13; verifiable parental consent; separate VPC for third-party disclosure; voiceprints now biometric PI; written retention + security program; school-authorization exception **not** codified | No | State laws | None |
| EU | GDPR Art. 8; DSA Art. 28 minors guidelines (14 Jul 2025) | 2018 / 2025 [V] | 16 default; 13 (BE, DK, EE, FI, LV, MT, PT, SE), 14 (AT, BG, CY, IT, LT, ES), 15 (CZ, FR, GR), 16 (HR, DE, HU, IE, LU, NL, PL, RO, SK, SI) | Art. 37 | 72 h | Ch. V; DPIA expected (children + monitoring + scale + new tech) |
| UK | UK GDPR; Children's Code (AADC); Online Safety Act 2023 | AADC enforced 2 Sep 2021; OSA child codes 25 Jul 2025 [V] | 13 for consent; Code covers <18: high-privacy defaults, minimisation, profiling off | As GDPR | 72 h | Adequacy/IDTA |
| Saudi Arabia | PDPL M/19 amended M/148; Implementing Regs; children rules 20 May 2025 | 14 Sep 2023; grace ended 14 Sep 2024 [V] | Guardian consent with verified guardianship; children rules age threshold [?]; **religious beliefs are sensitive data** | Mandatory for large-scale monitoring / core sensitive data | 72 h to SDAIA | Transfer regs + Saudi SCCs/BCRs; adequacy list unpublished (Mar 2026); no general localization; fines up to SAR 5m |
| UAE | Fed. Decree-Law 45/2021; Wadeema Law 3/2016; Decree-Law 26/2025 Child Digital Safety | PDPL 2 Jan 2022; **Executive Regs still not issued as of Mar 2026** [V, contradicts vendor blogs] | Child <18 | High-risk | "Immediately" | Health data localized; DIFC/ADGM separate |
| Jordan | Law No. 24 of 2023 | 17 Mar 2024; grace ended 17 Mar 2025 [V] | Guardian consent for persons lacking capacity (majority 18) | Mandatory incl. when processing data of minors or transferring abroad | 24 h to subjects, 72 h to Unit | Prohibited unless adequate protection; fines JOD 1,000–10,000 (+JOD 500/day, cap 3% revenue) |
| Egypt | Law 151/2020 + Exec Regs Decree 816/2025 | Regs 1–2 Nov 2025; grace to ~1 Nov 2026 [V] | Children's data sensitive; guardian consent (Art. 12); reportedly <15 written consent [S] | Mandatory, registered with Centre | 72 h; subjects 3 days | Licence/permit from Centre for any transfer; foreign controllers need local representative |
| Pakistan | PDP Bill 2023 / 2025 redraft | **Not enacted** (May 2026) [V] | Draft: parental consent, age verification | Draft | Draft 72 h | Draft: critical data on Pakistan servers |
| Malaysia | PDPA 2010 + Amendment 2024 | Phased 1 Jan / 1 Apr / 1 Jun 2025 [V] | <18 guardian consent | Mandatory from 1 Jun 2025 (>20k subjects etc.) | 72 h (guideline) | Whitelist repealed; "substantially similar" test |
| Indonesia | PDP Law 27/2022; GR 33/2026 (effective ~16 Jan 2027) | 17 Oct 2024 [V] | <18 guardian consent | Large-scale/specific data | 3×24 h | Adequacy/SCC/BCR; public-scope ESOs store in Indonesia; DPA not yet formed |
| Turkey | KVKK 6698 as amended by 7499 | 1 Jun 2024 [V] | <18 parent/guardian | VERBIS registration | 72 h | Adequacy/SCC (5-day filing)/BCR; social media >1m users localized |
| Nigeria | NDPA 2023 + GAID 2025 (operative 19 Sep 2025) | [V] | <18; parental consent + age verification | Controllers of Major Importance | 72 h | Adequacy or instruments; fines higher of NGN 10m or 2% |
| Australia | Privacy Act; Children's Online Privacy Code by 10 Dec 2026; under-16 social media ban 10 Dec 2025 | [V] | Code <18; ban <16 (education services excluded per Rules) [S] | No | NDB scheme | APP 8 |
| Canada | PIPEDA (C-27 died Jan 2025); Quebec Law 25 | Law 25 phases 2022–2024 [V] | Quebec <14 parental authority | Quebec privacy officer | Real risk of serious injury | Quebec PIA before out-of-province transfers |
| India | DPDP Act 2023 + Rules 2025 (phases to May 2027) | [V] | <18; verifiable parental consent (DigiLocker tokens etc.); no tracking/targeted ads to children; edtech vendors do **not** inherit school relief | SDFs: DPO + DPIA | Immediate + 72 h | Government may restrict destinations |

### Video recording of minors in online classes

- EU/UK: recordings are personal data, often Art. 9 (religion visible in a Quran class); lawful basis per purpose; parental consent under the national Art. 8 age; DPIA expected; Children's Code demands high-privacy defaults and minimal retention; DSA guidelines recommend blocking screenshots/downloads of minors' content.
- US: audio/video with a child's face/voice is COPPA personal information (voiceprints explicitly biometric); VPC, retention limit, security program; sharing needs separate VPC; FERPA treats school-maintained recordings as education records; California SOPIPA binds K-12 operators directly; all-party-consent states require releases.
- Saudi/UAE: guardian consent with verified guardianship; religious belief sensitive; DPIA for monitoring persons lacking capacity; Wadeema Law protects <18 (reported Art. 26 bars publishing a child's image/name without parental consent [S]).

### Practical baseline for the platform

1. Guardian account holds consent; age gate per country (13 UK/EU-low; 14 Quebec; 16 DE/IE/NL; 18 KSA/JO/EG/MY/ID/NG/IN/PK).
2. Recording OFF by default with per-session notice; separate consent to share or publish anything.
3. Short retention schedules; no ads or profiling of minors anywhere.
4. DPIA template shipped with the project; 72-hour breach playbook (24 h to individuals for Jordan).
5. Self-hosting for jurisdictions with transfer licensing (Egypt) or localization pressure (Indonesia public sector, Pakistan draft, Turkey sectors).
6. Treat religious affiliation as sensitive data in every jurisdiction (Saudi PDPL explicitly).

Open items: Saudi children-rules age threshold; UAE Executive Regulations status; Wadeema Art. 26 wording; Egypt Regs children age bands; Jordan bylaws inventory; Australia SMMA education exclusion (Wikipedia only); DIFC child age.

## Sources (accessed 2026-09-08)

Fonts: scancode-licensedb.aboutcode.org/kfgqpc-uthmanic-script-hafs.html; phabricator.wikimedia.org/T301871; github.com/ibnhazm/KFGQPC; github.com/thetruetruth/quran-data-kfgqpc; github.com/nuqayah/qpc-fonts; github.com/quranwbw/qpc-fonts; vdemir/zekr README; qul.tarteel.ai/resources/font (+ /238, /249, /240, /245, /243, /242, /462, /247), /resources/mushaf-layout, /credits; github.com/quran/quran.com-frontend-next (public/fonts, src/utils/fontFaceHelper.ts); github.com/quran/quran_android; github.com/marwan/indopak-quran-text; github.com/aliftype/amiri; google/fonts METADATA.pb for the OFL families listed; software.sil.org/{scheherazade,lateef,harmattan}; github.com/notofonts/arabic; github.com/nuqayah/kitab-font; github.com/Tarobish/Katibeh; github.com/DigitalKhatt/{madinafont,oldmadinafont,indopakfont,visualmetafont,digitalkhatt-js}; urdulabs.com/fonts/me_quran; groups.google.com/g/zekr; pakdata.com/products/arabicfont; urdufonts.com; noorehidayat.org; cle.org.pk; unicode.org/versions/Unicode16.0.0/core-spec/chapter-9/.

Privacy: lw.com COPPA update; ftc.gov press release 16 Jan 2025; ftc.gov safe-harbor list; leginfo.legislature.ca.gov SOPIPA; euconsent.eu age table; ec.europa.eu WP248 rev.01; digital-strategy.ec.europa.eu DSA minors guidelines; ico.org.uk Children's Code; reedsmith.com OSA codes; gov.uk OSA explainer; dlapiperdataprotection.com (SA, UAE, JO, MY, ID, TR, NG); practiceguides.chambers.com 2026 (Saudi, UAE, Pakistan); clydeco.com (Saudi regs; Egypt Jan 2026); kslaw.com Saudi transfers; securiti.ai (Saudi DPO; Jordan; DIFC); lexismiddleeast.com (Saudi children rules; Egypt); icmec.org UAE legislation; abdullahfirm.com Jordan law; acc.com Egypt law text; bakermckenzie.com Egypt Jan 2026; legal500.com (Egypt regs; Pakistan); taypartners.com.my; pdp.gov.my; kk-advocates.com GR 33/2026; iapp.org Turkey 7499; kilinclaw.com.tr; mondaq.com GAID; ndpc.gov.ng GAID PDF; oaic.gov.au Children's Online Privacy Code; esafety.gov.au; mccarthy.ca; cfib-fcei.ca Law 25; ey.com DPDP Rules 2025; ksandk.com (children; edtech).
