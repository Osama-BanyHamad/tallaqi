"""Read-only Quran API. Responses are immutable per release version and cacheable."""
from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.quran_core import get_core

ATTRIBUTION = settings.TALAQQI["QURAN_TEXT_ATTRIBUTION"]


def _ayah(core, a):
    return {"ayah_index": a.ayah_index, "surah": a.surah, "ayah": a.ayah, "key": a.key, "text_uthmani": a.text_uthmani,
            "word_count": a.word_count, "page": core.page_of(a.ayah_index), "juz": core.juz_of(a.ayah_index)}


class QuranView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        try:
            response["X-Quran-Core-Version"] = get_core().manifest["version"]
            response["Cache-Control"] = "public, max-age=86400"
        except Exception:
            pass
        return response


class ManifestView(QuranView):
    def get(self, request):
        core = get_core()
        m = dict(core.manifest)
        return Response({"version": m["version"], "riwayat": m["riwayat"], "sources": m["sources"], "attribution": ATTRIBUTION})


class SurahListView(QuranView):
    def get(self, request, riwayah="hafs_asim"):
        core = get_core(riwayah)
        return Response({"riwayah": riwayah, "attribution": ATTRIBUTION, "surahs": [
            {"number": s.number, "name_ar": s.name_ar, "name_tr": s.name_tr, "name_en": s.name_en, "ayah_count": s.ayah_count,
             "start_index": s.start_index, "revelation": s.revelation, "first_page": core.page_of(s.start_index)} for s in core.surahs]})


class AyahView(QuranView):
    def get(self, request, riwayah, key):
        core = get_core(riwayah)
        try:
            a = core.ayah(key)
        except KeyError:
            return Response({"code": "not_found", "detail": "Unknown ayah key."}, status=404)
        return Response({"attribution": ATTRIBUTION, **_ayah(core, a)})


class RangeView(QuranView):
    def get(self, request, riwayah):
        core = get_core(riwayah)
        try:
            first = int(request.query_params.get("from"))
            last = int(request.query_params.get("to"))
        except (TypeError, ValueError):
            return Response({"code": "bad_request", "detail": "from/to ayah_index required."}, status=400)
        if not (1 <= first <= last <= core.ayah_count) or last - first > 700:
            return Response({"code": "bad_request", "detail": "Invalid range (max 700 ayat)."}, status=400)
        return Response({"attribution": ATTRIBUTION, "ayat": [_ayah(core, a) for a in core.range(first, last)]})


class PageView(QuranView):
    def get(self, request, riwayah, page: int):
        core = get_core(riwayah)
        if not 1 <= page <= len(core.pages):
            return Response({"code": "not_found"}, status=404)
        p = core.page(page)
        ayat = core.page_ayat(page)
        surah_starts = [a.key for a in ayat if a.ayah == 1]
        return Response({"attribution": ATTRIBUTION, "page": page, "juz": p.juz, "first_ayah_index": p.first_ayah_index,
                         "last_ayah_index": p.last_ayah_index, "surah_starts": surah_starts, "ayat": [_ayah(core, a) for a in ayat]})


class UnitsView(QuranView):
    def get(self, request, riwayah, unit_type):
        core = get_core(riwayah)
        if unit_type == "page":
            return Response([{"number": p.page, "first_ayah_index": p.first_ayah_index, "last_ayah_index": p.last_ayah_index,
                              "juz": p.juz, "first_key": p.first_key} for p in core.pages])
        units = core.units_of(unit_type)
        if not units:
            return Response({"code": "not_found"}, status=404)
        return Response([{"number": u.number, "first_ayah_index": u.first_ayah_index, "last_ayah_index": u.last_ayah_index,
                          "first_key": core.ayah_by_index(u.first_ayah_index).key,
                          "first_page": core.page_of(u.first_ayah_index), "last_page": core.page_of(u.last_ayah_index)} for u in units])
