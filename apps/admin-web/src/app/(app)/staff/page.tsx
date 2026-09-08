"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { ErrorBox, Loading } from "@/components/ui";

type S = { id: string; person: { display_name_ar: string; display_name_en: string; phone: string }; staff_type: string; riwayat: string[]; halaqat: { id: string; name: string; role: string }[]; is_active: boolean };

export default function StaffPage() {
  const { t, locale } = useI18n();
  const q = useQuery({ queryKey: ["staff"], queryFn: () => api<{ results: S[] }>("/staff?page_size=100") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <div className="page-head"><div><span className="eyebrow">{t("nav_staff")}</span><h1>{t("nav_staff")}</h1></div></div>
      <div className="tbl"><table>
        <thead><tr><th>{t("teacher")}</th><th>{t("status")}</th><th>{t("halaqah")}</th><th>الرواية</th></tr></thead>
        <tbody>{q.data!.results.map((s) => (
          <tr key={s.id}><td>{locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar}</td><td><span className="pill">{s.staff_type}</span></td>
            <td>{s.halaqat.map((h) => h.name).join("، ") || "—"}</td><td className="muted">{s.riwayat.join(", ") || "—"}</td></tr>))}</tbody>
      </table></div>
    </>
  );
}
