"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { Avatar, ErrorBox, JuzStrip, Loading, Num, PageHead, RetentionBar } from "@/components/ui";
import { StudentForm } from "@/components/StudentForm";
import { useCapabilities } from "@/components/Shell";
import { EmptyState } from "@/components/Empty";

type Student = { id: string; person: { display_name_ar: string; display_name_en: string }; student_code: string; branch_name: string; status: string; level: string;
  halaqah: { id: string; name: string } | null; journey_summary: { id: string; memorized_ayat: number; avg_retention: number; weak_ayat: number; critical_ayat: number; memorized_pages: number; juz_map: [number, number | null, string][] } | null };

export default function StudentsPage() {
  const { t, locale } = useI18n();
  const tr = useT2();
  const caps = useCapabilities();
  const [search, setSearch] = useState("");
  const [adding, setAdding] = useState(false);
  const q = useQuery({ queryKey: ["students", search], queryFn: () => api<{ count: number; results: Student[] }>(`/students?search=${encodeURIComponent(search)}&page_size=100`) });
  return (
    <>
      <PageHead eyebrow={t("nav_students")} title={<>{t("students_title")} {q.data && <span className="num muted" style={{ fontSize: 18, fontWeight: 500 }}>· <Num v={q.data.count} /></span>}</>}
        actions={<>
          <input className="input" style={{ width: 300 }} placeholder={t("search")} value={search} onChange={(e) => setSearch(e.target.value)} />
          {caps.data?.permissions.includes("people.students.write") && <button className="btn primary" onClick={() => setAdding(true)}>+ {tr("طالب جديد", "New student")}</button>}
        </>} />
      {adding && <StudentForm onClose={() => setAdding(false)} onSaved={(s) => { setAdding(false); window.location.href = `/students/${s.id}`; }} />}
      {q.isLoading ? <Loading /> : q.error ? <ErrorBox e={q.error} /> : q.data!.results.length === 0 ? (
        <EmptyState title={search ? tr("لا نتائج", "No results") : tr("لا طلاب بعد", "No students yet")} body={search ? undefined : tr("أضف الطالب، اختر حلقته وولي أمره، وتُنشأ رحلته مع القرآن تلقائيًا.", "Add a student, choose their Halaqah and guardian, and their Quran journey is created automatically.")} action={!search && caps.data?.permissions.includes("people.students.write") ? tr("أضف أول طالب", "Add the first student") : undefined} onAction={() => setAdding(true)} />
      ) : (
        <div className="list stagger">
          {q.data!.results.map((s) => {
            const j = s.journey_summary;
            const name = locale === "en" && s.person.display_name_en ? s.person.display_name_en : s.person.display_name_ar;
            return (
              <Link key={s.id} href={`/students/${s.id}`} className="person-row">
                <Avatar name={name} />
                <div><div className="name">{name}</div><div className="meta"><span className="num" dir="ltr">{s.student_code}</span> · {s.halaqah?.name ?? "—"} · {s.branch_name}</div></div>
                <div><JuzStrip map={j?.juz_map} /><div className="meta" style={{ marginTop: 4 }}><Num v={j?.memorized_pages} /> {t("page")} · <Num v={j?.memorized_ayat} /> {t("ayat")}</div></div>
                <RetentionBar v={j?.avg_retention} />
                <div className="tail">{j && j.critical_ayat > 0 ? <span className="chip bad"><i className="dot" style={{ background: "var(--s-critical)" }} /><Num v={j.critical_ayat} /> {t("critical_ayat")}</span> : <span className="chip"><i className="dot" style={{ background: "var(--s-strong)" }} />{t("on_track")}</span>}</div>
              </Link>);
          })}
        </div>
      )}
    </>
  );
}
