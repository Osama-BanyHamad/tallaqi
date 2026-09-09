#!/usr/bin/env python3
"""Build the branded /stats/ summary page from Caddy's JSON access log.

Counts that matter for the project, computed from the raw log (no third-party trackers):
- app downloads: one per device (IP + user agent) per day per file, so range requests for one download are not double-counted
- unique visitors per day (IP + user agent), page views (HTML pages, not assets or API), API calls
- top pages and referrers
The full GoAccess report is linked as full.html.
"""
from __future__ import annotations

import html
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/talaqqi/logs/caddy")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/opt/talaqqi/stats/index.html")
DAYS = 30
SELF_AGENTS = ("Python-urllib", "curl/", "HeadlessChrome", "Go-http-client")
ASSET_PREFIXES = ("/_next/", "/api/", "/readyz", "/healthz", "/downloads/", "/stats", "/favicon", "/promo-poster", "/robots.txt")


def load():
    rows = []
    for f in sorted(LOG_DIR.glob("access.log*")):
        with f.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                req = r.get("request", {})
                ua = (req.get("headers", {}).get("User-Agent") or [""])[0]
                if any(s in ua for s in SELF_AGENTS):
                    continue
                ts = datetime.fromtimestamp(float(r.get("ts", 0)), tz=timezone.utc)
                rows.append({"day": ts.strftime("%Y-%m-%d"), "hour": ts.hour, "ip": req.get("remote_ip", ""), "ua": ua,
                             "uri": req.get("uri", "").split("?")[0], "status": int(r.get("status", 0)),
                             "ref": (req.get("headers", {}).get("Referer") or [""])[0], "host": req.get("host", "")})
    return rows


def build(rows):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    since = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime("%Y-%m-%d")
    rows = [r for r in rows if r["day"] >= since]
    visitors_day = defaultdict(set)
    views_day = Counter()
    api_day = Counter()
    pages = Counter()
    refs = Counter()
    dl = defaultdict(set)          # file -> {(ip, ua, day)}
    dl_day = defaultdict(set)      # day -> {(ip, ua, file)}
    for r in rows:
        key = (r["ip"], r["ua"])
        visitors_day[r["day"]].add(key)
        u = r["uri"]
        if u.startswith("/downloads/") and r["status"] in (200, 206):
            name = u.rsplit("/", 1)[-1]
            dl[name].add((r["ip"], r["ua"], r["day"]))
            dl_day[r["day"]].add((r["ip"], r["ua"], name))
        elif u.startswith("/api/"):
            api_day[r["day"]] += 1
        elif not u.startswith(ASSET_PREFIXES) and "." not in u.rsplit("/", 1)[-1] and r["status"] < 400:
            views_day[r["day"]] += 1
            pages[u] += 1
        ref = r["ref"]
        if ref and "tallaqi.com" not in ref:
            refs[ref.split("?")[0]] += 1
    days = sorted(set(list(visitors_day) + list(views_day) + list(dl_day)))
    apk_total = sum(len(v) for k, v in dl.items() if k.endswith(".apk"))
    video_total = sum(len(v) for k, v in dl.items() if k.endswith(".mp4"))
    total_visitors = len({k for s in visitors_day.values() for k in s})
    return {
        "today": today, "since": since, "days": days,
        "visitors_today": len(visitors_day.get(today, ())), "visitors_total": total_visitors,
        "views_today": views_day.get(today, 0), "views_total": sum(views_day.values()),
        "apk_today": len({x for x in dl_day.get(today, ()) if x[2].endswith(".apk")}), "apk_total": apk_total, "video_total": video_total,
        "downloads_by_file": sorted(((k, len(v)) for k, v in dl.items()), key=lambda x: -x[1]),
        "table": [(d, len(visitors_day.get(d, ())), views_day.get(d, 0), api_day.get(d, 0), len({x for x in dl_day.get(d, ()) if x[2].endswith('.apk')})) for d in reversed(days)][:DAYS],
        "pages": pages.most_common(12), "refs": refs.most_common(10),
    }


def ar(n):
    return str(n).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


def load_funnel():
    f = OUT.parent / "funnel.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    except ValueError:
        return None


def render(s):
    e = html.escape
    fn = load_funnel()
    funnel = ""
    if fn:
        t = fn.get("tenants", {})
        funnel = f"""<h2>الاستخدام الفعلي (من قاعدة البيانات)</h2>
<div class="kpis">
 <div class="kpi accent"><div class="l">حسابات مسجّلة</div><div class="v">{ar(fn.get('accounts', 0))}</div><div class="s">جديدة آخر ٧ أيام: {ar(fn.get('signups', {}).get('7d', 0))} · آخر ٢٤ ساعة: {ar(fn.get('signups', {}).get('24h', 0))}</div></div>
 <div class="kpi gold"><div class="l">متعلّمون مستقلون</div><div class="v">{ar(fn.get('solo_tenants', 0))}</div><div class="s">رحلات فردية أُنشئت من الموقع</div></div>
 <div class="kpi"><div class="l">متعلّمون نشطون (٧ أيام)</div><div class="v">{ar(fn.get('active_learners_7d', 0))}</div><div class="s">رحلة فيها تسميع خلال الأسبوع · من {ar(fn.get('journeys', 0))} رحلة</div></div>
 <div class="kpi"><div class="l">تسميعات مسجّلة (٧ أيام)</div><div class="v">{ar(fn.get('recitations', {}).get('7d', 0))}</div><div class="s">آخر ٢٤ ساعة: {ar(fn.get('recitations', {}).get('24h', 0))}</div></div>
 <div class="kpi"><div class="l">تسميع ذكي (٧ أيام)</div><div class="v">{ar(fn.get('ai', {}).get('asr_7d', 0))}</div><div class="s">مسودات ذكية: {ar(fn.get('ai', {}).get('drafts_7d', 0))}</div></div>
 <div class="kpi"><div class="l">مؤسسات</div><div class="v">{ar(sum(v for k, v in t.items() if k != 'solo'))}</div><div class="s">{', '.join(f'{k}: {v}' for k, v in t.items()) or '—'}</div></div>
</div>"""
    rows = "".join(f"<tr><td class=num>{e(d)}</td><td class=num>{ar(v)}</td><td class=num>{ar(p)}</td><td class=num>{ar(a)}</td><td class=num><b>{ar(k)}</b></td></tr>" for d, v, p, a, k in s["table"])
    files = "".join(f"<tr><td dir=ltr class=num>{e(k)}</td><td class=num><b>{ar(n)}</b></td></tr>" for k, n in s["downloads_by_file"]) or "<tr><td colspan=2 class=muted>لا تحميلات بعد</td></tr>"
    pages = "".join(f"<tr><td dir=ltr class=num>{e(u)}</td><td class=num>{ar(n)}</td></tr>" for u, n in s["pages"]) or "<tr><td colspan=2 class=muted>—</td></tr>"
    refs = "".join(f"<tr><td dir=ltr class=num>{e(u[:80])}</td><td class=num>{ar(n)}</td></tr>" for u, n in s["refs"]) or "<tr><td colspan=2 class=muted>لا مُحيلات خارجية بعد</td></tr>"
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>تَلَقِّي · إحصاءات الزيارات والتحميلات</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@600;800&family=IBM+Plex+Sans+Arabic:wght@400;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>
:root{{--night:#0d1230;--night2:#182253;--ink:#101320;--ink2:#474b58;--ink3:#868a96;--rule:#e5e3dc;--ground:#f3f2ee;--surface:#fff;--lapis:#1b2c74;--gold:#b99441;--gold2:#d4b56a;--green:#2f7a5b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--ground);color:var(--ink);font-family:"IBM Plex Sans Arabic",sans-serif;font-size:15px;line-height:1.7}}
header{{background:linear-gradient(170deg,var(--night2),var(--night));color:#eeeadf;padding:34px 6vw 28px;border-bottom:1px solid var(--gold)}}
header h1{{font-family:"Noto Kufi Arabic";font-size:26px;margin:6px 0 0}}header .eyebrow{{color:var(--gold2);font-size:12.5px;font-weight:600}}header .sub{{color:#8f97c4;font-size:13px;margin-top:6px}}
main{{padding:26px 6vw 60px;max-width:1200px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:26px}}
.kpi{{background:var(--surface);border:1px solid var(--rule);border-radius:14px;padding:16px 18px 14px;box-shadow:0 8px 18px -12px rgba(16,19,32,.2)}}
.kpi.accent{{background:linear-gradient(135deg,#2a3f95,var(--lapis));color:#fff;border:0}}.kpi.gold{{background:linear-gradient(135deg,var(--gold2),var(--gold));color:#1f1806;border:0}}
.kpi .l{{font-size:12.5px;opacity:.8}}.kpi .v{{font-family:"Noto Kufi Arabic";font-size:34px;font-weight:800;line-height:1.1;margin-top:4px}}.kpi .s{{font-size:12px;opacity:.75;margin-top:4px}}
h2{{font-family:"Noto Kufi Arabic";font-size:17px;margin:26px 0 10px}}
table{{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--rule);border-radius:12px;overflow:hidden}}th,td{{padding:9px 12px;border-bottom:1px solid var(--rule);text-align:start;font-size:13.5px}}th{{background:#faf9f6;color:var(--ink3);font-weight:600;font-size:12px}}tr:last-child td{{border-bottom:0}}
.num{{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}}.muted{{color:var(--ink3)}}.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
a.btn{{display:inline-block;margin-top:22px;padding:10px 18px;border-radius:10px;background:var(--night);color:#eeeadf;text-decoration:none;font-weight:600}}footer{{color:var(--ink3);font-size:12px;margin-top:30px}}
</style></head><body>
<header><div class="eyebrow">تَلَقِّي · لوحة الإحصاءات</div><h1>الزيارات وتحميلات التطبيق</h1><div class="sub">آخر {ar(DAYS)} يومًا · من {e(s['since'])} إلى {e(s['today'])} (UTC) · تُحدَّث كل ساعة · لا متتبّعات خارجية، وعناوين IP لا تُعرض</div></header>
<main>
<div class="kpis">
 <div class="kpi gold"><div class="l">تحميلات تطبيق أندرويد</div><div class="v">{ar(s['apk_total'])}</div><div class="s">اليوم: {ar(s['apk_today'])} · جهاز واحد يُحسب مرة في اليوم</div></div>
 <div class="kpi accent"><div class="l">زوّار فريدون</div><div class="v">{ar(s['visitors_total'])}</div><div class="s">اليوم: {ar(s['visitors_today'])}</div></div>
 <div class="kpi"><div class="l">مشاهدات الصفحات</div><div class="v">{ar(s['views_total'])}</div><div class="s">اليوم: {ar(s['views_today'])}</div></div>
 <div class="kpi"><div class="l">مشاهدات الفيديو الدعائي</div><div class="v">{ar(s['video_total'])}</div><div class="s">تشغيلات فريدة للملف</div></div>
</div>
<div class="grid2">
 <div><h2>التحميلات حسب الملف</h2><table><thead><tr><th>الملف</th><th>تحميلات فريدة</th></tr></thead><tbody>{files}</tbody></table></div>
 <div><h2>مصادر الزيارات (مُحيلات خارجية)</h2><table><thead><tr><th>المصدر</th><th>زيارات</th></tr></thead><tbody>{refs}</tbody></table></div>
</div>
{funnel}
<h2>حسب اليوم</h2>
<table><thead><tr><th>اليوم</th><th>زوّار</th><th>مشاهدات صفحات</th><th>طلبات API</th><th>تحميلات APK</th></tr></thead><tbody>{rows}</tbody></table>
<h2>أكثر الصفحات زيارة</h2>
<table><thead><tr><th>الصفحة</th><th>مشاهدات</th></tr></thead><tbody>{pages}</tbody></table>
<a class="btn" href="full.html">التقرير الكامل (GoAccess): البلدان، المتصفحات، الأجهزة، الساعات ←</a>
<footer>تُحسب الأرقام من سجل الوصول لخادم Caddy مباشرة. الزائر الفريد = عنوان IP + المتصفح في اليوم نفسه. تُستبعد فحوصات الصحة وسكربتات التحقق الخاصة بنا.</footer>
</main></body></html>"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(build(load())), encoding="utf-8")
    print(f"summary page written: {OUT}")
