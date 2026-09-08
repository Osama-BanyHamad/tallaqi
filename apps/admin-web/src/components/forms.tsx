"use client";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

export function Field({ label, children, hint, span }: { label: string; children: React.ReactNode; hint?: string; span?: number }) {
  return (
    <label className="stack" style={{ gap: 6, gridColumn: span ? `span ${span}` : undefined }}>
      <span style={{ fontSize: 13, color: "var(--ink-2)", fontWeight: 500 }}>{label}</span>
      {children}
      {hint && <span className="muted" style={{ fontSize: 12 }}>{hint}</span>}
    </label>
  );
}

export function Select({ value, onChange, options, placeholder }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; placeholder?: string }) {
  return (
    <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

/** Rendered through a portal so animated/transformed ancestors never trap the fixed overlay. */
export function Modal({ title, onClose, children, width = 640 }: { title: string; onClose: () => void; children: React.ReactNode; width?: number }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!mounted) return null;
  return createPortal(
    <div role="dialog" aria-modal aria-label={title} onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(13,18,48,.45)", backdropFilter: "blur(3px)", display: "grid", placeItems: "center", zIndex: 40, padding: 20 }}>
      <div className="surface fade-up" onClick={(e) => e.stopPropagation()} style={{ width: `min(${width}px, 100%)`, maxHeight: "92dvh", overflow: "auto", padding: 0 }}>
        <div className="row" style={{ justifyContent: "space-between", padding: "16px 22px", borderBottom: "1px solid var(--rule)" }}>
          <h2 style={{ fontSize: 18 }}>{title}</h2>
          <button className="btn sm" onClick={onClose} aria-label="close">×</button>
        </div>
        <div style={{ padding: 22 }}>{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export const grid2: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 };
