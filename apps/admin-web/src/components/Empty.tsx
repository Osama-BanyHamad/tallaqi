"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { useCapabilities } from "@/components/Shell";

/** An empty screen that teaches: one sentence and the one button that fixes it. */
export function EmptyState({ title, body, action, onAction, href, icon }: { title: string; body?: string; action?: string; onAction?: () => void; href?: string; icon?: React.ReactNode }) {
  return (
    <div className="surface fade-up" style={{ padding: "48px 28px", textAlign: "center", display: "grid", justifyItems: "center", gap: 10 }}>
      <div style={{ width: 64, height: 64, borderRadius: 999, background: "var(--lapis-tint)", display: "grid", placeItems: "center", color: "var(--lapis)" }}>{icon ?? <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H12v18H6.5A2.5 2.5 0 0 0 4 23z" /><path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H12v18h5.5a2.5 2.5 0 0 1 2.5 2z" /></svg>}</div>
      <h2 style={{ fontSize: 20 }}>{title}</h2>
      {body && <p className="muted" style={{ margin: 0, maxWidth: "46ch" }}>{body}</p>}
      {action && (href ? <Link href={href} className="btn primary" style={{ marginTop: 8 }}>{action}</Link> : <button className="btn primary" style={{ marginTop: 8 }} onClick={onAction}>{action}</button>)}
    </div>
  );
}

type Counts = { branches: number; halaqat: number; staff: number; students: number };

/** Owner's first-run checklist: five steps, ticks itself, disappears when the center is set up. */
export function SetupChecklist() {
  const tr = useT2();
  const caps = useCapabilities();
  const q = useQuery({
    queryKey: ["setup-counts"],
    queryFn: async (): Promise<Counts> => {
      const [b, h, s, st] = await Promise.all([api<{ count: number }>("/branches?page_size=1"), api<{ count: number }>("/halaqat?page_size=1"), api<{ count: number }>("/staff?page_size=1"), api<{ count: number }>("/students?page_size=1")]);
      return { branches: b.count, halaqat: h.count, staff: s.count, students: st.count };
    },
    enabled: !!caps.data?.permissions.includes("people.students.write"),
  });
  if (!q.data) return null;
  const c = q.data;
  const steps = [
    { done: c.branches > 0, ar: "أضف فرعك الأول", en: "Add your first branch", href: "/settings" },
    { done: c.staff > 0, ar: "أضف معلمًا وأنشئ له حساب دخول", en: "Add a teacher and create their login", href: "/staff" },
    { done: c.halaqat > 0, ar: "أنشئ حلقة واربطها بالمعلم", en: "Create a Halaqah and assign the teacher", href: "/halaqat" },
    { done: c.students > 0, ar: "سجّل الطلاب في الحلقة", en: "Enroll students", href: "/students" },
    { done: c.students > 0 && c.halaqat > 0, ar: "افتح حلقة اليوم وسجّل أول تسميع", en: "Open today's Halaqah and record the first Tasmee'", href: "/halaqat" },
  ];
  const doneCount = steps.filter((s) => s.done).length;
  if (doneCount === steps.length && c.students > 3) return null;
  return (
    <div className="surface pad fade-up" style={{ marginBottom: 26, borderColor: "color-mix(in srgb, var(--gold) 45%, var(--rule))", background: "linear-gradient(135deg, var(--gold-tint), var(--surface))" }}>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
        <div><span className="eyebrow">{tr("إعداد المركز", "Center setup")}</span><h2 style={{ fontSize: 18, marginTop: 4 }}>{tr("خمس خطوات وتبدأ أول حلقة", "Five steps and the first Halaqah starts")}</h2></div>
        <span className="chip"><b className="num">{doneCount}</b> / {steps.length}</span>
      </div>
      <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8 }}>
        {steps.map((s, i) => (
          <li key={i}>
            <Link href={s.href} className="row" style={{ gap: 10, padding: "10px 12px", borderRadius: 10, background: s.done ? "transparent" : "var(--surface)", border: "1px solid var(--rule)", color: "inherit", opacity: s.done ? .6 : 1, textDecoration: s.done ? "line-through" : "none" }}>
              <span style={{ width: 22, height: 22, borderRadius: 999, display: "grid", placeItems: "center", background: s.done ? "var(--s-strong)" : "var(--lapis-tint)", color: s.done ? "#fff" : "var(--lapis)", fontSize: 12, fontWeight: 700 }}>{s.done ? "✓" : i + 1}</span>
              <span style={{ fontSize: 13.5 }}>{tr(s.ar, s.en)}</span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Human names for learning-policy keys, from the API (falls back to the key). */
export function usePolicyNames() {
  const { data } = useQuery({ queryKey: ["policies"], queryFn: () => api<{ key: string; name_ar: string; name_en: string }[]>("/policies"), staleTime: Infinity });
  return (key: string, locale: "ar" | "en") => { const p = data?.find((x) => x.key === key); return p ? (locale === "en" ? p.name_en || p.name_ar : p.name_ar) : key.replaceAll("_", " "); };
}
