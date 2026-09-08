"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, getSession, setSession } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export type Capabilities = {
  tenant: { slug: string; name: string; name_en: string; locale: string; riwayah: string; branding: { app_name?: string } };
  person_id: string | null;
  modules: Record<string, { enabled: boolean; safety: string; core: boolean }>;
  permissions: string[];
  roles: string[];
  scopes: { type: string; refs: string[] }[];
};

export function useCapabilities() {
  return useQuery({ queryKey: ["capabilities"], queryFn: () => api<Capabilities>("/me/capabilities"), staleTime: 60_000 });
}

export function Shell({ children }: { children: React.ReactNode }) {
  const { t, locale, setLocale } = useI18n();
  const path = usePathname();
  const router = useRouter();
  const [session, setSessionState] = useState<ReturnType<typeof getSession>>(null);
  useEffect(() => { const s = getSession(); setSessionState(s); if (!s) router.replace("/login"); }, [router]);
  const caps = useCapabilities();
  const can = (p: string) => caps.data?.permissions.includes(p);
  const mod = (m: string) => caps.data?.modules[m]?.enabled;

  const items = [
    { href: "/dashboard", label: t("nav_dashboard"), glyph: "◆", show: can("intel.supervisor.read") && mod("intel.supervisor") },
    { href: "/halaqat", label: t("nav_halaqat"), glyph: "◎", show: can("ops.halaqat.read") && mod("ops.halaqat") },
    { href: "/students", label: t("nav_students"), glyph: "◇", show: can("people.students.read") },
    { href: "/staff", label: t("nav_staff"), glyph: "△", show: can("people.staff.read") && mod("people.staff") },
    { href: "/settings/modules", label: t("nav_modules"), glyph: "▣", show: can("platform.tenancy.read") },
  ].filter((i) => i.show);

  return (
    <div className="shell">
      <aside className="spine">
        <div className="wordmark"><span className="ar">تَلَقِّي</span><span className="latin">Talaqqi</span></div>
        <div className="tenant-chip">
          <b>{caps.data ? (locale === "en" && caps.data.tenant.name_en ? caps.data.tenant.name_en : caps.data.tenant.name) : "…"}</b>
          {session?.account.full_name} · {caps.data?.roles.join(" · ")}
        </div>
        <nav aria-label="main">
          {items.map((i) => (
            <Link key={i.href} href={i.href} aria-current={path.startsWith(i.href) ? "page" : undefined}><span className="glyph">{i.glyph}</span>{i.label}</Link>
          ))}
        </nav>
        <div className="foot">
          <button type="button" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>{t("switch_lang")}</button>
          <button type="button" onClick={() => { setSession(null); router.replace("/login"); }}>{t("signout")}</button>
          <span>{t("quran_attribution")}</span>
        </div>
      </aside>
      <main className="matn">{children}</main>
    </div>
  );
}
