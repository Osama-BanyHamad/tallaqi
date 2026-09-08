"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Avatar, ErrorBox, JuzStrip, Kpi, Loading, Num, PageHead, Pct, RetentionBar } from "@/components/ui";

type Row = { journey_id: string; student_id: string; name: string; branch: string; avg_retention: number; memorized_ayat: number; weak_ayat: number; critical_ayat: number; sessions_7d: number; absences_14d: number; reasons: string[]; juz_map: [number, number | null, string][]; memorized_pages: number };
type Dash = { totals: { students: number; on_track: number; behind: number; attention: number; avg_retention: number }; attention: Row[]; behind: Row[]; on_track: Row[];
  halaqat: { id: string; name: string; students: number; teacher: string; avg_retention: number; critical_ayat: number; memorized_pages: number }[] };

export default function Dashboard() {
  const { t } = useI18n();
  const q = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dash>("/dashboard") });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const d = q.data!;
  const List = ({ rows, title, tone }: { rows: Row[]; title: string; tone: string }) => (
    <section>
      <div className="section-title"><h2 style={{ color: tone }}>{title}</h2><small><Num v={rows.length} /> {t("students")}</small></div>
      {rows.length === 0 ? <p className="muted" style={{ margin: 0 }}>—</p> : (
        <div className="list stagger">
          {rows.map((r) => (
            <Link key={r.journey_id} href={`/journeys/${r.journey_id}`} className="person-row">
              <Avatar name={r.name} />
              <div><div className="name">{r.name}</div><div className="meta">{r.branch} · <Num v={r.memorized_pages} /> {t("page")}</div></div>
              <JuzStrip map={r.juz_map} />
              <RetentionBar v={r.avg_retention} />
              <div className="tail"><span className="chip"><i className="dot" style={{ background: r.sessions_7d ? "var(--s-strong)" : "var(--s-weak)" }} />{r.sessions_7d} {t("sessions")}</span></div>
              <div className="reasons">{r.reasons.map((x, i) => <span key={i} className={`chip ${tone === "var(--s-weak)" ? "bad" : "warn"}`}>{x}</span>)}</div>
            </Link>))}
        </div>
      )}
    </section>
  );
  return (
    <>
      <PageHead eyebrow={t("nav_dashboard")} title={t("dash_title")} sub={t("dash_sub")} />
      <div className="kpis stagger">
        <Kpi accent label={t("students")} value={<Num v={d.totals.students} />} sub={`${t("avg_retention")} ${Math.round(d.totals.avg_retention * 100)}%`} />
        <Kpi tone="ok" label={t("on_track")} value={<Num v={d.totals.on_track} />} />
        <Kpi tone="behind" label={t("behind")} value={<Num v={d.totals.behind} />} />
        <Kpi tone="attention" label={t("attention")} value={<Num v={d.totals.attention} />} />
        <Kpi label={t("avg_retention")} value={<Pct v={d.totals.avg_retention} />} sub={t("explanation")} />
      </div>
      <div className="with-margin">
        <div className="stack" style={{ gap: 34 }}>
          <List rows={d.attention} title={t("attention")} tone="var(--s-weak)" />
          <List rows={d.behind} title={t("behind")} tone="var(--s-needs)" />
        </div>
        <aside className="hashiya">
          <div>
            <h3>{t("halaqah_perf")}</h3>
            <div className="stack" style={{ gap: 12 }}>
              {d.halaqat.map((h) => (
                <Link key={h.id} href={`/halaqat/${h.id}`} className="surface pad" style={{ padding: "14px 16px", color: "inherit", display: "block" }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{h.name}</div>
                  <div className="muted" style={{ fontSize: 12.5, marginBottom: 8 }}>{h.teacher || "—"} · <Num v={h.students} /> {t("students")}</div>
                  <RetentionBar v={h.avg_retention} width={120} />
                  <div className="muted" style={{ fontSize: 12.5, marginTop: 6 }}><Num v={h.memorized_pages} /> {t("memorized_pages")} · <Num v={h.critical_ayat} /> {t("critical_ayat")}</div>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}
