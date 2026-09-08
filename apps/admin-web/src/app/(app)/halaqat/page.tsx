"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { ErrorBox, Loading, Num } from "@/components/ui";

type H = { id: string; name: string; branch_name: string; kind: string; policy_key: string; schedule_summary: string; capacity: number; student_count: number; teachers: { name: string; role: string }[] };

export default function HalaqatPage() {
  const { t } = useI18n();
  const q = useQuery({ queryKey: ["halaqat"], queryFn: () => api<{ results: H[] }>("/halaqat?page_size=100") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <div className="page-head"><div><span className="eyebrow">{t("nav_halaqat")}</span><h1>{t("nav_halaqat")}</h1></div></div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
        {q.data!.results.map((h) => (
          <Link key={h.id} href={`/halaqat/${h.id}`} className="card stack" style={{ gap: 8, textDecoration: "none", color: "inherit" }}>
            <div className="row" style={{ justifyContent: "space-between" }}><h2 style={{ fontSize: 16 }}>{h.name}</h2><span className="pill">{h.kind}</span></div>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>{h.branch_name} · {h.schedule_summary}</p>
            <p style={{ margin: 0, fontSize: 13 }}>{t("teacher")}: {h.teachers.map((x) => x.name).join("، ") || "—"}</p>
            <p style={{ margin: 0, fontSize: 13 }}><Num v={h.student_count} /> / <Num v={h.capacity} /> {t("students")} · {h.policy_key}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
