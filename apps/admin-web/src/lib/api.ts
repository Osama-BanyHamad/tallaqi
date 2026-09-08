"use client";

/** Thin API client: JWT in memory/localStorage, X-Tenant header, Arabic default, typed errors. */

export type Membership = { tenant_slug: string; tenant_name: string; tenant_kind: string; roles: string[] };
export type Session = { access: string; refresh: string; account: { id: string; email: string; full_name: string; locale: string }; memberships: Membership[]; tenant: string };

const KEY = "talaqqi.session";

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  try { const raw = localStorage.getItem(KEY); return raw ? (JSON.parse(raw) as Session) : null; } catch { return null; }
}
export function setSession(s: Session | null) {
  try { s ? localStorage.setItem(KEY, JSON.stringify(s)) : localStorage.removeItem(KEY); } catch { /* private mode */ }
}
export function getLocale(): "ar" | "en" {
  try { return (localStorage.getItem("talaqqi.locale") as "ar" | "en") || "ar"; } catch { return "ar"; }
}
export function setLocale(l: "ar" | "en") { try { localStorage.setItem("talaqqi.locale", l); } catch { /* ignore */ } }

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public body?: unknown) { super(message); }
}

async function refreshAccess(s: Session): Promise<Session | null> {
  const r = await fetch("/api/v1/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: s.refresh }) });
  if (!r.ok) return null;
  const j = await r.json();
  const next = { ...s, access: j.access, refresh: j.refresh ?? s.refresh };
  setSession(next);
  return next;
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}, retry = true): Promise<T> {
  const s = getSession();
  const headers: Record<string, string> = { Accept: "application/json", "Accept-Language": getLocale(), ...(init.headers as Record<string, string> | undefined) };
  if (init.json !== undefined) headers["Content-Type"] = "application/json";
  if (s?.access) headers.Authorization = `Bearer ${s.access}`;
  if (s?.tenant) headers["X-Tenant"] = s.tenant;
  const r = await fetch(`/api/v1${path}`, { ...init, headers, body: init.json !== undefined ? JSON.stringify(init.json) : init.body });
  if (r.status === 401 && s && retry) {
    const n = await refreshAccess(s);
    if (n) return api<T>(path, init, false);
    setSession(null);
    if (typeof window !== "undefined") window.location.href = "/login";
  }
  if (!r.ok) {
    let body: { code?: string; detail?: unknown } = {};
    try { body = await r.json(); } catch { /* not json */ }
    throw new ApiError(r.status, body.code ?? "error", typeof body.detail === "string" ? body.detail : r.statusText, body);
  }
  if (r.status === 204) return undefined as T;
  return (await r.json()) as T;
}

export async function login(email: string, password: string, tenant?: string): Promise<Session> {
  const r = await fetch("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json", "Accept-Language": getLocale() }, body: JSON.stringify({ email, password }) });
  if (!r.ok) {
    const b = await r.json().catch(() => ({}));
    throw new ApiError(r.status, b.code ?? "error", b.detail ?? "تعذّر تسجيل الدخول");
  }
  const j = await r.json();
  const slug = tenant ?? j.memberships?.[0]?.tenant_slug ?? "";
  const s: Session = { ...j, tenant: slug };
  setSession(s);
  return s;
}
