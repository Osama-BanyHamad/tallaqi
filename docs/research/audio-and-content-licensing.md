# Research — Quran Audio, Tafsir, Hadith, and Corpus Licensing (accessed 2026-09-08)

Verdict key: **Yes** = permissive, safe to bundle · **Attribution-only** · **No-derivatives** (verbatim + attribution) · **No** · **Unclear — do not bundle**.

## A. Quran recitation audio

Headline finding: **no audio source was found whose rights-holder-issued license permits bundling famous-reciter recordings in an open-source repository.** Only *timing data* is openly licensed.

| Source | What it provides | License text found | Verdict |
|---|---|---|---|
| EveryAyah.com | Per-ayah MP3s for ~50 reciters/bitrates, page MP3s, zips, MD5s, timing files (`data/{Reciter}_{kbps}kbps/{SSS}{AAA}.mp3`) | No license on main page or data root; timing disclaimer says "(C) VerseByVerseQuran.com — You must link back… Full License at versebyversequran.com/site/license" (URL now 404). Directory names credit third-party sites (QuranExplorer, ketaballah, AudioIslam) | **Unclear — do not bundle**; timing files attribution-only (weak) |
| QuranicAudio.com (Quran.com family) | Surah-level MP3 for 181 reciters via `quranicaudio.com/api/qaris` and `download.quranicaudio.com/quran/{path}/{001..114}.mp3` | About page: "may be downloaded and used for personal use free of charge… you may not use these files for commercial purposes as many of these files have rules and regulations that prevent their sale" | **No** for bundling |
| mp3quran.net | 22 Riwayat via `mp3quran.net/api/v3/{reciters,riwayat,suwar,moshaf}` | Site and terms pages 403; no license found | **Unclear — do not bundle** |
| Quran Foundation Content API v4 | Recitations, audio files with `segments=true` word timestamps | Developer Terms (effective 2026-08-26): content "not sold, sublicensed, or redistributed"; cache ≤ 1 week unless Content Sync; datasets need written commercial license | **No** for bundling; API-consume only |
| QUL (qul.tarteel.ai) recitations | 133 recitations (58 segmented), ayah- and surah-level, JSON/SQLite segments, CDN `audio-cdn.tarteel.ai` (do not hotlink) | FAQ: "resources vary in their copyright status… review the licensing terms for each resource"; no per-resource license field; credits EveryAyah/QuranicAudio as sources | **Unclear — do not bundle audio**; segments derived from CC-BY data |
| cpfair/quran-align | Word-level timing JSON for 12 EveryAyah reciters (Abdul Basit ×2, Sudais, Shatri, Alafasy, Rifai, Husary ×2, Minshawi ×2, Tablawi, Shuraim) | MIT (code) + **CC BY 4.0** (data) | **Yes / Attribution-only** (timing only) |
| tarteel-ai/everyayah (Hugging Face) | 117 GB audio + text ASR dataset | Card says CC BY 4.0 / tag says MIT; no evidence Tarteel holds rights to relicense reciters' recordings | **Unclear — do not rely on the label** |
| AlQuran.cloud / Islamic Network CDN | ~28 verse-by-verse + 180 surah editions | Terms claim "Recitations are licensed to us by the reciters or their estates for free, non-commercial redistribution… copyrights lie with the reciters and they may ask you to remove the content" | **Unclear — do not bundle** (unverifiable third-party claim, take-down risk) |
| Internet Archive mirrors | Full sets | No rights fields | **No** |
| Alafasy official app terms | — | "audio… owned by Alafasy Berhad or licensed partners. Unauthorized use is strictly prohibited" | **No** (explicit reservation) |

Reciter status: Alafasy — rights holder Alafasy Berhad, no public license; Abdul Basit — Egyptian Radio / Sono Cairo lineage, no statement; Husary, Minshawi, Sudais, Shuraim, Basfar, Ayyub, Ajmi, Shatri, Rifai, Ghamdi, Muaiqly, Dosari — **unclear**, no documented permission found. Fatwa literature (British Fatwa Council; Islamweb 87644, 83969) supports that reserved rights on recordings must be respected; neighbouring rights apply to sound recordings regardless of the public-domain text.

**Platform policy derived from this:** the repository ships the audio index schema, the ingestion tool, a source list with license status, and a `license_status` gate; operators import reciters they have rights for; QF API streaming under its terms is a supported adapter; commissioning recordings or obtaining written permissions is the path to a bundled default reciter.

## B. Quran text and structure

(From Part 1 of the data-sources research; the summary agent's full Part 1 report was not returned before the budget ran out — the items below are the load-bearing facts recorded by the sub-agents. Re-verify Tanzil and KFGQPC terms before the first Quran Core release.)

| Source | Notes | Verdict |
|---|---|---|
| Tanzil.net Quran text | Uthmani/simple text; Tanzil license historically CC BY-ND 3.0-style (verbatim, attribution, no modification); metadata (juz, hizb, page, sajda) provided as separate files; **translations page states non-commercial only and forbids redistributing the list** | Text: **No-derivatives / attribution** (verbatim); translations: **No** |
| QUL text resources (Uthmani, QPC Hafs, Indopak, tajweed, layouts, word-by-word) | SQLite/JSON downloads; no per-resource license field; FAQ "varies" | **Unclear — confirm with Tarteel before public bundling**; treat page-layout data as attribution-only in practice |
| KFGQPC (qurancomplex.gov.sa) | Official Uthmani text, Hafs/Warsh/Qalun fonts, QCF page fonts | Site unreachable during research (ECONNREFUSED); terms **NOT VERIFIED** | **Unclear** until terms fetched |
| Quran.com API v4 | Text, layouts, words | Developer ToS: API-only, no redistribution | **API use only** |
| Quranic Arabic Corpus morphology v0.4 | POS/lemma/root for 77,430 words | GPL v3 + "verbatim copies… changing not allowed" header; attribution + link required | **Attribution-only** (ship unmodified file + separate patch layer) |
| Lane's Lexicon digitisation | CC BY-SA 3.0 (PDFs) / GPL-3 (LexiconDatabase) | **Yes / Attribution-ShareAlike** |
| quranwbw.com word-by-word | Proprietary to QuranWBW team | **No** |

## C. Tafsir

| Dataset | License | Verdict |
|---|---|---|
| QUL classical Arabic tafsirs (Tabari, Qurtubi, Ibn Kathir ar, Baghawi, Jalalayn ar, Razi, Muyassar, Saadi ar, Tahrir, Wasit) — SQLite/JSON, ayah-grouped | No per-resource license; underlying works public domain; digitised edition (KSU "Ayat"/quran.com lineage) unlicensed | **Unclear — attribution-only in practice; confirm with Tarteel** |
| QUL Ibn Kathir English (Darussalam abridged, Mubarakpuri) | Commercial publisher | **No** |
| QUL Jalalayn English (Aal al-Bayt / Feras Hamza) | altafsir.com: "© Royal Aal al-Bayt Institute… may not be reproduced… without prior permission" | **No** |
| Al-Mukhtasar (Tafsir Center, many languages) | None on QUL; Saudi charitable centre | **Unclear — ask publisher** |
| Quran.com API v4 tafsirs (20 editions) | Developer ToS (1-week cache, no redistribution) | **API use only** |
| spa5k/tafsir_api (122 editions, MIT) | MIT applied by aggregator, not rights holders; includes altafsir.com content | **Unclear — do not bundle** |
| Quran-Tafseer/tafseer_api (MIT code) | Data from Tanzil (non-commercial) and KSU Ayat | **Unclear — do not bundle** |
| Translations: Pickthall (1930), Yusuf Ali (1934 original) | Public domain outside US (low risk in US) | **Yes** |
| Saheeh International | Publisher statement unverifiable; saheehinternational.com domain is currently hijacked (do not link) | **Unclear** |
| The Clear Quran (Khattab) | Explicit copyright, written consent required | **No** |
| Hilali & Khan (KFGQPC) | Free distribution ≠ open license; terms not fetched | **Unclear** |

## D. Hadith

| Dataset | License | Verdict |
|---|---|---|
| sunnah.com API | API key by GitHub issue; no license; About: "We do not permit the scraping of our data, nor mass reproduction of entire books"; individual hadith for teaching permitted | **API use only; do not bundle** |
| fawazahmed0/hadith-api (10 collections, 9 languages) | The Unlicense (public domain dedication by maintainer) but sources include sunnah.com and copyrighted translations | **Arabic matn usable with attribution; audit English editions individually** |
| AhmedBaset/hadith-json | No license; scraped from sunnah.com | **No** |
| mhashim6/Open-Hadith-Data (9 Arabic books, CSV) | **ODbL 1.0 + DbCL** | **Attribution-only (share-alike on derived databases)** — best Arabic bulk source |
| ceefour/hadith-islamware (upstream) | Unlicense with Islam Ware copyright caveat | **Attribution-only with caveat** |
| HadeethEnc.com API (authentic hadiths + simplified explanations, many languages) | "No modification, addition, or deletion… clearly referring to the publisher and source (HadeethEnc.com)" | **No-derivatives (verbatim + attribution)** — cleanest multilingual source |
| dorar.net API | Intended for displaying search results; no terms found | **Unclear — do not bundle** |
| IslamQA.info | Personal, non-commercial only; no redistribution | **No** |
| Grading data (Albani, Darussalam/Zubair Ali Zai) | No rights-cleared dataset found; Darussalam grades are commercial editorial content | **Unclear — display only with source attribution via API** |

## E. Implications for the Content Library

1. Ship the **provenance model** and importers, not the datasets, for anything marked Unclear/No.
2. Bundle only: Pickthall/Yusuf Ali translations, Open-Hadith-Data (Arabic, ODbL), HadeethEnc (verbatim, attribution), Quranic Arabic Corpus morphology (unmodified, attribution), Lane's Lexicon, cpfair timing data.
3. Provide **live-API adapters** (Quran Foundation, sunnah.com, HadeethEnc, dorar search) that respect cache limits and attribution strings.
4. Classical Arabic tafsir via QUL: ship an importer; recommend operators confirm with Tarteel; mark `license_status: attribution_presumed`.
5. Every imported item stores license, source URL, retrieval date, and checksum; the UI shows attribution text from the record.

## Sources (accessed 2026-09-08)

everyayah.com (+ /data/, recitations.js, timings_files/000_disclaimer.txt); quranicaudio.com/about; quranicaudio.com/api/qaris; mp3quran.net/api/v3/riwayat; api-docs.quran.foundation/legal/developer-terms/; qul.tarteel.ai/{resources/recitation,resources/tafsir,faq,credits,docs}; github.com/cpfair/quran-align; huggingface.co/datasets/tarteel-ai/everyayah; alquran.cloud/terms-and-conditions; alafasy.co/terms-of-use; britishfatwacouncil.org; islamweb.net/en/fatwa/87644; tanzil.net/trans/; corpus.quran.com/{download/,license.jsp}; lanelexicon.com/updates/; github.com/laneslexicon/LexiconDatabase; api.quran.com/api/v4/resources/tafsirs; altafsir.com; theclearquran.org/copyright/; sacred-texts.com; github.com/spa5k/tafsir_api; github.com/Quran-Tafseer/tafseer_api; sunnah.com/{developers,about}; github.com/sunnah-com/api; github.com/fawazahmed0/hadith-api; github.com/AhmedBaset/hadith-json; github.com/mhashim6/Open-Hadith-Data; github.com/ceefour/hadith-islamware; hadeethenc.com (Postman doc); dorar.net/article/389; islamqa.info/en/terms; github.com/marwan/quranwbw. Unreachable today: qurancomplex.gov.sa, islamhouse.com terms, dorar.net terms, tarteel.ai/terms (empty render), web.archive.org.
