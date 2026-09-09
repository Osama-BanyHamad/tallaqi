"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, getSession, setSession } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { IconBook, IconCircle, IconCompass, IconGlobe, IconLogout, IconModules, IconStudents, IconTeacher } from "@/components/icons";

export type Capabilities = {
  tenant: { slug: string; name: string; name_en: string; locale: string; riwayah: string; branding: { app_name?: string; accent?: string } };
  person_id: string | null;
  modules: Record<string, { enabled: boolean; safety: string; core: boolean }>;
  permissions: string[];
  roles: string[];
  scopes: { type: string; refs: string[] }[];
};

export function useCapabilities() {
  return useQuery({ queryKey: ["capabilities"], queryFn: () => api<Capabilities>("/me/capabilities"), staleTime: 60_000 });
}

/** Where a role lands after sign-in: students → today, parents → children, staff → dashboard or Halaqat, finance → finance. */
export function homeFor(c: Capabilities): string {
  const can = (p: string) => c.permissions.includes(p);
  const mod = (m: string) => c.modules[m]?.enabled;
  if (c.roles.includes("student") || c.roles.includes("solo_learner")) return "/me";
  if (c.roles.includes("listener")) return "/students";
  if (c.roles.includes("guardian")) return "/parent";
  if (can("intel.supervisor.read") && mod("intel.supervisor")) return "/dashboard";
  if (can("ops.halaqat.read")) return "/halaqat";
  if (can("finance.invoicing.read") && mod("finance.fees")) return "/finance";
  if (can("people.students.read")) return "/students";
  return "/settings";
}

/** Permission each app route needs; a role without it is sent to its own home instead of a bare 403. */
const ROUTE_PERM: [string, string][] = [
  ["/dashboard", "intel.supervisor.read"], ["/students", "people.students.read"], ["/staff", "people.staff.read"], ["/halaqat", "ops.halaqat.read"],
  ["/finance", "finance.invoicing.read"], ["/reports", "intel.reports.read"], ["/settings", "platform.tenancy.read"], ["/parent", "parent.portal.use"],
];

const IconCoins = () => (<svg viewBox="0 0 24 24" fill="none" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="6.5" rx="7" ry="3" /><path d="M5 6.5v5c0 1.7 3.1 3 7 3s7-1.3 7-3v-5M5 11.5v5c0 1.7 3.1 3 7 3s7-1.3 7-3v-5" /></svg>);
const IconReport = () => (<svg viewBox="0 0 24 24" fill="none" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round"><path d="M5 20V9M12 20V4M19 20v-7" /><path d="M3 20h18" /></svg>);
const IconFamily = () => (<svg viewBox="0 0 24 24" fill="none" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round"><circle cx="8" cy="7" r="2.6" /><circle cx="16.5" cy="8.5" r="2" /><path d="M3 19c.5-3.2 2.5-5 5-5s4.5 1.8 5 5M13 19c.3-2.3 1.7-3.7 3.5-3.7S19.7 16.7 20 19" /></svg>);
const IconSettings = () => (<svg viewBox="0 0 24 24" fill="none" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg>);

export function Shell({ children }: { children: React.ReactNode }) {
  const { t, locale, setLocale } = useI18n();
  const path = usePathname();
  const router = useRouter();
  const [session, setSessionState] = useState<ReturnType<typeof getSession>>(null);
  useEffect(() => { const s = getSession(); setSessionState(s); if (!s) router.replace("/login"); }, [router]);
  const caps = useCapabilities();
  const can = (p: string) => caps.data?.permissions.includes(p);
  const mod = (m: string) => caps.data?.modules[m]?.enabled;
  const roles = caps.data?.roles ?? [];
  const tr = (ar: string, en: string) => (locale === "en" ? en : ar);

  const items = [
    { href: "/me", label: tr("اليوم", "Today"), Icon: IconBook, show: roles.includes("student") || roles.includes("solo_learner") },
    { href: "/parent", label: tr("أبنائي", "My children"), Icon: IconFamily, show: roles.includes("guardian") && mod("parent.portal") },
    { href: "/dashboard", label: t("nav_dashboard"), Icon: IconCompass, show: can("intel.supervisor.read") && mod("intel.supervisor") },
    { href: "/halaqat", label: t("nav_halaqat"), Icon: IconCircle, show: can("ops.halaqat.read") && mod("ops.halaqat") && !roles.includes("guardian") },
    { href: "/students", label: roles.includes("listener") ? tr("من أسمّع له", "Who I listen to") : t("nav_students"), Icon: IconStudents, show: can("people.students.read") && !roles.includes("guardian") && !roles.includes("student") && !roles.includes("solo_learner") },
    { href: "/staff", label: t("nav_staff"), Icon: IconTeacher, show: can("people.staff.read") && mod("people.staff") },
    { href: "/finance", label: tr("المالية", "Finance"), Icon: IconCoins, show: (can("finance.invoicing.read") || can("finance.fees.read")) && mod("finance.fees") },
    { href: "/reports", label: tr("التقارير", "Reports"), Icon: IconReport, show: can("intel.reports.read") && mod("intel.reports") },
    { href: "/read", label: tr("الورد", "Reading"), Icon: IconBook, show: can("quran.reading.use") && mod("quran.reading") },
    { href: "/settings", label: tr("الإعدادات", "Settings"), Icon: IconSettings, show: (can("platform.tenancy.read") || can("platform.rbac.read")) && !roles.includes("solo_learner") },
  ].filter((i) => i.show);

  useEffect(() => {
    if (!caps.data) return;
    const rule = ROUTE_PERM.find(([r]) => path === r || path.startsWith(r + "/"));
    if (rule && !caps.data.permissions.includes(rule[1])) router.replace(homeFor(caps.data));
  }, [caps.data, path, router]);

  const roleLabel: Record<string, string> = { owner: "مالك المؤسسة", quran_supervisor: "مشرف القرآن", teacher: "معلم", assistant_teacher: "معلم مساعد", guardian: "ولي أمر", finance: "مالية", center_admin: "مدير المركز", student: "طالب", support: "دعم", branch_manager: "مدير الفرع", solo_learner: "متعلّم مستقل", listener: "مُسمِّع" };
  const accent = caps.data?.tenant.branding?.accent;

  return (
    <div className="shell" style={accent ? ({ ["--lapis" as string]: accent } as React.CSSProperties) : undefined}>
      <aside className="spine">
        <div className="lattice" />
        <Link href="/" className="wordmark"><span className="ar">تَلَقِّي</span><span className="latin">Talaqqi</span></Link>
        <div className="tenant-chip">
          <b>{caps.data ? (locale === "en" && caps.data.tenant.name_en ? caps.data.tenant.name_en : caps.data.tenant.name) : "…"}</b>
          {session?.account.full_name}{roles.length ? ` · ${roles.map((r) => (locale === "ar" ? roleLabel[r] ?? r : r)).join(" · ")}` : ""}
        </div>
        <nav aria-label="main">
          {items.map(({ href, label, Icon }) => (
            <Link key={href} href={href} className="nav-item" aria-current={path === href || (href !== "/settings" && path.startsWith(href + "/")) || (href === "/settings" && path.startsWith("/settings")) ? "page" : undefined}><Icon />{label}</Link>
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
