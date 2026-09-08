"""Load the pinned Quran Core release into PostgreSQL (the only sanctioned write path)."""
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from packages.quran_core import get_core
from services.quran.models import Ayah, QuranRelease, Surah, Unit


class Command(BaseCommand):
    help = "Load/verify the Quran Core release into the read-only quran_* tables."

    def add_arguments(self, parser):
        parser.add_argument("--riwayah", default="hafs_asim")

    def handle(self, *args, **opts):
        core = get_core(opts["riwayah"])   # raises on any checksum mismatch
        version = core.manifest["version"]
        meta = core.manifest["riwayat"][core.riwayah]
        existing = QuranRelease.objects.filter(version=version, riwayah=core.riwayah).first()
        if existing and existing.text_root_sha256 == meta["text_root_sha256"] and Ayah.objects.filter(riwayah=core.riwayah).count() == core.ayah_count:
            self.stdout.write(f"quran-core {version} ({core.riwayah}) already loaded and verified")
            return
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("SELECT set_config('app.quran_core_load', 'on', true)")
            Ayah.objects.filter(riwayah=core.riwayah).delete()
            Surah.objects.filter(riwayah=core.riwayah).delete()
            Unit.objects.filter(riwayah=core.riwayah).delete()
            Surah.objects.bulk_create([Surah(riwayah=core.riwayah, **s.__dict__) for s in core.surahs])
            hizb_of, rub_of = {}, {}
            for u in core.units:
                for i in range(u.first_ayah_index, u.last_ayah_index + 1):
                    if u.unit_type == "hizb":
                        hizb_of[i] = u.number
                    elif u.unit_type == "rub":
                        rub_of[i] = u.number
            Ayah.objects.bulk_create([Ayah(riwayah=core.riwayah, ayah_index=a.ayah_index, surah=a.surah, ayah=a.ayah, key=a.key,
                                           text_uthmani=a.text_uthmani, word_count=a.word_count, page=core.page_of(a.ayah_index),
                                           juz=core.juz_of(a.ayah_index), hizb=hizb_of[a.ayah_index], rub=rub_of[a.ayah_index],
                                           sha256=a.sha256) for a in core.ayat], batch_size=1000)
            Unit.objects.bulk_create([Unit(riwayah=core.riwayah, unit_type=u.unit_type, number=u.number,
                                           first_ayah_index=u.first_ayah_index, last_ayah_index=u.last_ayah_index) for u in core.units]
                                     + [Unit(riwayah=core.riwayah, unit_type="page", number=p.page,
                                             first_ayah_index=p.first_ayah_index, last_ayah_index=p.last_ayah_index) for p in core.pages])
            QuranRelease.objects.update_or_create(version=version, defaults={
                "riwayah": core.riwayah, "text_root_sha256": meta["text_root_sha256"], "manifest": core.manifest, "active": True})
        self.stdout.write(self.style.SUCCESS(f"loaded quran-core {version} ({core.riwayah}): {core.ayah_count} ayat, 604 pages"))
