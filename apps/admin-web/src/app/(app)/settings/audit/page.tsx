"use client";
import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { ErrorBox, Loading, PageHead } from "@/components/ui";

type Row = { id: string; actor_email: string | null; actor_type: string; action: string; object_type: string; object_id: string; before: unknown; after: unknown; ip: string | null; created_at: string };

export default function AuditPage() {
  const { locale } = useI18n();
  const tr = useT2();
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["audit", search], queryFn: () => api<{ count: number; results: Row[] }>(`/audit?search=${encodeURIComponent(search)}&page_size=100`) });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={tr("الإعدادات", "Settings")} title={tr("سجل التدقيق", "Audit log")} sub={tr("من فعل ماذا ومتى، مع الحالة قبل وبعد. السجل لا يُعدَّل ولا يُحذف.", "Who did what and when, with before/after state. Immutable.")}
        actions={<input className="input" style={{ width: 300 }} placeholder={tr("بحث: الإجراء أو الكائن أو المستخدم", "Search action, object, or user")} value={search} onChange={(e) => setSearch(e.target.value)} />} />
      <div className="tbl"><table>
        <thead><tr><th>{tr("الوقت", "Time")}</th><th>{tr("المستخدم", "User")}</th><th>{tr("الإجراء", "Action")}</th><th>{tr("الكائن", "Object")}</th><th>IP</th><th /></tr></thead>
        <tbody>
          {q.data!.results.map((r) => (
            <Fragment key={r.id}>
              <tr>
                <td className="num" style={{ fontSize: 12.5, whiteSpace: "nowrap" }}>{new Intl.DateTimeFormat(locale === "ar" ? "ar-JO" : "en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(r.created_at))}</td>
                <td dir="ltr" style={{ textAlign: "start" }}>{r.actor_email ?? r.actor_type}</td>
                <td><span className="chip"><i className="dot" style={{ background: r.action.includes("delete") || r.action.includes("revoke") ? "var(--s-weak)" : "var(--lapis)" }} />{r.action}</span></td>
                <td className="num" style={{ fontSize: 12 }}>{r.object_type} <span className="muted">{r.object_id.slice(0, 8)}</span></td>
                <td className="num muted" style={{ fontSize: 12 }}>{r.ip ?? "—"}</td>
                <td><button className="btn sm" onClick={() => setOpen(open === r.id ? null : r.id)}>{open === r.id ? "−" : "+"}</button></td>
              </tr>
              {open === r.id && <tr><td colSpan={6}><pre dir="ltr" style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 12, background: "var(--surface-2)", padding: 12, borderRadius: 6, overflowX: "auto" }}>{JSON.stringify({ before: r.before, after: r.after }, null, 2)}</pre></td></tr>}
            </Fragment>
          ))}
        </tbody>
      </table></div>
    </>
  );
}
