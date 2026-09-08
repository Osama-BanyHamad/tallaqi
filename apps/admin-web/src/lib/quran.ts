/** Presentation helpers for Quran text. The text itself is never altered; these only split for display. */

export const BASMALAH = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ";

/** Tanzil prefixes the Basmalah to the first Ayah of each Surah (except 1 and 9). Split it out for layout only. */
export function splitBasmalah(text: string, surah: number, ayah: number): { basmalah: string | null; body: string } {
  if (ayah === 1 && surah !== 1 && surah !== 9 && text.startsWith(BASMALAH + " ")) {
    return { basmalah: BASMALAH, body: text.slice(BASMALAH.length + 1) };
  }
  return { basmalah: null, body: text };
}

export const STATE_ORDER = ["not_memorized", "learning", "recent", "strong", "mastered", "needs_revision", "weak", "critical"] as const;
export type AyahState = (typeof STATE_ORDER)[number];

export const toArabicDigits = (n: number | string) => String(n).replace(/\d/g, (d) => "٠١٢٣٤٥٦٧٨٩"[+d]);

export function fmtPct(x: number | null | undefined, locale: "ar" | "en") {
  if (x == null) return "—";
  const s = `${Math.round(x * 100)}%`;
  return locale === "ar" ? toArabicDigits(s).replace("%", "٪") : s;
}
export function fmtNum(n: number | null | undefined, locale: "ar" | "en") {
  if (n == null) return "—";
  return locale === "ar" ? toArabicDigits(n) : String(n);
}
