# Quran Core data licenses and provenance

This directory ships **verified structured data only**. No audio is bundled.

## Quran text (Hafs ʿan ʿĀṣim, Uthmani script)

Source: **Tanzil Project**, Quran text, Uthmani edition — https://tanzil.net/download/

Tanzil terms of use (reproduced as required):

- Permission is granted to copy and distribute verbatim copies of this text, but **CHANGING IT IS NOT ALLOWED**.
- This Quran text can be used in any website or application, provided that its source (Tanzil Project) is clearly indicated, and a link is made to https://tanzil.net to enable users to keep track of changes.
- This copyright notice shall be included in all verbatim copies of the text, and shall be reproduced appropriately in all files derived from or containing substantial portion of this text.

Talaqqi complies by: never modifying the text (the build copies it verbatim and the CI snapshot test proves it), displaying "Quran text: Tanzil Project — tanzil.net" in every Mushaf view, and keeping this notice.

## Structure metadata (surahs, juz, hizb quarters, Madani pages, sajdas)

Source: Tanzil metadata `quran-data.xml`, © 2008–2009 Tanzil.info, licensed **CC-BY** — https://tanzil.net/res/text/metadata/quran-data.xml

## Integrity

`data/manifest.json` lists SHA-256 checksums for every file and a text-root checksum; `data/snapshots/hafs_asim_ayah_sha256.txt` is the per-Ayah golden snapshot. `packages/quran_core/tests/test_integrity.py` fails CI if any Ayah changes. Releases require updating the manifest and snapshot together and two reviewer approvals (CODEOWNERS).
