"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { ErrorBox, Loading, Num, RetentionBar } from "@/components/ui";

type Student = { id: string; person: { display_name_ar: string; display_name_en: string }; student_code: string; branch_name: string; status: string; level: string;
  halaqah: { id: string; name: string } | null; journey_summary: { id: string; memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; memorized_pages: number } | null };

export default function StudentsPage() {
  const { t, locale } = useI18n();
  const [search, setSearch] = useState("");
  const q = useQuery({ queryKey: ["students", search], queryFn: () => api<{ count: number; results: Student[] }>(`/students?search=${encodeURIComponent(search)}&page_size=100`) });
  return (
    <>
      <div className="page-head">
        <div><span className="eyebrow">{t("nav_students")}</span><h1>{t("students_title")} {q.data && <span className="num muted" style={{ fontSize: 16 }}>· <Num v={q.data.count} /></span>}</h1></div>
        <input className="input" style={{ maxWidth: 320 }} placeholder={t("search")} value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      {q.isLoading ? <Loading /> : q.error ? <ErrorBox e={q.error} /> : (
        <div className="tbl"><table>
          <thead><tr><th>{t("students")}</th><th>{t("code")}</th><th>{t("halaqah")}</th><th>{t("memorized_pages")}</th><th>{t("memorized")}</th><th>{t("retention")}</th><th>{t("critical_ayat")}</th></tr></thead>
          <tbody>{q.data!.results.map((s) => {
            const j = s.journey_summary;
            const href = j ? `/journeys/${j.id}` : "#";
            return (
              <tr key={s.id} className="row-link" onClick={() => j && (window.location.href = href)}>
                <td><Link href={href}>{locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar}</Link><div className="muted" style={{ fontSize: 12 }}>{s.branch_name}{s.level ? ` · ${s.level}` : ""}</div></td>
                <td className="num" dir="ltr">{s.student_code}</td>
                <td>{s.halaqah?.name ?? "—"}</td>
                <td><Num v={j?.memorized_pages} /></td>
                <td><Num v={j?.memorized_ayat} /> {t("ayat")}</td>
                <td><RetentionBar v={j?.avg_retention} /></td>
                <td>{j && j.critical_ayat > 0 ? <span className="pill state-critical"><i className="dot" /><Num v={j.critical_ayat} /></span> : <span className="muted">—</span>}</td>
              </tr>);
          })}</tbody>
        </table></div>
      )}
    </>
  );
}
