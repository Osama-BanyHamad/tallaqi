"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { Field, Modal, Select } from "@/components/forms";
import { useCapabilities } from "@/components/Shell";

type Unit = { number: number; first_ayah_index: number; last_ayah_index: number; first_key?: string };
type Surah = { number: number; name_ar: string; ayah_count: number; start_index: number };

/** Formal assessment on a Juz, a Surah, or a page range. Records a graded session (purpose=assessment) through the same Tasmee' screen. */
export function AssessmentLauncher({ journeyId }: { journeyId: string }) {
  const tr = useT2();
  const router = useRouter();
  const caps = useCapabilities();
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"juz" | "surah" | "pages">("juz");
  const [n, setN] = useState("30");
  const [p1, setP1] = useState("604"), [p2, setP2] = useState("604");
  const juz = useQuery({ queryKey: ["units-juz"], queryFn: () => api<Unit[]>("/quran/hafs_asim/units/juz"), staleTime: Infinity, enabled: open });
  const surahs = useQuery({ queryKey: ["surahs"], queryFn: () => api<{ surahs: Surah[] }>("/quran/hafs_asim/surahs"), staleTime: Infinity, enabled: open });
  const pages = useQuery({ queryKey: ["quran-pages"], queryFn: () => api<Unit[]>("/quran/hafs_asim/units/page"), staleTime: Infinity, enabled: open });
  if (!caps.data?.permissions.includes("hifz.assessments.record") || !caps.data.modules["hifz.assessments"]?.enabled) return null;
  function start() {
    let from = 0, to = 0;
    if (kind === "juz") { const u = juz.data?.find((x) => x.number === Number(n)); if (!u) return; from = u.first_ayah_index; to = u.last_ayah_index; }
    else if (kind === "surah") { const s = surahs.data?.surahs.find((x) => x.number === Number(n)); if (!s) return; from = s.start_index; to = s.start_index + s.ayah_count - 1; }
    else { const a = pages.data?.find((x) => x.number === Number(p1)), b = pages.data?.find((x) => x.number === Number(p2)); if (!a || !b) return; from = Math.min(a.first_ayah_index, b.first_ayah_index); to = Math.max(a.last_ayah_index, b.last_ayah_index); }
    if (to - from > 700) { alert(tr("النطاق كبير جدًا؛ قسّم الاختبار على جلسات (حد ٧٠٠ آية).", "Range too large; split the exam (max 700 Ayat).")); return; }
    router.push(`/tasmee/${journeyId}?purpose=assessment&from=${from}&to=${to}`);
  }
  return (
    <>
      <button className="btn" onClick={() => setOpen(true)}>{tr("اختبار", "Assessment")}</button>
      {open && (
        <Modal title={tr("اختبار رسمي", "Formal assessment")} onClose={() => setOpen(false)} width={480}>
          <div className="stack" style={{ gap: 14 }}>
            <p className="muted" style={{ margin: 0, fontSize: 13.5 }}>{tr("يُسجَّل الاختبار بدرجة، ويُعطى وزنًا أعلى في الثبات من التسميع اليومي. النطاق الكبير يُقسَّم على جلسات.", "Assessments are graded and weigh more than daily Tasmee' in retention. Large ranges are split across sessions.")}</p>
            <Field label={tr("النطاق", "Scope")}><Select value={kind} onChange={(v) => setKind(v as typeof kind)} options={[{ value: "juz", label: tr("جزء", "Juz") }, { value: "surah", label: tr("سورة", "Surah") }, { value: "pages", label: tr("صفحات", "Pages") }]} /></Field>
            {kind === "juz" && <Field label={tr("الجزء", "Juz")}><Select value={n} onChange={setN} options={Array.from({ length: 30 }, (_, i) => ({ value: String(i + 1), label: `${tr("الجزء", "Juz")} ${i + 1}` }))} /></Field>}
            {kind === "surah" && <Field label={tr("السورة", "Surah")}><Select value={n} onChange={setN} options={(surahs.data?.surahs ?? []).map((s) => ({ value: String(s.number), label: `${s.number}. ${s.name_ar}` }))} /></Field>}
            {kind === "pages" && <div className="row"><Field label={tr("من صفحة", "From page")}><input className="input" type="number" min={1} max={604} value={p1} onChange={(e) => setP1(e.target.value)} /></Field><Field label={tr("إلى صفحة", "To page")}><input className="input" type="number" min={1} max={604} value={p2} onChange={(e) => setP2(e.target.value)} /></Field></div>}
            <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn primary" onClick={start}>{tr("ابدأ الاختبار", "Start")}</button></div>
          </div>
        </Modal>
      )}
    </>
  );
}
