"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PageHead } from "@/components/ui";
import { PageReader } from "@/components/Wird";
import { useT2 } from "@/lib/t2";

export default function ReadPage() {
  return <Suspense><ReadInner /></Suspense>;
}

function ReadInner() {
  const tr = useT2();
  const sp = useSearchParams();
  const from = Math.max(1, Math.min(604, parseInt(sp.get("from") ?? "1") || 1));
  const to = Math.max(from, Math.min(604, parseInt(sp.get("to") ?? String(from)) || from));
  const wird = sp.get("wird") === "1";
  return (
    <>
      <PageHead eyebrow={wird ? tr("الورد اليومي", "Daily reading") : tr("المصحف", "Mushaf")} title={tr("قراءة", "Reading")} sub={tr("اضغط أي آية لسماعها بصوت القارئ.", "Click any ayah to hear it recited.")} />
      <PageReader from={from} to={to} wird={wird} />
    </>
  );
}
