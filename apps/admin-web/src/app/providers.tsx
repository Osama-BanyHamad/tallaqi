"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { I18nContext, translate, type Locale } from "@/lib/i18n";
import { getLocale, setLocale as persistLocale } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 15_000, retry: 1, refetchOnWindowFocus: false } } }));
  const [locale, setLocaleState] = useState<Locale>("ar");
  useEffect(() => { setLocaleState(getLocale()); }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
  }, [locale]);
  const value = useMemo(() => ({ locale, t: (k: Parameters<typeof translate>[1]) => translate(locale, k), setLocale: (l: Locale) => { persistLocale(l); setLocaleState(l); } }), [locale]);
  return (
    <QueryClientProvider client={qc}>
      <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
    </QueryClientProvider>
  );
}
