"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useState } from "react";
import { ErrorBox, Loading, Num, PageHead } from "@/components/ui";
import { HalaqahForm } from "@/components/HalaqahManage";
import { useCapabilities } from "@/components/Shell";

type H = { id: string; name: string; branch_name: string; kind: string; policy_key: string; schedule_summary: string; capacity: number; student_count: number; teachers: { name: string; role: string }[] };
const KIND: Record<string, string> = { in_person: "حضوري", online: "عن بُعد", hybrid: "مدمج" };

export default function HalaqatPage() {
  const { t, locale } = useI18n();
  const [creating, setCreating] = useState(false);
  const caps = useCapabilities();
  const q = useQuery({ queryKey: ["halaqat"], queryFn: () => api<{ results: H[] }>("/halaqat?page_size=100") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={t("nav_halaqat")} title={t("nav_halaqat")} sub={locale === "ar" ? "افتح الحلقة لتسجيل الحضور والتسميع من خطة اليوم." : "Open a Halaqah to mark attendance and run Tasmee' from today's plan."}
        actions={caps.data?.permissions.includes("ops.halaqat.write") && <button className="btn primary" onClick={() => setCreating(true)}>+ {locale === "ar" ? "حلقة جديدة" : "New Halaqah"}</button>} />
      {creating && <HalaqahForm initial={{ name: "", branch: "", kind: "in_person", gender_policy: "male", capacity: 12, policy_key: "sabaq_sabqi_manzil", schedule_summary: "" }} onClose={() => setCreating(false)} onSaved={(h) => { window.location.href = `/halaqat/${h.id}`; }} />}
      <div className="stagger" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {q.data!.results.map((h) => (
          <Link key={h.id} href={`/halaqat/${h.id}`} className="surface pad stack" style={{ gap: 10, color: "inherit" }}>
            <div className="row" style={{ justifyContent: "space-between" }}><h2 style={{ fontSize: 18 }}>{h.name}</h2><span className="chip">{locale === "ar" ? KIND[h.kind] ?? h.kind : h.kind}</span></div>
            <p className="muted" style={{ margin: 0, fontSize: 13.5 }}>{h.branch_name}<br />{h.schedule_summary}</p>
            <p style={{ margin: 0, fontSize: 14 }}>{t("teacher")}: <b>{h.teachers.map((x) => x.name).join("، ") || "—"}</b></p>
            <div className="row" style={{ justifyContent: "space-between", marginTop: 4 }}>
              <span className="num" style={{ fontSize: 22, fontFamily: "var(--font-display)", fontWeight: 700 }}><Num v={h.student_count} /><span className="muted" style={{ fontSize: 13, fontWeight: 500 }}> / <Num v={h.capacity} /> {t("students")}</span></span>
              <span className="chip">{h.policy_key.replaceAll("_", " ")}</span>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
