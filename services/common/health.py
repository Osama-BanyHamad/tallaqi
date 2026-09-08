from django.db import connection
from django.http import JsonResponse


def healthz(_request):
    return JsonResponse({"status": "ok"})


def readyz(_request):
    checks = {}
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:  # pragma: no cover
        checks["database"] = f"error: {e}"
    try:
        from packages.quran_core import get_core
        core = get_core()
        checks["quran_core"] = f"ok ({core.riwayah}, {core.ayah_count} ayat, verified)"
    except Exception as e:
        checks["quran_core"] = f"error: {e}"
    ok = all(v.startswith("ok") for v in checks.values())
    return JsonResponse({"status": "ok" if ok else "degraded", "checks": checks}, status=200 if ok else 503)
