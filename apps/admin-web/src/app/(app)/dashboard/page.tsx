"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { ErrorBox, Loading, Num, Pct, RetentionBar } from "@/components/ui";

type Row = { journey_id: string; student_id: string; name: string; branch: string; avg_retention: number; memorized_ayat: number; weak_ayat: number; critical_ayat: number; sessions_7d: number; absences_14d: number; reasons: string[] };
type Dash = { totals: { students: number; on_track: number; behind: number; attention: number; avg_retention: number }; attention: Row[]; behind: Row[]; on_track: Row[];
  halaqat: { id: string; name: string; students: number; teacher: string; avg_retention: number; critical_ayat: number; memorized_pages: number }[] };

export default function Dashboard() {
  const { t } = useI18n();
  const q = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dash>("/dashboard") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const d = q.data!;
  const List = ({ rows, title, tone }: { rows: Row[]; title: string; tone: string }) => (
    <section className="stack" style={{ gap: 10 }}>
      <h2 style={{ color: tone }}>{title} <span className="num muted" style={{ fontSize: 14 }}>· {rows.length}</span></h2>
      {rows.length === 0 ? <p className="muted" style={{ margin: 0 }}>—</p> : (
        <div className="tbl"><table>
          <thead><tr><th>{t("students")}</th><th>{t("retention")}</th><th>{t("memorized")}</th><th>{t("reasons")}</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.journey_id} className="row-link" onClick={() => (window.location.href = `/journeys/${r.journey_id}`)}>
              <td><Link href={`/journeys/${r.journey_id}`}>{r.name}</Link><div className="muted" style={{ fontSize: 12 }}>{r.branch}</div></td>
              <td><RetentionBar v={r.avg_retention} /></td>
              <td><Num v={r.memorized_ayat} /> {t("ayat")}</td>
              <td>{r.reasons.length ? r.reasons.map((x, i) => <span key={i} className="pill" style={{ marginInlineEnd: 6 }}>{x}</span>) : <span className="muted">—</span>}</td>
            </tr>))}</tbody>
        </table></div>
      )}
    </section>
  );
  return (
    <>
      <div className="page-head"><div><span className="eyebrow">{t("nav_dashboard")}</span><h1>{t("dash_title")}</h1><p>{t("dash_sub")}</p></div></div>
      <div className="ledger">
        <div><div className="label">{t("students")}</div><div className="value num"><Num v={d.totals.students} /></div></div>
        <div><div className="label">{t("on_track")}</div><div className="value num" style={{ color: "var(--s-strong)" }}><Num v={d.totals.on_track} /></div></div>
        <div><div className="label">{t("behind")}</div><div className="value num" style={{ color: "var(--s-needs)" }}><Num v={d.totals.behind} /></div></div>
        <div><div className="label">{t("attention")}</div><div className="value num attention"><Num v={d.totals.attention} /></div></div>
        <div><div className="label">{t("avg_retention")}</div><div className="value num"><Pct v={d.totals.avg_retention} /></div></div>
      </div>
      <div className="with-margin">
        <div className="stack" style={{ gap: 30 }}>
          <List rows={d.attention} title={t("attention")} tone="var(--s-weak)" />
          <List rows={d.behind} title={t("behind")} tone="var(--s-needs)" />
        </div>
        <aside className="hashiya">
          <h3>{t("halaqah_perf")}</h3>
          {d.halaqat.map((h) => (
            <div key={h.id} style={{ paddingBottom: 12, borderBottom: "1px dashed var(--rule)" }}>
              <Link href={`/halaqat/${h.id}`} style={{ fontWeight: 600 }}>{h.name}</Link>
              <dl className="kv" style={{ marginTop: 4 }}>
                <dt>{t("teacher")}</dt><dd>{h.teacher || "—"}</dd>
                <dt>{t("students")}</dt><dd><Num v={h.students} /></dd>
                <dt>{t("avg_retention")}</dt><dd><RetentionBar v={h.avg_retention} /></dd>
                <dt>{t("critical_ayat")}</dt><dd><Num v={h.critical_ayat} /></dd>
                <dt>{t("memorized_pages")}</dt><dd><Num v={h.memorized_pages} /></dd>
              </dl>
            </div>
          ))}
        </aside>
      </div>
    </>
  );
}
