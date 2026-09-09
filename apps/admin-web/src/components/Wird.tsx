"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { useI18n } from "@/lib/i18n";
import { fmtNum } from "@/lib/quran";

type Today = {
  plan: { id: string; pages_per_day: number; current_page: number; khatmat: number; progress: number; reminder_time: string };
  today: { from_page: number; to_page: number; pages: number; from_key: string; to_key: string; from_surah: string; to_surah: string; juz: number; done: boolean; read_today: number };
  streak: number; days_left: number; remaining_pages: number;
};

/** Daily reading card: today's pages, one click to read (with audio), one click to log. */
export function WirdCard() {
  const tr = useT2();
  const { locale } = useI18n();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["wird"], queryFn: () => api<Today>("/reading/today"), retry: false });
  const [days, setDays] = useState(30);
  const [perDay, setPerDay] = useState<number | null>(null);
  const create = useMutation({
    mutationFn: () => api("/reading/plan", { method: "POST", json: perDay ? { kind: "pages", pages_per_day: perDay } : { kind: "khatmah", target_days: days } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wird"] }),
  });
  const log = useMutation({
    mutationFn: (t: Today["today"]) => api("/reading/log", { method: "POST", json: { from_page: t.from_page, to_page: t.to_page, minutes: 0 } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wird"] }),
  });
  const n = (v: number) => fmtNum(v, locale);
  const err = q.error as (Error & { code?: string; status?: number }) | null;
  if (q.isLoading) return null;
  if (err && !/no_plan|404/.test(String(err.code ?? err.message ?? ""))) return null;
  if (!q.data) {
    return (
      <div className="surface pad">
        <span className="eyebrow">{tr("الورد اليومي", "Daily reading")}</span>
        <h3 style={{ margin: "4px 0 6px", fontSize: 17 }}>{tr("ابدأ وردًا ثابتًا", "Start a steady daily wird")}</h3>
        <p className="muted" style={{ margin: "0 0 10px", fontSize: 13 }}>{tr("قراءة من المصحف مستقلة عن خطة الحفظ، بصوت القارئ الذي تختاره.", "Mushaf reading independent of the memorization plan, with a reciter of your choice.")}</p>
        <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
          {[30, 60, 90, 180].map((d) => <button key={d} className={`chip ${!perDay && days === d ? "warn" : ""}`} onClick={() => { setDays(d); setPerDay(null); }}>{tr(`ختمة في ${n(d)} يومًا`, `Khatmah in ${n(d)} days`)}</button>)}
          {[1, 2, 5].map((p) => <button key={p} className={`chip ${perDay === p ? "warn" : ""}`} onClick={() => setPerDay(p)}>{tr(p === 1 ? "صفحة يوميًا" : `${n(p)} صفحات يوميًا`, `${n(p)} page(s)/day`)}</button>)}
        </div>
        <button className="btn primary" onClick={() => create.mutate()} disabled={create.isPending}>{tr("ابدأ الورد", "Start")}</button>
      </div>
    );
  }
  const d = q.data;
  const t = d.today;
  return (
    <div className="surface pad" style={{ borderColor: t.done ? "color-mix(in srgb, var(--s-strong) 40%, var(--rule))" : "color-mix(in srgb, var(--gold) 50%, var(--rule))" }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <span className="eyebrow">{tr("الورد اليومي", "Daily reading")}</span>
          <h3 style={{ margin: "4px 0 2px", fontSize: 17 }}>{t.done ? tr("أتممت وردك اليوم", "Today's wird is done") : tr(`صفحة ${n(t.from_page)} إلى ${n(t.to_page)}`, `Pages ${n(t.from_page)}–${n(t.to_page)}`)}</h3>
          <p className="muted" style={{ margin: 0, fontSize: 13 }}>{t.from_surah} {t.from_key.split(":")[1]} ← {t.to_surah} {t.to_key.split(":")[1]} · {tr("الجزء", "Juz")} {n(t.juz)}</p>
        </div>
        <div style={{ textAlign: "center", minWidth: 64 }}>
          <div className="num" style={{ fontSize: 22, fontWeight: 700 }}>{n(Math.round(d.plan.progress * 100))}٪</div>
          <div className="muted" style={{ fontSize: 11 }}>{tr("الختمة", "khatmah")}</div>
        </div>
      </div>
      <div className="row" style={{ gap: 8, marginTop: 12, flexWrap: "wrap" }}>
        <Link className="btn primary" href={`/read?from=${t.from_page}&to=${t.to_page}&wird=1`}>{t.done ? tr("تابع القراءة", "Keep reading") : tr("اقرأ الآن", "Read now")}</Link>
        {!t.done && <button className="btn" onClick={() => log.mutate(t)} disabled={log.isPending}>{tr("قرأته من مصحفي", "Read it elsewhere")}</button>}
      </div>
      <div className="row muted" style={{ gap: 14, marginTop: 10, fontSize: 12.5 }}>
        <span>{tr(`${n(d.streak)} يوم متتالٍ`, `${n(d.streak)}-day streak`)}</span>
        <span>{tr(`${n(d.plan.pages_per_day)} صفحات يوميًا`, `${n(d.plan.pages_per_day)} pages/day`)}</span>
        <span>{tr(`${n(d.days_left)} يومًا للختمة`, `${n(d.days_left)} days to finish`)}</span>
      </div>
    </div>
  );
}

type Reciter = { key: string; name_ar: string; name_en: string; base: string };
type PageData = { page: number; juz: number; attribution: string; ayat: { ayah_index: number; surah: number; ayah: number; key: string; text_uthmani: string }[] };

/** Shared ayah audio: reciter registry + one <audio> element. Click an ayah to hear it; keeps playing the page in order. */
export function useAyahAudio() {
  const reg = useQuery({ queryKey: ["reciters"], queryFn: () => api<{ reciters: Reciter[]; pattern: string; note: string }>("/quran/reciters"), retry: false, staleTime: 3600_000 });
  const [reciter, setReciterKey] = useState<string>(() => { try { return localStorage.getItem("talaqqi.reciter") ?? "husary"; } catch { return "husary"; } });
  const [current, setCurrent] = useState<[number, number] | null>(null);
  const queue = useRef<[number, number][]>([]);
  const audio = useRef<HTMLAudioElement | null>(null);
  useEffect(() => {
    const a = new Audio();
    a.onended = () => { const next = queue.current.shift(); if (next) play(next[0], next[1], false); else setCurrent(null); };
    a.onerror = () => setCurrent(null);
    audio.current = a;
    return () => { a.pause(); audio.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const r = reg.data?.reciters.find((x) => x.key === reciter) ?? reg.data?.reciters[0];
  const url = (s: number, a: number) => `${r?.base ?? ""}${(reg.data?.pattern ?? "{surah:03d}{ayah:03d}.mp3").replace("{surah:03d}", String(s).padStart(3, "0")).replace("{ayah:03d}", String(a).padStart(3, "0"))}`;
  function play(s: number, a: number, clearQueue = true) {
    const el = audio.current; if (!el || !r) return;
    if (clearQueue) queue.current = [];
    if (current && current[0] === s && current[1] === a && !el.paused && clearQueue) { el.pause(); setCurrent(null); return; }
    el.src = url(s, a); setCurrent([s, a]); el.play().catch(() => setCurrent(null));
  }
  function playAll(list: [number, number][]) { if (!list.length) return; queue.current = list.slice(1); play(list[0][0], list[0][1], false); }
  function stop() { audio.current?.pause(); queue.current = []; setCurrent(null); }
  function setReciter(k: string) { setReciterKey(k); try { localStorage.setItem("talaqqi.reciter", k); } catch {} }
  return { available: !!reg.data && !!r, reciters: reg.data?.reciters ?? [], reciter: r, setReciter, current, play, playAll, stop, note: reg.data?.note };
}

/** Mushaf page reader with per-ayah audio. */
export function PageReader({ from, to, wird }: { from: number; to: number; wird?: boolean }) {
  const tr = useT2();
  const { locale } = useI18n();
  const qc = useQueryClient();
  const [page, setPage] = useState(from);
  const [font, setFont] = useState(28);
  const audio = useAyahAudio();
  const q = useQuery({ queryKey: ["qpage", page], queryFn: () => api<PageData>(`/quran/hafs_asim/page/${page}`), staleTime: 86_400_000 });
  const surahs = useQuery({ queryKey: ["surahs"], queryFn: () => api<{ surahs: { number: number; name_ar: string }[] }>("/quran/hafs_asim/surahs"), staleTime: 86_400_000 });
  const names = new Map((surahs.data?.surahs ?? []).map((s) => [s.number, s.name_ar]));
  const finish = useMutation({ mutationFn: () => api("/reading/log", { method: "POST", json: { from_page: from, to_page: Math.max(from, page), minutes: 0 } }), onSuccess: () => qc.invalidateQueries({ queryKey: ["wird"] }) });
  const n = (v: number) => fmtNum(v, locale);
  const atEnd = page >= to;
  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <div className="row" style={{ gap: 6 }}>
          <button className="btn sm" onClick={() => setPage((p) => Math.max(1, p - 1))}>{tr("السابقة", "Previous")}</button>
          <span className="chip">{tr("صفحة", "Page")} {n(page)}{q.data ? ` · ${tr("الجزء", "Juz")} ${n(q.data.juz)}` : ""}</span>
          <button className="btn sm" onClick={() => setPage((p) => Math.min(604, p + 1))}>{tr("التالية", "Next")}</button>
        </div>
        <div className="row" style={{ gap: 6 }}>
          {audio.available && (
            <select className="input" style={{ height: 34, padding: "0 8px", fontSize: 13 }} value={audio.reciter?.key} onChange={(e) => audio.setReciter(e.target.value)}>
              {audio.reciters.map((r) => <option key={r.key} value={r.key}>{locale === "en" ? r.name_en : r.name_ar}</option>)}
            </select>
          )}
          {audio.available && q.data && <button className="btn sm" onClick={() => audio.playAll(q.data!.ayat.map((a) => [a.surah, a.ayah]))}>▶ {tr("استمع للصفحة", "Play page")}</button>}
          {audio.current && <button className="btn sm" onClick={audio.stop}>■ {tr("إيقاف", "Stop")}</button>}
          <button className="btn sm" onClick={() => setFont((f) => (f >= 36 ? 22 : f + 4))}>A</button>
        </div>
      </div>
      {q.isLoading && <p className="muted">…</p>}
      {q.data && (
        <div className="mushaf" dir="rtl" style={{ fontSize: font, lineHeight: 2 }}>
          {q.data.ayat.map((a) => {
            const playing = audio.current && audio.current[0] === a.surah && audio.current[1] === a.ayah;
            return (
              <span key={a.ayah_index}>
                {a.ayah === 1 && <div className="surah-head">{tr("سورة", "Surah")} {names.get(a.surah) ?? a.surah}</div>}
                <span className={`ayah ${playing ? "playing" : ""}`} title={audio.available ? tr("اضغط لسماع الآية", "Click to listen") : undefined} onClick={() => audio.available && audio.play(a.surah, a.ayah)} style={{ cursor: audio.available ? "pointer" : "default", background: playing ? "color-mix(in srgb, var(--lapis) 12%, transparent)" : undefined, borderRadius: 6 }}>
                  {a.text_uthmani}
                  <span className="ayah-no"> ﴿{n(a.ayah)}﴾ </span>
                </span>
              </span>
            );
          })}
          <p className="muted" style={{ fontSize: 11, textAlign: "center", marginTop: 12 }}>{q.data.attribution}{audio.note ? ` · ${audio.note}` : ""}</p>
        </div>
      )}
      {wird && (
        <div className="row" style={{ justifyContent: "flex-end", gap: 8 }}>
          {!atEnd && <button className="btn" onClick={() => setPage((p) => p + 1)}>{tr("الصفحة التالية", "Next page")}</button>}
          {atEnd && <Link className="btn primary" href="/me" onClick={() => finish.mutate()}>{tr("أنهيت وردي اليوم", "Finished today's wird")}</Link>}
        </div>
      )}
    </div>
  );
}
