"use client";
/** A deterministic sample Memory Map (a memorizer around Juz 26 → 30 with real-looking variance). Used on the public site and login. */
const STATES = ["mastered", "strong", "recent", "needs_revision", "weak", "critical"] as const;
const COLS: Record<string, string> = { mastered: "var(--s-mastered)", strong: "var(--s-strong)", recent: "var(--s-recent)", needs_revision: "var(--s-needs)", weak: "var(--s-weak)", critical: "var(--s-critical)" };

function h(i: number) { return (((i + 1) * 2654435761) >>> 0) % 1000 / 1000; }

export function samplePages(): { page: number; juz: number; state: string | null }[] {
  const out = [];
  for (let p = 1; p <= 604; p++) {
    const juz = Math.min(30, Math.floor((p - 2) / 20) + 1);
    let state: string | null = null;
    if (p >= 520) {
      const r = h(p);
      state = p >= 582 ? (r < .55 ? "strong" : r < .8 ? "mastered" : r < .9 ? "needs_revision" : "recent")
        : p >= 550 ? (r < .5 ? "strong" : r < .75 ? "needs_revision" : r < .9 ? "weak" : "critical")
        : (r < .35 ? "needs_revision" : r < .7 ? "weak" : r < .85 ? "critical" : "strong");
    }
    out.push({ page: p, juz, state });
  }
  return out;
}

export function SampleMap({ dark, rows = [24, 25, 26, 27, 28, 29, 30], compact }: { dark?: boolean; rows?: number[]; compact?: boolean }) {
  const pages = samplePages();
  return (
    <div style={{ display: "grid", gap: compact ? 4 : 6 }} aria-hidden>
      {rows.map((j) => (
        <div key={j} style={{ display: "grid", gridTemplateColumns: "44px 1fr", gap: 10, alignItems: "center" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: dark ? "var(--night-muted)" : "var(--ink-3)" }}>Juz {j}</span>
          <div style={{ display: "grid", gridTemplateColumns: `repeat(${pages.filter((p) => p.juz === j).length}, 1fr)`, gap: 3 }}>
            {pages.filter((p) => p.juz === j).map((p) => (
              <span key={p.page} style={{ height: compact ? 12 : 18, borderRadius: 3, background: p.state ? COLS[p.state] : dark ? "rgba(255,255,255,.08)" : "var(--s-none)" }} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
