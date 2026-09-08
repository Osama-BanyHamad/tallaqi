"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Avatar, ErrorBox, Loading, PageHead } from "@/components/ui";

type S = { id: string; person: { display_name_ar: string; display_name_en: string; phone: string }; staff_type: string; riwayat: string[]; halaqat: { id: string; name: string; role: string }[]; is_active: boolean };
const TYPE: Record<string, string> = { teacher: "معلم", assistant: "معلم مساعد", supervisor: "مشرف", admin: "إداري", finance: "مالية", hr: "موارد بشرية", instructor: "مدرب", support: "دعم" };

export default function StaffPage() {
  const { t, locale } = useI18n();
  const q = useQuery({ queryKey: ["staff"], queryFn: () => api<{ results: S[] }>("/staff?page_size=100") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={t("nav_staff")} title={t("nav_staff")} />
      <div className="list stagger">
        {q.data!.results.map((s) => {
          const name = locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar;
          return (
            <div key={s.id} className="person-row" style={{ gridTemplateColumns: "44px 1.2fr 1fr auto" }}>
              <Avatar name={name} />
              <div><div className="name">{name}</div><div className="meta">{s.halaqat.map((h) => h.name).join("، ") || "—"}</div></div>
              <div className="muted" style={{ fontSize: 13 }}>{s.riwayat.length ? "حفص عن عاصم" : "—"}</div>
              <span className="chip">{locale === "ar" ? TYPE[s.staff_type] ?? s.staff_type : s.staff_type}</span>
            </div>);
        })}
      </div>
    </>
  );
}
