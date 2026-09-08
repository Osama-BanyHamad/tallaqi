"use client";
import { use, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { fmtNum, splitBasmalah } from "@/lib/quran";
import { ErrorBox, Loading, StatePill } from "@/components/ui";
import type { AyahRow } from "@/components/MemoryMap";

type QAyah = { ayah_index: number; surah: number; ayah: number; key: string; text_uthmani: string; page: number };
type PageData = { page: number; juz: number; surah_starts: string[]; ayat: QAyah[]; attribution: string };
type MType = { key: string; name_ar: string; name_en: string; severity: string };
type Mistake = { ayah_index: number; word_position: number | null; mistake_type: string; severity: string };

/** The Tasmee' screen: the teacher's eyes stay on the Mushaf; a normal evaluation is ≤ 4 taps. */
export default function TasmeePage({ params }: { params: Promise<{ journeyId: string }> }) {
  const { journeyId } = use(params);
  const sp = useSearchParams();
  const router = useRouter();
  const { t, locale } = useI18n();
  const from = Number(sp.get("from"));
  const to = Number(sp.get("to"));
  const purpose = sp.get("purpose") ?? "near";
  const segment = sp.get("segment");
  const halaqah = sp.get("halaqah");

  const range = useQuery({ queryKey: ["range", from, to], queryFn: () => api<{ ayat: QAyah[] }>(`/quran/hafs_asim/range?from=${from}&to=${to}`), enabled: from > 0 && to >= from });
  const firstPage = range.data?.ayat[0]?.page;
  const pageQ = useQuery({ queryKey: ["qpage", firstPage], queryFn: () => api<PageData>(`/quran/hafs_asim/page/${firstPage}`), enabled: !!firstPage });
  const states = useQuery({ queryKey: ["mm", journeyId, "page", firstPage], queryFn: () => api<{ units: AyahRow[] }>(`/journeys/${journeyId}/memory-map?level=page&number=${firstPage}`), enabled: !!firstPage });
  const journey = useQuery({ queryKey: ["journey", journeyId], queryFn: () => api<{ student_name: string; student_code: string }>(`/journeys/${journeyId}`) });
  const types = useQuery({ queryKey: ["mistake-types"], queryFn: () => api<MType[]>("/recitations/mistake-types"), staleTime: Infinity });
  const surahs = useQuery({ queryKey: ["surahs"], queryFn: () => api<{ surahs: { number: number; name_ar: string }[] }>("/quran/hafs_asim/surahs"), staleTime: Infinity });
  const surahName = (n: number) => surahs.data?.surahs.find((s) => s.number === n)?.name_ar ?? String(n);

  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [picking, setPicking] = useState<{ ayah_index: number; word_position: number } | null>(null);
  const [note, setNote] = useState("");
  const [done, setDone] = useState<string | null>(null);
  const idem = useMemo(() => `${journeyId}-${from}-${to}-${Date.now()}`, [journeyId, from, to]);

  const save = useMutation({
    mutationFn: (outcome: "pass" | "repeat" | "partial") => api(`/recitations`, { method: "POST", json: { journey: journeyId, purpose, from_ayah_index: from, to_ayah_index: to, outcome, mistakes, note, plan_segment: segment, halaqah, idempotency_key: idem } }),
    onSuccess: (_d, outcome) => { setDone(outcome); setTimeout(() => router.back(), 900); },
  });

  if (range.isLoading || pageQ.isLoading) return <Loading />;
  if (range.error) return <ErrorBox e={range.error} />;
  const pageData = pageQ.data!;
  const stateOf = new Map((states.data?.units ?? []).map((u) => [u.ayah_index, u]));
  const inRange = (i: number) => i >= from && i <= to;

  function toggleWord(ayah_index: number, word_position: number) {
    if (!inRange(ayah_index)) return;
    const existing = mistakes.find((m) => m.ayah_index === ayah_index && m.word_position === word_position);
    if (existing) { setMistakes(mistakes.filter((m) => m !== existing)); return; }
    setPicking({ ayah_index, word_position });
  }
  function choose(tp: MType) {
    if (!picking) return;
    setMistakes([...mistakes, { ...picking, mistake_type: tp.key, severity: tp.severity }]);
    setPicking(null);
  }

  return (
    <>
      <div className="page-head">
        <div>
          <span className="eyebrow">{t("tasmee")} · {t(`purpose_${purpose}` as Key)}</span>
          <h1>{journey.data?.student_name ?? "…"}</h1>
          <p>{range.data!.ayat[0].key} → {range.data!.ayat.at(-1)!.key} · {t("page")} {fmtNum(pageData.page, locale)} · {t("juz")} {fmtNum(pageData.juz, locale)} — {t("tap_word_hint")}</p>
        </div>
        <div className="row"><span className="pill"><i className="dot" style={{ background: "var(--s-weak)" }} />{t("mistakes")}: <b className="num">{fmtNum(mistakes.length, locale)}</b></span></div>
      </div>
      <div className="with-margin">
        <div className="mushaf">
          <div className="quran">
            {pageData.ayat.map((a) => {
              const { basmalah, body } = splitBasmalah(a.text_uthmani, a.surah, a.ayah);
              const st = stateOf.get(a.ayah_index)?.state;
              const dim = !inRange(a.ayah_index);
              const words = body.split(" ");
              return (
                <span key={a.key}>
                  {a.ayah === 1 && <div className="surah-head">سورة {surahName(a.surah)}</div>}
                  {basmalah && <span className="basmalah">{basmalah}</span>}
                  <span className={`ayah-line ${st === "weak" || st === "critical" ? st : ""}`} style={{ opacity: dim ? .38 : 1 }}>
                    {words.map((w, i) => {
                      const m = mistakes.find((x) => x.ayah_index === a.ayah_index && x.word_position === i + 1);
                      return <span key={i} className={`w ${m ? (m.severity === "major" ? "marked" : "minor") : ""}`} onClick={() => toggleWord(a.ayah_index, i + 1)}>{w} </span>;
                    })}
                    <span className="ayah-end">﴿{fmtNum(a.ayah, "ar")}﴾</span>
                  </span>
                </span>
              );
            })}
          </div>
          <p className="attrib">{pageData.attribution}</p>
        </div>
        <aside className="hashiya">
          <div>
            <h3>{t("mistakes")}</h3>
            {mistakes.length === 0 ? <p>—</p> : (
              <ul style={{ margin: "6px 0 0", paddingInlineStart: 16, fontSize: 13 }}>
                {mistakes.map((m, i) => { const tp = types.data?.find((x) => x.key === m.mistake_type); const ay = pageData.ayat.find((a) => a.ayah_index === m.ayah_index);
                  return <li key={i}>{ay?.key} · {locale === "en" ? tp?.name_en : tp?.name_ar} <button className="btn" style={{ padding: "0 6px", fontSize: 11 }} onClick={() => setMistakes(mistakes.filter((x) => x !== m))}>×</button></li>; })}
              </ul>)}
          </div>
          <div>
            <h3>{t("memory_map")}</h3>
            <div className="stack" style={{ gap: 4 }}>
              {range.data!.ayat.map((a) => { const s = stateOf.get(a.ayah_index); return <div key={a.key} className="row" style={{ fontSize: 12.5, gap: 8 }}><span className="num" style={{ minWidth: 40 }}>{a.key}</span>{s ? <StatePill state={s.state} /> : <StatePill state="not_memorized" />}{s?.retention_score != null && <span className="num muted">{Math.round(s.retention_score * 100)}%</span>}</div>; })}
            </div>
          </div>
          <label className="stack" style={{ gap: 6 }}>
            <h3>{t("note")}</h3>
            <textarea className="input" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <div className="stack" style={{ gap: 8 }}>
            <button className="btn primary" disabled={save.isPending} onClick={() => save.mutate("pass")} style={{ justifyContent: "center", padding: "12px" }}>{t("pass")} ✓</button>
            <div className="row" style={{ gap: 8 }}>
              <button className="btn grow" disabled={save.isPending} onClick={() => save.mutate("partial")} style={{ justifyContent: "center" }}>{t("partial")}</button>
              <button className="btn grow" disabled={save.isPending} onClick={() => save.mutate("repeat")} style={{ justifyContent: "center", borderColor: "var(--s-weak)", color: "var(--s-weak)" }}>{t("repeat")}</button>
            </div>
            {save.error && <ErrorBox e={save.error} />}
          </div>
        </aside>
      </div>
      {picking && (
        <div className="sheet" role="dialog" aria-label={t("mistakes")}>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
            <b>{pageData.ayat.find((a) => a.ayah_index === picking.ayah_index)?.key} · {t("ayah")} — {locale === "ar" ? "نوع الخطأ" : "Mistake type"}</b>
            <button className="btn" onClick={() => setPicking(null)}>×</button>
          </div>
          <div className="types">
            {(types.data ?? []).map((tp) => <button key={tp.key} onClick={() => choose(tp)}>{locale === "en" ? tp.name_en : tp.name_ar}<small>{tp.severity === "major" ? (locale === "ar" ? "خطأ جسيم" : "major") : (locale === "ar" ? "خطأ خفيف" : "minor")}</small></button>)}
          </div>
        </div>
      )}
      {done && <div className="toast" role="status">{t("saved")} — {t(`outcome_${done}` as Key)}</div>}
    </>
  );
}
