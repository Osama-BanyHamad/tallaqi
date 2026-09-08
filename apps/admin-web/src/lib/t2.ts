"use client";
import { useI18n } from "@/lib/i18n";

/** Inline bilingual helper for screens added after the core dictionary: tr("عربي", "English"). */
export function useT2() {
  const { locale } = useI18n();
  return (ar: string, en: string) => (locale === "en" ? en : ar);
}
