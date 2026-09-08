# 19 — Visual Identity of the Admin Web (as built)

Concept: **المَتْن والحاشية** — the manuscript body and its margin. Every working screen has three zones: the **spine** (dark lapis navigation band with a single gold hairline), the **matn** (the content being read or acted on), and the **hashiya** (a sticky margin column holding annotations: today's plan, explanations, the timeline, teacher notes). Nothing decorative; every device carries information.

## Tokens (`apps/admin-web/src/app/globals.css`)

| Role | Light | Dark | Meaning |
|---|---|---|---|
| Paper | `#F4F2EC` | `#12151D` | Ground |
| Ink | `#171A24` | `#E7E4DA` | Text |
| Lapis | `#22357A` | `#8EA0E6` | The institution's voice: links, primary actions, mastered |
| Gold | `#A9862B` | `#D2B25D` | Only for what is sacred or verified: the spine hairline, the Mushaf frame, Ayah markers, the "due" dot |
| Spine | `#141A33` | `#0C0F18` | Navigation band |
| States | sage `#3F7D5C` strong · teal `#6AA3A8` recent · lapis mastered · ochre `#C98F2A` needs revision · rust `#B5502F` weak · deep red `#7A1F1F` critical · paper-3 not memorized · hatched learning | | An earth scale, never traffic lights |

Type: **Noto Kufi Arabic** for headings (geometric, modern-Islamic without ornament), **IBM Plex Sans Arabic** for body, **Amiri Quran** for Quran text (OFL; DigitalKhatt/KFGQPC packs come with the Mushaf renderer), **IBM Plex Mono** for numerals and codes. Arabic-Indic digits in the Arabic locale.

## Signature element

The **Memory Map folio strip**: thirty Juz rows, each a run of page-tiles colored by retention state, with a gold dot for pages due today. Quran → Juz → Page drill-down, and at page level every Ayah opens to its Arabic explanation of the score. The same motif, hashed deterministically, is the only image on the login screen.

## Rules kept

- Quran text is rendered verbatim from the API; overlays (marks, highlights) never alter it; every Mushaf view shows the Tanzil attribution.
- The Tasmee' screen keeps the teacher's eyes on the Mushaf: tap a word → pick a type → Pass. Mistake types come from the backend catalog.
- Retention is labeled an educational metric in the margin of every journey page.
- RTL is the base direction; English mirrors it with logical CSS properties.
- Dark mode is a full palette, not an inversion.
