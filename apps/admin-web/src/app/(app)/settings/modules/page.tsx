"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { ErrorBox, Loading } from "@/components/ui";

type Mod = { key: string; name_ar: string; name_en: string; safety: "GREEN" | "YELLOW" | "RED"; core: boolean; requires: string[]; enabled: boolean };

export default function ModulesPage() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [err, setErr] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["modules"], queryFn: () => api<Mod[]>("/tenant/modules") });
  const toggle = useMutation({
    mutationFn: (m: Mod) => api("/tenant/modules", { method: "PUT", json: { key: m.key, enabled: !m.enabled } }),
    onSuccess: () => { setErr(null); qc.invalidateQueries({ queryKey: ["modules"] }); qc.invalidateQueries({ queryKey: ["capabilities"] }); },
    onError: (e) => setErr((e as Error).message),
  });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const groups = new Map<string, Mod[]>();
  q.data!.forEach((m) => { const g = m.key.split(".")[0]; groups.set(g, [...(groups.get(g) ?? []), m]); });
  const tone = { GREEN: "var(--s-strong)", YELLOW: "var(--s-needs)", RED: "var(--s-critical)" };
  return (
    <>
      <div className="page-head"><div><span className="eyebrow">{t("nav_modules")}</span><h1>{t("modules_title")}</h1><p>{t("modules_sub")}</p></div></div>
      {err && <p role="alert" style={{ color: "var(--s-weak)" }}>{err}</p>}
      <div className="stack" style={{ gap: 26 }}>
        {[...groups.entries()].map(([g, mods]) => (
          <section key={g}>
            <h2 style={{ marginBottom: 10, fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-3)", textTransform: "uppercase" }}>{g}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 10 }}>
              {mods.map((m) => (
                <div key={m.key} className="card" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, alignItems: "center", opacity: m.enabled ? 1 : .7 }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{locale === "en" ? m.name_en : m.name_ar}</div>
                    <div className="muted num" style={{ fontSize: 11.5 }} dir="ltr">{m.key}</div>
                    <div className="row" style={{ gap: 6, marginTop: 6 }}>
                      <span className="pill" style={{ ["--dot" as string]: tone[m.safety] }}><i className="dot" />{t(`safety_${m.safety}` as Key)}</span>
                      {m.core && <span className="pill">{t("core")}</span>}
                      {m.requires.length > 0 && <span className="muted" style={{ fontSize: 11.5 }}>← {m.requires.join(", ")}</span>}
                    </div>
                  </div>
                  <button className={`btn ${m.enabled ? "primary" : ""}`} disabled={m.core || toggle.isPending} onClick={() => toggle.mutate(m)} aria-pressed={m.enabled} style={{ minWidth: 92, justifyContent: "center" }}>
                    {m.enabled ? t("enabled") : t("disabled")}
                  </button>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
