"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { fmtNum } from "@/lib/quran";
import { MemoryMap, PageDetail } from "@/components/MemoryMap";
import { ErrorBox, JuzStrip, Kpi, Loading, Num, PageHead, Pct } from "@/components/ui";

type Journey = { id: string; student_name: string; memorized_pages: number; memorized_ayat: number; avg_retention: number; juz_map: [number, number | null, string][]; current_key: { surah_name: string; ayah: number; page: number } | null };
type Plan = { paused_new: boolean; rationale: string[]; segments: { id: string; purpose: string; from_ayah_index: number; to_ayah_index: number; from_key: { surah_name: string; ayah: number }; to_key: { surah_name: string; ayah: number }; reason: string; completion: string }[] };

/** Student home on the web: today's plan and the journey. Calm, no streaks. */
export default function MePage() {
  const { t, locale } = useI18n();
  const tr = useT2();
  const [page, setPage] = useState<number | null>(null);
  const me = useQuery({ queryKey: ["me-journey"], queryFn: () => api<{ results: { id: string }[] }>("/journeys?page_size=1") });
  const jid = me.data?.results[0]?.id ?? null;
  const j = useQuery({ queryKey: ["journey", jid], queryFn: () => api<Journey>(`/journeys/${jid}`), enabled: !!jid });
  const plan = useQuery({ queryKey: ["plan", jid], queryFn: () => api<Plan>(`/journeys/${jid}/plan`), enabled: !!jid });
  if (me.isLoading) return <Loading />;
  if (me.error) return <ErrorBox e={me.error} />;
  if (!jid) return <p className="muted">{tr("لا يوجد ملف طالب مرتبط بهذا الحساب.", "No student profile is linked to this account.")}</p>;
  if (!j.data) return <Loading />;
  const d = j.data;
  return (
    <>
      <PageHead eyebrow={tr("اليوم", "Today")} title={d.student_name} sub={d.current_key ? `${t("position")}: ${d.current_key.surah_name} ${fmtNum(d.current_key.ayah, locale)} · ${t("page")} ${fmtNum(d.current_key.page, locale)}` : tr("في المراجعة الطويلة", "Long-term revision")} />
      <div className="kpis stagger">
        <Kpi accent label={t("memorized_pages")} value={<Num v={d.memorized_pages} />} />
        <Kpi label={t("memorized")} value={<Num v={d.memorized_ayat} />} unit={t("ayat")} />
        <Kpi label={t("avg_retention")} value={<Pct v={d.avg_retention} />} />
      </div>
      <div className="with-margin">
        <div className="stack" style={{ gap: 26 }}>
          <div className="surface pad"><JuzStrip map={d.juz_map} large /></div>
          <div className="surface pad"><MemoryMap journeyId={jid} onSelectPage={setPage} /></div>
          {page != null && <PageDetail journeyId={jid} page={page} />}
        </div>
        <aside className="hashiya">
          <div><h3>{t("todays_plan")}</h3>
            <div className="stack" style={{ gap: 8 }}>
              {(plan.data?.segments ?? []).map((s) => (
                <Link key={s.id} href={`/practice/${jid}?from=${s.from_ayah_index}&to=${s.to_ayah_index}&purpose=${s.purpose}`} className="seg" style={{ gridTemplateColumns: "auto 1fr auto" }}>
                  <span className={`purpose ${s.purpose}`}>{t(`purpose_${s.purpose}` as Key)}</span>
                  <span style={{ fontSize: 13 }}>{s.from_key.surah_name} {fmtNum(s.from_key.ayah, locale)} → {s.to_key.surah_name} {fmtNum(s.to_key.ayah, locale)}</span>
                  <span className="num" style={{ color: s.completion === "verified" ? "var(--s-strong)" : "var(--gold)" }}>{s.completion === "verified" ? "✓" : tr("تدرّب", "Practice")}</span>
                </Link>))}
              {plan.data?.paused_new && <p style={{ fontSize: 12.5 }}>{tr("إيقاف مؤقت للحفظ الجديد — ركّز على المراجعة.", "New memorization paused; focus on revision.")}</p>}
              {(plan.data?.rationale ?? []).map((r, i) => <p key={i} style={{ fontSize: 12.5 }}>{r}</p>)}
            </div>
          </div>
          <div><h3>{t("explanation")}</h3><p>{tr("الثبات مقياس تعليمي يُحسب من تسميعات معلمك. ليس حكمًا شرعيًا على تلاوتك.", "Retention is an educational metric computed from your teacher's recitations, not a religious judgment.")}</p></div>
        </aside>
      </div>
    </>
  );
}
