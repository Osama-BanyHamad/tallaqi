"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useT2 } from "@/lib/t2";
import { ErrorBox, Loading, PageHead } from "@/components/ui";
import { Field, Select, grid2 } from "@/components/forms";

type Tenant = { slug: string; name: string; name_en: string; kind: string; default_locale: string; locales: string[]; timezone: string; currency: string; calendar: string; default_riwayah: string; default_mushaf_type: string; branding: { accent?: string; app_name?: string }; recording_allowed: boolean };

export default function SettingsPage() {
  const tr = useT2();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["tenant"], queryFn: () => api<Tenant>("/tenant") });
  const [f, setF] = useState<Tenant | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => { if (q.data && !f) setF(q.data); }, [q.data, f]);
  const save = useMutation({ mutationFn: () => api("/tenant", { method: "PATCH", json: f }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["tenant"] }); qc.invalidateQueries({ queryKey: ["capabilities"] }); setSaved(true); setTimeout(() => setSaved(false), 1500); } });
  if (q.isLoading || !f) return <Loading />;
  if (q.error) return <ErrorBox e={q.error} />;
  return (
    <>
      <PageHead eyebrow={tr("الإعدادات", "Settings")} title={tr("إعدادات المؤسسة", "Organization settings")} sub={tr("الاسم والهوية واللغة والعملة وسياسة التسجيل.", "Name, identity, language, currency, and the recording policy.")}
        actions={<><Link className="btn" href="/settings/accounts">{tr("الحسابات والأدوار", "Accounts & roles")}</Link><Link className="btn" href="/settings/modules">{tr("الوحدات", "Modules")}</Link><Link className="btn" href="/settings/audit">{tr("سجل التدقيق", "Audit log")}</Link></>} />
      <form className="surface pad stack" style={{ gap: 18, maxWidth: 820 }} onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
        <div style={grid2}>
          <Field label={tr("اسم المؤسسة (عربي)", "Name (Arabic)")}><input className="input" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required /></Field>
          <Field label={tr("الاسم (إنجليزي)", "Name (English)")}><input className="input" dir="ltr" value={f.name_en} onChange={(e) => setF({ ...f, name_en: e.target.value })} /></Field>
          <Field label={tr("النوع", "Kind")}><Select value={f.kind} onChange={(v) => setF({ ...f, kind: v })} options={[["center", "مركز", "Center"], ["academy", "أكاديمية", "Academy"], ["institution", "مؤسسة", "Institution"], ["mosque", "مسجد", "Mosque"], ["organization", "منظمة", "Organization"], ["individual", "معلم مستقل", "Individual teacher"]].map(([v, a, e]) => ({ value: v, label: tr(a, e) }))} /></Field>
          <Field label={tr("اللغة الافتراضية", "Default language")}><Select value={f.default_locale} onChange={(v) => setF({ ...f, default_locale: v })} options={[{ value: "ar", label: "العربية" }, { value: "en", label: "English" }]} /></Field>
          <Field label={tr("المنطقة الزمنية", "Time zone")}><input className="input" dir="ltr" value={f.timezone} onChange={(e) => setF({ ...f, timezone: e.target.value })} /></Field>
          <Field label={tr("العملة", "Currency")}><input className="input" dir="ltr" maxLength={3} value={f.currency} onChange={(e) => setF({ ...f, currency: e.target.value.toUpperCase() })} /></Field>
          <Field label={tr("التقويم", "Calendar")}><Select value={f.calendar} onChange={(v) => setF({ ...f, calendar: v })} options={[{ value: "both", label: tr("هجري وميلادي", "Hijri + Gregorian") }, { value: "gregorian", label: tr("ميلادي", "Gregorian") }, { value: "hijri", label: tr("هجري", "Hijri") }]} /></Field>
          <Field label={tr("الرواية الافتراضية", "Default Riwayah")}><Select value={f.default_riwayah} onChange={(v) => setF({ ...f, default_riwayah: v })} options={[{ value: "hafs_asim", label: "حفص عن عاصم" }]} /></Field>
          <Field label={tr("اسم التطبيق للطلاب", "App name shown to students")}><input className="input" value={f.branding?.app_name ?? ""} onChange={(e) => setF({ ...f, branding: { ...f.branding, app_name: e.target.value } })} /></Field>
          <Field label={tr("لون الهوية", "Accent color")}><input className="input" type="color" value={f.branding?.accent ?? "#1b2c74"} onChange={(e) => setF({ ...f, branding: { ...f.branding, accent: e.target.value } })} style={{ height: 42, padding: 4 }} /></Field>
        </div>
        <div className="surface pad" style={{ background: "var(--surface-2)" }}>
          <label className="row" style={{ gap: 12, cursor: "pointer" }}>
            <input type="checkbox" checked={f.recording_allowed} onChange={(e) => setF({ ...f, recording_allowed: e.target.checked })} />
            <div><b>{tr("السماح بتسجيل الفصول المباشرة", "Allow live session recording")}</b><p className="muted" style={{ margin: 0, fontSize: 13 }}>{tr("عند الإيقاف لا تُنشأ أي تسجيلات على الخادم ولا تُستدعى واجهات التسجيل. لا يمكن منع التسجيل بجهاز خارجي؛ هذا وعد بالتصميم لا بالاستحالة.", "When off, no server-side recordings are created and provider recording APIs are never called. Recording with another device cannot be prevented; this is a promise by design, not impossibility.")}</p></div>
          </label>
        </div>
        {save.error && <p style={{ color: "var(--s-weak)", margin: 0 }}>{(save.error as Error).message}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn primary" disabled={save.isPending}>{saved ? tr("تم الحفظ ✓", "Saved ✓") : tr("حفظ", "Save")}</button></div>
      </form>
    </>
  );
}
