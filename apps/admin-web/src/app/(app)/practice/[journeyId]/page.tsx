"use client";
import { use, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { useT2 } from "@/lib/t2";
import { fmtNum, splitBasmalah } from "@/lib/quran";
import { ErrorBox, Loading, PageHead } from "@/components/ui";

type QAyah = { ayah_index: number; surah: number; ayah: number; key: string; text_uthmani: string };

/** Self-practice: read → hide → recall → reveal. Every hint is the exact verified text from the Quran Core; nothing generative exists here. */
export default function PracticePage({ params }: { params: Promise<{ journeyId: string }> }) {
  const { journeyId } = use(params);
  void journeyId;
  const sp = useSearchParams();
  const { t, locale } = useI18n();
  const tr = useT2();
  const from = Number(sp.get("from")), to = Number(sp.get("to"));
  const purpose = sp.get("purpose") ?? "near";
  const [hide, setHide] = useState(false);
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const q = useQuery({ queryKey: ["range", from, to], queryFn: () => api<{ ayat: QAyah[]; attribution: string }>(`/quran/hafs_asim/range?from=${from}&to=${to}`), enabled: from > 0 });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  const ayat = q.data!.ayat;
  return (
    <>
      <PageHead eyebrow={`${tr("تدريب ذاتي", "Self-practice")} · ${t(`purpose_${purpose}` as Key)}`} title={`${ayat[0].key} → ${ayat.at(-1)!.key}`} sub={tr("اقرأ، ثم أخفِ النص واسترجع، ثم اكشف للتحقق. التلميحات من النص الموثّق فقط.", "Read, hide and recall, then reveal to check. Hints are verified text only.")}
        actions={<><button className="btn gold" onClick={() => { setHide(!hide); setRevealed(new Set()); }}>{hide ? tr("أظهر الكل", "Show all") : tr("أخفِ النص واسترجع", "Hide and recall")}</button><span className="chip">{tr("تلميحات", "Hints")}: <b className="num">{fmtNum(revealed.size, locale)}</b></span></>} />
      <div className="mushaf" style={{ maxWidth: 900 }}>
        <div className="quran">
          {ayat.map((a) => {
            const { basmalah, body } = splitBasmalah(a.text_uthmani, a.surah, a.ayah);
            const hidden = hide && !revealed.has(a.ayah_index);
            const words = body.split(" ");
            return (
              <span key={a.key} onClick={() => hidden && setRevealed(new Set([...revealed, a.ayah_index]))} style={{ cursor: hidden ? "pointer" : "default" }}>
                {basmalah && <span className="basmalah">{basmalah}</span>}
                {hidden ? <span style={{ color: "var(--ink-3)" }}>{words[0]} {"ـــ ".repeat(Math.min(12, Math.max(1, words.length - 1)))}</span> : body}
                <span className="ayah-end">﴿{fmtNum(a.ayah, "ar")}﴾</span>{" "}
              </span>);
          })}
        </div>
        <p className="attrib">{q.data!.attribution}</p>
      </div>
    </>
  );
}
