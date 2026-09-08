"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { ErrorBox, Loading, PageHead } from "@/components/ui";

type Mod = { key: string; name_ar: string; name_en: string; safety: "GREEN" | "YELLOW" | "RED"; core: boolean; requires: string[]; enabled: boolean };
const GROUP: Record<string, string> = { platform: "المنصة", quran: "القرآن", people: "الأشخاص", ops: "التشغيل", hifz: "الحفظ والمراجعة", parent: "أولياء الأمور", intel: "الذكاء المؤسسي", finance: "المالية", live: "الفصل المباشر" };

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
      <PageHead eyebrow={t("nav_modules")} title={t("modules_title")} sub={t("modules_sub")} />
      {err && <p role="alert" style={{ color: "var(--s-weak)" }}>{err}</p>}
      <div className="stack" style={{ gap: 30 }}>
        {[...groups.entries()].map(([g, mods]) => (
          <section key={g}>
            <div className="section-title"><h2 style={{ fontSize: 17 }}>{locale === "ar" ? GROUP[g] ?? g : g}</h2><small>{g}</small></div>
            <div className="stagger" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
              {mods.map((m) => (
                <div key={m.key} className="surface" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "center", padding: "16px 18px", opacity: m.enabled ? 1 : .72 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>{locale === "en" ? m.name_en : m.name_ar}</div>
                    <div className="muted num" style={{ fontSize: 11.5 }} dir="ltr">{m.key}</div>
                    <div className="row" style={{ gap: 6, marginTop: 8 }}>
                      <span className="chip" style={{ ["--dot" as string]: tone[m.safety] }}><i className="dot" />{t(`safety_${m.safety}` as Key)}</span>
                      {m.core && <span className="chip">{t("core")}</span>}
                      {m.requires.length > 0 && <span className="muted num" style={{ fontSize: 11 }} dir="ltr">← {m.requires.join(", ")}</span>}
                    </div>
                  </div>
                  <button className={`btn sm ${m.enabled ? "primary" : ""}`} disabled={m.core || toggle.isPending} onClick={() => toggle.mutate(m)} aria-pressed={m.enabled} style={{ minWidth: 92 }}>
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
