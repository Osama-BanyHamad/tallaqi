"use client";
import { useEffect, useRef, useState } from "react";
import { ApiError, getLocale, getSession } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { useAyahAudio } from "@/components/Wird";
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

/** The AI report, written for the reciter: a verdict in words, each ayah with the exact words highlighted,
 *  and tappable recommendations (listen to the ayah with the chosen reciter, re-read it). "Heard" text is muted, never styled as Quran. */
export function AsrSummary({ r, onAdopt, adopted, onReread, onRetry }: { r: AsrResult; onAdopt?: (c: AsrCandidate[]) => void; adopted?: boolean; onReread?: (ayahIndex: number) => void; onRetry?: () => void }) {
  const tr = useT2();
  const audio = useAyahAudio();
  const nothing = (r as AsrResult & { nothing_heard?: boolean }).nothing_heard === true || !r.transcript?.trim();
  const issues = r.ayat.filter((a) => a.status === "issues");
  const missing = issues.reduce((n, a) => n + a.words.filter((w) => w.status === "missing").length, 0);
  const substituted = issues.reduce((n, a) => n + a.words.filter((w) => w.status === "substituted").length, 0);
  const total = missing + substituted;
  const pct = Math.round(r.accuracy * 100);
  const [verdict, tone] = nothing ? [tr("لم نسمع تلاوة واضحة", "No clear recitation was heard"), "var(--ink-3)"]
    : total === 0 ? [tr("ما شاء الله — تلاوة مطابقة", "Excellent, a matching recitation"), "var(--s-strong)"]
    : r.accuracy >= 0.9 ? [tr("جيد جدًا — مواضع قليلة", "Very good, a few spots"), "var(--s-strong)"]
    : r.accuracy >= 0.75 ? [tr("جيد — يحتاج تثبيتًا", "Good, needs consolidation"), "var(--s-needs)"]
    : [tr("يحتاج مراجعة قبل التسميع", "Needs revision before Tasmee'"), "var(--s-weak)"];
  const parts = [missing > 0 && tr(`${missing} منسية`, `${missing} missing`), substituted > 0 && tr(`${substituted} مبدّلة`, `${substituted} substituted`), r.extra.length > 0 && tr(`${r.extra.length} زائدة`, `${r.extra.length} extra`)].filter(Boolean).join(" · ");
  const summary = nothing ? tr("قرّب الميكروفون واقرأ بصوت واضح، ثم أعد التسجيل.", "Move closer to the microphone, read clearly, then record again.")
    : total === 0 ? tr(`كل كلمات المقطع (${r.expected_words}) سُمعت في موضعها.`, `All ${r.expected_words} words were heard in place.`)
    : tr(`${total} ${total === 1 ? "كلمة تحتاج" : "كلمات تحتاج"} انتباهك في ${issues.length} ${issues.length === 1 ? "آية" : "آيات"}: ${parts}.`, `${total} word(s) need attention in ${issues.length} ayah(s): ${parts}.`);
  const key = (a: AsrAyah) => a.key.split(":").map(Number) as [number, number];
  const recos: { icon: string; text: string; onClick?: () => void; tone?: string }[] = [];
  if (nothing) recos.push({ icon: "🎙", text: tr("أعد التسجيل: اقترب من الميكروفون واقرأ بصوت واضح دون ضجيج.", "Record again: closer to the microphone, clear voice, no background noise."), onClick: onRetry });
  else if (issues.length === 0) recos.push({ icon: "✓", text: tr("سمّع المقطع لمعلمك (أو لمن يسمّع لك) ليُعتمد ويرتفع ثباته.", "Recite it to your teacher or listener so it is verified and retention rises."), tone: "var(--s-strong)" });
  else {
    for (const a of issues.slice(0, 3)) {
      const [s, n] = key(a);
      const sub = a.words.find((w) => w.status === "substituted" && w.heard);
      const miss = a.words.filter((w) => w.status === "missing");
      if (audio.available) recos.push({ icon: "▶", text: tr(`استمع للآية ${a.key} بصوت القارئ ثم أعد قراءتها ثلاث مرات.`, `Listen to ayah ${a.key}, then re-read it three times.`), onClick: () => audio.play(s, n) });
      else if (onReread) recos.push({ icon: "↺", text: tr(`أعد قراءة الآية ${a.key} ثلاث مرات.`, `Re-read ayah ${a.key} three times.`), onClick: () => onReread(a.ayah_index) });
      if (sub) recos.push({ icon: "⇄", text: tr(`انتبه للفرق: الصحيح «${sub.expected}» وسُمع «${sub.heard}».`, `Mind the difference: expected “${sub.expected}”, heard “${sub.heard}”.`) });
      if (miss.length >= 2) recos.push({ icon: "👁", text: tr(`الآية ${a.key} فيها ${miss.length} كلمات منسية: اقرأها ثم أخفِ النص واسترجعها.`, `Ayah ${a.key} has ${miss.length} missing words: read it, hide, recall.`), onClick: onReread ? () => onReread(a.ayah_index) : undefined });
    }
    if (issues.length >= 3 && audio.available) recos.push({ icon: "≡", text: tr("المواضع متفرّقة: استمع للمقطع كاملًا ثم سمّعه مرة أخرى.", "Spots are spread out: listen to the whole range, then recite again."), onClick: () => audio.playAll(r.ayat.map(key)) });
    if (r.accuracy < 0.75) recos.push({ icon: "⏳", text: tr("ثبّت المقطع اليوم وأجّل التسميع للمعلم إلى الغد.", "Consolidate today; postpone the teacher's Tasmee' to tomorrow."), tone: "var(--s-weak)" });
    else recos.push({ icon: "🎙", text: tr("بعد الإصلاح، سجّل مرة أخرى للتأكد ثم سمّع لمعلمك.", "After fixing, record again to confirm, then recite to your teacher."), onClick: onRetry });
  }
  return (
    <div className="surface pad" style={{ borderColor: `color-mix(in srgb, ${tone} 45%, var(--rule))` }}>
      <div className="row" style={{ gap: 14, alignItems: "flex-start" }}>
        <div style={{ textAlign: "center", minWidth: 64 }}>
          <div className="num" style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 700, color: tone, lineHeight: 1.1 }}>{nothing ? "—" : `${pct}%`}</div>
          <div className="muted" style={{ fontSize: 11 }}>{tr("مطابقة", "match")}</div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 700, color: tone }}>{verdict}</div>
          <div style={{ fontSize: 13.5, color: "var(--ink-2)", marginTop: 2 }}>{summary}</div>
        </div>
        {onAdopt && total > 0 && <button type="button" className="btn primary sm" disabled={adopted} onClick={() => onAdopt(r.candidates)}>{adopted ? tr("أُضيفت ✓", "Added ✓") : tr(`اعتمد ${r.candidates.length} موضعًا كأخطاء`, `Adopt ${r.candidates.length} as mistakes`)}</button>}
      </div>
      {issues.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 14, fontWeight: 700, marginBottom: 6 }}>{tr("ما يحتاج انتباهك", "What needs attention")}</div>
          <div className="stack" style={{ gap: 8 }}>
            {issues.slice(0, 8).map((a) => {
              const [s, n] = key(a);
              const subs = a.words.filter((w) => w.status === "substituted" && w.heard);
              const m = a.words.filter((w) => w.status === "missing").length;
              return (
                <div key={a.ayah_index} style={{ background: "var(--paper)", border: "1px solid var(--rule)", borderRadius: 12, padding: "10px 12px" }}>
                  <div className="row" style={{ gap: 6, fontSize: 12.5 }}>
                    <b style={{ color: "var(--lapis)" }}>{tr("الآية", "Ayah")} {a.key}</b>
                    {m > 0 && <span className="chip" style={{ background: "color-mix(in srgb, var(--s-weak) 15%, transparent)", color: "var(--s-weak)", fontSize: 11 }}>{tr(`${m} منسية`, `${m} missing`)}</span>}
                    {subs.length > 0 && <span className="chip" style={{ background: "color-mix(in srgb, var(--s-needs) 18%, transparent)", color: "var(--s-needs)", fontSize: 11 }}>{tr(`${subs.length} مبدّلة`, `${subs.length} substituted`)}</span>}
                  </div>
                  <div dir="rtl" style={{ fontFamily: "var(--font-quran)", fontSize: 24, lineHeight: 2, marginTop: 4 }}>
                    {a.words.map((w) => (
                      <span key={w.position} title={w.status === "missing" ? tr(`لم تُسمع «${w.expected}»`, `“${w.expected}” was not heard`) : w.status === "substituted" ? tr(`الصحيح «${w.expected}»${w.heard ? ` — سُمع «${w.heard}»` : ""}`, `Expected “${w.expected}”${w.heard ? `, heard “${w.heard}”` : ""}`) : undefined}
                        style={w.status === "ok" ? undefined : { background: `color-mix(in srgb, ${w.status === "missing" ? "var(--s-weak)" : "var(--s-needs)"} 16%, transparent)`, borderBottom: `3px solid ${w.status === "missing" ? "var(--s-weak)" : "var(--s-needs)"}`, borderRadius: 4, padding: "0 3px", color: w.status === "missing" ? "var(--s-weak)" : undefined, cursor: "help" }}>{w.expected} </span>
                    ))}
                    <span style={{ color: "var(--gold)", fontSize: 18 }}>﴿{n}﴾</span>
                  </div>
                  {subs.length > 0 && <div className="muted" style={{ fontSize: 12 }}>{subs.map((w) => tr(`«${w.expected}» سُمعت «${w.heard}»`, `“${w.expected}” heard as “${w.heard}”`)).join(" · ")}</div>}
                  <div className="row" style={{ gap: 6, marginTop: 6 }}>
                    {audio.available && <button type="button" className="btn sm" onClick={() => audio.play(s, n)}>▶ {tr("استمع", "Listen")}</button>}
                    {onReread && <button type="button" className="btn sm" onClick={() => onReread(a.ayah_index)}>{tr("أعد قراءتها", "Re-read")}</button>}
                  </div>
                </div>
              );
            })}
            {issues.length > 8 && <span className="muted" style={{ fontSize: 12 }}>+{issues.length - 8}</span>}
          </div>
        </div>
      )}
      {r.extra.length > 0 && <p style={{ margin: "10px 0 0", fontSize: 12.5, color: "var(--ink-2)" }}>{tr("كلمات زائدة سُمعت:", "Extra words heard:")} {r.extra.slice(0, 6).map((e) => `«${e.heard}»`).join(" ")}</p>}
      <div style={{ marginTop: 14 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{tr("التوصيات", "Recommendations")}</div>
        {recos.map((x, i) => (
          <div key={i} role={x.onClick ? "button" : undefined} onClick={x.onClick} className="row" style={{ gap: 10, padding: "6px 2px", cursor: x.onClick ? "pointer" : "default", alignItems: "flex-start" }}>
            <span style={{ width: 28, height: 28, borderRadius: 8, display: "grid", placeItems: "center", background: `color-mix(in srgb, ${x.tone ?? "var(--lapis)"} 12%, transparent)`, color: x.tone ?? "var(--lapis)", fontSize: 13, flex: "none" }}>{x.icon}</span>
            <span style={{ fontSize: 13.5 }}>{x.text}</span>
          </div>
        ))}
      </div>
      {audio.current && <button type="button" className="btn sm" style={{ marginTop: 8 }} onClick={audio.stop}>■ {tr("إيقاف الصوت", "Stop audio")}</button>}
      <p className="muted" style={{ margin: "10px 0 0", fontSize: 11.5 }}>{tr("كشف آلي يساعد ولا يقرّر: يقارن صوتك بالنص الموثّق ويقترح؛ الإنسان هو من يعتمد.", "Assistive detection: compares your voice with the verified text and suggests; a human decides.")}</p>
    </div>
  );
}
