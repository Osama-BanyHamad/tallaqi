"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ApiError, api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { useCapabilities } from "@/components/Shell";

type Draft = { text: string; source: "ai"; provider: string; model: string; disclaimer: string; safety: "YELLOW" };

function useAiAllowed() {
  const caps = useCapabilities();
  return !!caps.data?.modules["ai.assist"]?.enabled && caps.data.permissions.includes("ai.assist.use");
}

const Spark = () => (<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="M19 16l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z" /></svg>);

function errorText(e: unknown, tr: (a: string, b: string) => string) {
  if (e instanceof ApiError && e.code === "ai_unavailable") return tr("المساعد الذكي غير مُعدّ على الخادم.", "The AI assistant is not configured on the server.");
  if (e instanceof ApiError && e.code === "capability_disabled") return tr("المساعد الذكي غير مفعّل لهذه المؤسسة.", "The AI assistant is disabled for this organization.");
  return (e as Error).message;
}

/** Drafts a parent-facing note from the week's real data into the teacher's note field. The teacher edits before saving; nothing is stored automatically. */
export function AiDraftButton({ journeyId, onDraft }: { journeyId: string; onDraft: (text: string) => void }) {
  const tr = useT2();
  const allowed = useAiAllowed();
  const [msg, setMsg] = useState<string | null>(null);
  const m = useMutation({
    mutationFn: () => api<Draft>("/ai/weekly-note", { method: "POST", json: { journey_id: journeyId } }),
    onSuccess: (d) => { onDraft(d.text); setMsg(d.disclaimer); setTimeout(() => setMsg(null), 9000); },
    onError: (e) => { setMsg(errorText(e, tr)); setTimeout(() => setMsg(null), 6000); },
  });
  if (!allowed) return null;
  return (
    <span className="row" style={{ gap: 8 }}>
      <button type="button" className="btn sm" onClick={() => m.mutate()} disabled={m.isPending} title={tr("مسودة من بيانات الطالب — تُراجَع قبل الحفظ", "Draft from the student's data — review before saving")} style={{ color: "var(--gold)", borderColor: "color-mix(in srgb, var(--gold) 50%, var(--rule))" }}>
        <Spark />{m.isPending ? tr("يكتب…", "Drafting…") : tr("مسودة ذكية", "AI draft")}
      </button>
      {msg && <span className="muted" style={{ fontSize: 11.5, maxWidth: 260 }}>{msg}</span>}
    </span>
  );
}

/** Explains the student's state and suggests this week's intervention. Labeled, never saved. */
export function AiExplain({ journeyId }: { journeyId: string }) {
  const tr = useT2();
  const allowed = useAiAllowed();
  const m = useMutation({ mutationFn: () => api<Draft>("/ai/explain-journey", { method: "POST", json: { journey_id: journeyId } }) });
  if (!allowed) return null;
  return (
    <div style={{ marginBottom: 18 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>{tr("المساعد الذكي", "AI assistant")} <span className="chip warn" style={{ fontSize: 10.5, padding: "2px 8px", marginInlineStart: 6 }}>YELLOW</span></h3>
        <button type="button" className="btn sm" onClick={() => m.mutate()} disabled={m.isPending} style={{ color: "var(--gold)" }}><Spark />{m.isPending ? tr("يحلّل…", "Analyzing…") : tr("اشرح الحالة", "Explain")}</button>
      </div>
      {m.error && <p style={{ color: "var(--s-weak)", fontSize: 12.5, margin: "8px 0 0" }}>{errorText(m.error, tr)}</p>}
      {m.data && (
        <div className="surface pad" style={{ marginTop: 10, background: "var(--gold-tint)", borderColor: "color-mix(in srgb, var(--gold) 40%, var(--rule))" }}>
          <p style={{ margin: 0, fontSize: 13.5, whiteSpace: "pre-wrap", color: "var(--ink)" }}>{m.data.text}</p>
          <p className="muted" style={{ margin: "10px 0 0", fontSize: 11.5 }}>{m.data.disclaimer} · {m.data.model}</p>
        </div>
      )}
    </div>
  );
}
