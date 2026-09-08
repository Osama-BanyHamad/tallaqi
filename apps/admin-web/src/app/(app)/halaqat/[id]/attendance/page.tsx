"use client";
import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { ErrorBox, Loading, PageHead } from "@/components/ui";

type M = { since: string; dates: string[]; students: { id: string; name: string; days: Record<string, string> }[] };
const C: Record<string, string> = { present: "var(--s-strong)", late: "var(--s-needs)", absent: "var(--s-weak)", excused: "var(--gold)", left_early: "var(--s-recent)" };

export default function AttendanceMatrix({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t } = useI18n();
  const tr = useT2();
  const h = useQuery({ queryKey: ["halaqah", id], queryFn: () => api<{ name: string }>(`/halaqat/${id}`) });
  const q = useQuery({ queryKey: ["att-matrix", id], queryFn: () => api<M>(`/halaqat/${id}/attendance-history?days=30`) });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const d = q.data!;
  return (
    <>
      <PageHead eyebrow={`${t("attendance")} · ${tr("آخر ٣٠ يومًا", "last 30 days")}`} title={h.data?.name ?? "…"} />
      <div className="tbl">
        <table>
          <thead><tr><th>{t("students")}</th>{d.dates.map((dt) => <th key={dt} className="num" style={{ fontSize: 10.5, padding: "8px 4px", writingMode: "vertical-rl", transform: "rotate(180deg)" }}>{dt.slice(5)}</th>)}<th>{tr("نسبة الحضور", "Rate")}</th></tr></thead>
          <tbody>
            {d.students.map((s) => {
              const vals = Object.values(s.days);
              const rate = vals.length ? Math.round(vals.filter((v) => v === "present" || v === "late").length / vals.length * 100) : null;
              return (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600, whiteSpace: "nowrap" }}>{s.name}</td>
                  {d.dates.map((dt) => <td key={dt} style={{ padding: 4, textAlign: "center" }}><span title={s.days[dt] ? t(s.days[dt] as "present") : ""} style={{ display: "inline-block", width: 16, height: 16, borderRadius: 3, background: C[s.days[dt]] ?? "var(--s-none)" }} /></td>)}
                  <td className="num">{rate == null ? "—" : `${rate}%`}</td>
                </tr>);
            })}
          </tbody>
        </table>
      </div>
      <div className="legend">{Object.entries(C).map(([k, v]) => <span key={k}><i style={{ background: v }} />{t(k as "present")}</span>)}</div>
    </>
  );
}
