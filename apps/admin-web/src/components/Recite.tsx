"use client";
import { useEffect, useRef, useState } from "react";
import { ApiError, getLocale, getSession } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { useCapabilities } from "@/components/Shell";

export type AsrWord = { position: number; expected: string; status: "ok" | "missing" | "substituted"; heard: string | null };
export type AsrAyah = { ayah_index: number; key: string; status: "ok" | "issues"; words: AsrWord[]; missing: number; substituted: number };
export type AsrCandidate = { ayah_index: number; word_position: number; kind: "omission" | "substitution" | "addition"; mistake_type: string | null; severity: string; heard: string | null; expected: string | null };
export type AsrResult = { transcript: string; accuracy: number; expected_words: number; matched: number; ayat: AsrAyah[]; extra: { after_ayah_index: number; after_position: number; heard: string }[]; candidates: AsrCandidate[]; model: string; disclaimer: string };

export function useAsrAllowed() {
  const caps = useCapabilities();
  return !!caps.data?.modules["hifz.asr"]?.enabled && caps.data.permissions.includes("hifz.asr.use");
}

async function uploadCheck(blob: Blob, from: number, to: number, journeyId?: string): Promise<AsrResult> {
  const s = getSession();
  const fd = new FormData();
  fd.append("audio", blob, blob.type.includes("mp4") ? "recitation.m4a" : "recitation.webm");
  fd.append("from_ayah_index", String(from)); fd.append("to_ayah_index", String(to));
  if (journeyId) fd.append("journey_id", journeyId);
  const r = await fetch("/api/v1/ai/asr-check", { method: "POST", body: fd, headers: { Authorization: `Bearer ${s?.access}`, "X-Tenant": s?.tenant ?? "", "Accept-Language": getLocale() } });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new ApiError(r.status, body.code ?? "error", typeof body.detail === "string" ? body.detail : r.statusText, body);
  return body as AsrResult;
}

const Mic = ({ on }: { on?: boolean }) => (<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="3" width="6" height="11" rx="3" fill={on ? "currentColor" : "none"} /><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8" /></svg>);

/**
 * Records the reciter, sends the audio to the tenant's speech provider, and reports candidate mismatches against the verified text.
 * YELLOW: nothing is recorded automatically; the caller decides what to do with the candidates.
 */
export function ReciteCheck({ from, to, journeyId, onResult, compact }: { from: number; to: number; journeyId?: string; onResult: (r: AsrResult | null) => void; compact?: boolean }) {
  const tr = useT2();
  const allowed = useAsrAllowed();
  const [state, setState] = useState<"idle" | "recording" | "uploading" | "done" | "error">("idle");
  const [msg, setMsg] = useState<string | null>(null);
  const [secs, setSecs] = useState(0);
  const [level, setLevel] = useState(0);
  const rec = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | null>(null);
  const audioCtx = useRef<AudioContext | null>(null);
  const raf = useRef<number | null>(null);

  useEffect(() => () => { stopAll(); }, []);
  function stopAll() {
    if (timer.current) window.clearInterval(timer.current);
    if (raf.current) cancelAnimationFrame(raf.current);
    rec.current?.stream.getTracks().forEach((t) => t.stop());
    audioCtx.current?.close().catch(() => {});
  }

  async function start() {
    setMsg(null); onResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((m) => MediaRecorder.isTypeSupported(m));
      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunks.current = [];
      mr.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
      mr.onstop = async () => {
        stopAll();
        const blob = new Blob(chunks.current, { type: mr.mimeType || "audio/webm" });
        if (blob.size < 2000) { setState("error"); setMsg(tr("لم يُسجَّل صوت. جرّب مرة أخرى.", "No audio captured. Try again.")); return; }
        setState("uploading");
        try { const r = await uploadCheck(blob, from, to, journeyId); onResult(r); setState("done"); }
        catch (e) { setState("error"); setMsg(e instanceof ApiError && e.code === "ai_unavailable" ? tr("خدمة الصوت غير مُعدّة على الخادم.", "Speech service is not configured.") : (e as Error).message); }
      };
      // live level meter
      const ctx = new AudioContext(); audioCtx.current = ctx;
      const src = ctx.createMediaStreamSource(stream); const an = ctx.createAnalyser(); an.fftSize = 512; src.connect(an);
      const buf = new Uint8Array(an.frequencyBinCount);
      const tick = () => { an.getByteTimeDomainData(buf); let s = 0; for (const v of buf) { const d = (v - 128) / 128; s += d * d; } setLevel(Math.min(1, Math.sqrt(s / buf.length) * 4)); raf.current = requestAnimationFrame(tick); };
      tick();
      rec.current = mr; mr.start(250); setState("recording"); setSecs(0);
      timer.current = window.setInterval(() => setSecs((x) => x + 1), 1000);
    } catch {
      setState("error"); setMsg(tr("لم يُسمح باستخدام الميكروفون.", "Microphone permission was denied."));
    }
  }
  function stop() { rec.current?.stop(); if (timer.current) window.clearInterval(timer.current); }

  if (!allowed) return null;
  const busy = state === "uploading";
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row" style={{ gap: 10, flexWrap: "nowrap" }}>
        {state !== "recording" ? (
          <button type="button" className={`btn ${compact ? "sm" : ""} gold`} onClick={start} disabled={busy} style={{ gap: 8 }}><Mic />{busy ? tr("يحلّل التلاوة…", "Analyzing…") : tr("سمّع بالذكاء الاصطناعي", "Recite with AI check")}</button>
        ) : (
          <button type="button" className={`btn ${compact ? "sm" : ""} danger`} onClick={stop} style={{ gap: 8 }}><Mic on />{tr("أوقف وحلّل", "Stop & check")} · <span className="num">{String(Math.floor(secs / 60)).padStart(2, "0")}:{String(secs % 60).padStart(2, "0")}</span></button>
        )}
        {state === "recording" && <span aria-hidden style={{ display: "inline-flex", gap: 3, alignItems: "flex-end", height: 22 }}>{[0.5, 0.8, 1, 0.7, 0.4].map((k, i) => <i key={i} style={{ width: 4, borderRadius: 2, background: "var(--s-weak)", height: 4 + 18 * level * k, transition: "height .08s" }} />)}</span>}
      </div>
      {msg && <span style={{ fontSize: 12.5, color: "var(--s-weak)" }}>{msg}</span>}
    </div>
  );
}

/** Result summary: accuracy, per-Ayah status, and the list of candidates with what was heard (in muted text, never styled as Quran). */
export function AsrSummary({ r, onAdopt, adopted }: { r: AsrResult; onAdopt?: (c: AsrCandidate[]) => void; adopted?: boolean }) {
  const tr = useT2();
  const pct = Math.round(r.accuracy * 100);
  const tone = pct >= 95 ? "var(--s-strong)" : pct >= 85 ? "var(--s-needs)" : "var(--s-weak)";
  const label = (c: AsrCandidate) => c.kind === "omission" ? tr("إسقاط", "Omitted") : c.kind === "addition" ? tr("زيادة", "Added") : tr("إبدال", "Substituted");
  return (
    <div className="surface pad" style={{ borderColor: "color-mix(in srgb, var(--gold) 45%, var(--rule))", background: "var(--gold-tint)" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div><span className="eyebrow">{tr("كشف آلي", "AI check")} · YELLOW</span><div style={{ fontFamily: "var(--font-display)", fontSize: 30, fontWeight: 700, color: tone, lineHeight: 1.1, marginTop: 4 }}>{pct}%</div><div className="muted" style={{ fontSize: 12.5 }}>{r.matched} / {r.expected_words} {tr("كلمة مطابقة", "words matched")}</div></div>
        {onAdopt && r.candidates.length > 0 && <button type="button" className="btn primary sm" disabled={adopted} onClick={() => onAdopt(r.candidates)}>{adopted ? tr("أُضيفت ✓", "Added ✓") : tr(`اعتمد ${r.candidates.length} اقتراحًا`, `Adopt ${r.candidates.length} candidates`)}</button>}
      </div>
      {r.candidates.length === 0 ? <p style={{ margin: "10px 0 0", fontSize: 14 }}>{tr("لا فروق مسموعة عن النص الموثّق في هذا المقطع.", "No audible differences from the verified text in this range.")}</p> : (
        <div className="stack" style={{ gap: 4, marginTop: 10 }}>
          {r.candidates.slice(0, 12).map((c, i) => (
            <div key={i} className="row" style={{ fontSize: 13, gap: 8, justifyContent: "space-between" }}>
              <span><span className="chip" style={{ padding: "1px 8px", fontSize: 11 }}>{label(c)}</span> <span className="num muted">{r.ayat.find((a) => a.ayah_index === c.ayah_index)?.key} · {c.word_position}</span></span>
              <span className="muted" style={{ fontSize: 12 }}>{c.expected && <>{tr("المتوقع", "expected")}: <b style={{ fontFamily: "var(--font-quran)" }}>{c.expected}</b></>}{c.heard && <> · {tr("سُمع", "heard")}: {c.heard}</>}</span>
            </div>
          ))}
          {r.candidates.length > 12 && <span className="muted" style={{ fontSize: 12 }}>+{r.candidates.length - 12}</span>}
        </div>
      )}
      <p className="muted" style={{ margin: "10px 0 0", fontSize: 11.5 }}>{r.disclaimer} · {r.model}</p>
    </div>
  );
}
