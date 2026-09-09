"use client";
import { use, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { fmtNum, splitBasmalah } from "@/lib/quran";
import { ErrorBox, Loading, PageHead } from "@/components/ui";
import { AsrSummary, ReciteCheck, type AsrResult } from "@/components/Recite";

type QAyah = { ayah_index: number; surah: number; ayah: number; key: string; text_uthmani: string };

/** Self-practice: read → hide → recall → reveal. Every hint is the exact verified text from the Quran Core; nothing generative exists here. */
export default function PracticePage({ params }: { params: Promise<{ journeyId: string }> }) {
  const { journeyId } = use(params);
  const sp = useSearchParams();
  const { t, locale } = useI18n();
  const tr = useT2();
  const from = Number(sp.get("from")), to = Number(sp.get("to"));
  const purpose = sp.get("purpose") ?? "near";
  const [hide, setHide] = useState(false);
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const [asr, setAsr] = useState<AsrResult | null>(null);
  const [focus, setFocus] = useState<number | null>(null);
  const q = useQuery({ queryKey: ["range", from, to], queryFn: () => api<{ ayat: QAyah[]; attribution: string }>(`/quran/hafs_asim/range?from=${from}&to=${to}`), enabled: from > 0 });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const ayat = q.data!.ayat;
  return (
    <>
      <PageHead eyebrow={`${tr("تدريب ذاتي", "Self-practice")} · ${t(`purpose_${purpose}` as Key)}`} title={`${ayat[0].key} → ${ayat.at(-1)!.key}`} sub={tr("اقرأ، ثم أخفِ النص واسترجع، ثم اكشف للتحقق. التلميحات من النص الموثّق فقط.", "Read, hide and recall, then reveal to check. Hints are verified text only.")}
        actions={<><button className="btn gold" onClick={() => { setHide(!hide); setRevealed(new Set()); }}>{hide ? tr("أظهر الكل", "Show all") : tr("أخفِ النص واسترجع", "Hide and recall")}</button><ReciteCheck from={from} to={to} journeyId={journeyId} onResult={setAsr} /><span className="chip">{tr("تلميحات", "Hints")}: <b className="num">{fmtNum(revealed.size, locale)}</b></span></>} />
      {asr && <div style={{ maxWidth: 900, marginBottom: 18 }}><AsrSummary r={asr} onRetry={() => setAsr(null)} onReread={(idx) => { setHide(false); setFocus(idx); document.getElementById(`ayah-${idx}`)?.scrollIntoView({ behavior: "smooth", block: "center" }); setTimeout(() => setFocus(null), 4000); }} /></div>}
      <div className="mushaf" style={{ maxWidth: 900 }}>
        <div className="quran">
          {ayat.map((a) => {
            const { basmalah, body } = splitBasmalah(a.text_uthmani, a.surah, a.ayah);
            const hidden = hide && !revealed.has(a.ayah_index);
            const flagged = asr?.ayat.find((x) => x.ayah_index === a.ayah_index)?.status === "issues";
            const words = body.split(" ");
            return (
              <span id={`ayah-${a.ayah_index}`} key={a.key} onClick={() => hidden && setRevealed(new Set([...revealed, a.ayah_index]))} style={{ cursor: hidden ? "pointer" : "default", outline: focus === a.ayah_index ? "2px solid var(--lapis)" : undefined, outlineOffset: 2, background: flagged ? "color-mix(in srgb, var(--s-needs) 16%, transparent)" : undefined, borderRadius: 6 }}>
                {basmalah && <span className="basmalah">{basmalah}</span>}
                {hidden ? <span style={{ color: "var(--ink-3)" }}>{words[0]} {"ـــ ".repeat(Math.min(12, Math.max(1, words.length - 1)))}</span> : words.map((w, i) => {
                  const st = asr?.ayat.find((x) => x.ayah_index === a.ayah_index)?.words.find((x) => x.position === i + 1)?.status;
                  const c = st === "missing" ? "var(--s-weak)" : st === "substituted" ? "var(--s-needs)" : null;
                  return <span key={i} style={c ? { background: `color-mix(in srgb, ${c} 16%, transparent)`, borderBottom: `3px solid ${c}`, borderRadius: 4 } : undefined}>{w}{i < words.length - 1 ? " " : ""}</span>;
                })}
                <span className="ayah-end">﴿{fmtNum(a.ayah, "ar")}﴾</span>{" "}
              </span>);
          })}
        </div>
        <p className="attrib">{q.data!.attribution}</p>
      </div>
    </>
  );
}
