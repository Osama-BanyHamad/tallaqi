"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, getSession, setSession } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { IconCircle, IconCompass, IconGlobe, IconLogout, IconModules, IconStudents, IconTeacher } from "@/components/icons";

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
    { href: "/dashboard", label: t("nav_dashboard"), Icon: IconCompass, show: can("intel.supervisor.read") && mod("intel.supervisor") },
    { href: "/halaqat", label: t("nav_halaqat"), Icon: IconCircle, show: can("ops.halaqat.read") && mod("ops.halaqat") },
    { href: "/students", label: t("nav_students"), Icon: IconStudents, show: can("people.students.read") },
    { href: "/staff", label: t("nav_staff"), Icon: IconTeacher, show: can("people.staff.read") && mod("people.staff") },
    { href: "/settings/modules", label: t("nav_modules"), Icon: IconModules, show: can("platform.tenancy.read") },
  ].filter((i) => i.show);

  const roleLabel: Record<string, string> = { owner: "مالك المؤسسة", quran_supervisor: "مشرف القرآن", teacher: "معلم", guardian: "ولي أمر", finance: "مالية", center_admin: "مدير المركز" };

  return (
    <div className="shell">
      <aside className="spine">
        <div className="lattice" />
        <Link href="/" className="wordmark"><span className="ar">تَلَقِّي</span><span className="latin">Talaqqi</span></Link>
        <div className="tenant-chip">
          <b>{caps.data ? (locale === "en" && caps.data.tenant.name_en ? caps.data.tenant.name_en : caps.data.tenant.name) : "…"}</b>
          {session?.account.full_name}{caps.data?.roles.length ? ` · ${caps.data.roles.map((r) => (locale === "ar" ? roleLabel[r] ?? r : r)).join(" · ")}` : ""}
        </div>
        <nav aria-label="main">
          {items.map(({ href, label, Icon }) => (
            <Link key={href} href={href} className="nav-item" aria-current={path.startsWith(href) ? "page" : undefined}><Icon />{label}</Link>
          ))}
        </nav>
        <div className="foot">
          <div className="row">
            <button type="button" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}><span style={{ display: "inline-flex", verticalAlign: "middle", width: 16, marginInlineEnd: 6 }}><IconGlobe /></span>{t("switch_lang")}</button>
            <button type="button" onClick={() => { setSession(null); router.replace("/login"); }}><span style={{ display: "inline-flex", verticalAlign: "middle", width: 16, marginInlineEnd: 6 }}><IconLogout /></span>{t("signout")}</button>
          </div>
          <span>{t("quran_attribution")}</span>
        </div>
      </aside>
      <main className="matn">{children}</main>
    </div>
  );
}
