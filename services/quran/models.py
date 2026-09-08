"""Quran Core tables: loaded from the versioned release, read-only for the application role
(trigger raises on write unless app.quran_core_load='on'). Not tenant-scoped."""
from django.db import models


class QuranRelease(models.Model):
    version = models.CharField(max_length=20, primary_key=True)
    riwayah = models.CharField(max_length=32)
    text_root_sha256 = models.CharField(max_length=64)
    manifest = models.JSONField()
    loaded_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "quran_release"


class Surah(models.Model):
    riwayah = models.CharField(max_length=32)
    number = models.PositiveSmallIntegerField()
    ayah_count = models.PositiveSmallIntegerField()
    start_index = models.PositiveIntegerField()
    name_ar = models.CharField(max_length=64)
    name_tr = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64)
    revelation = models.CharField(max_length=10)
    revelation_order = models.PositiveSmallIntegerField()
    rukus = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "quran_surah"
        unique_together = [("riwayah", "number")]


class Ayah(models.Model):
    riwayah = models.CharField(max_length=32)
    ayah_index = models.PositiveIntegerField()
    surah = models.PositiveSmallIntegerField()
    ayah = models.PositiveSmallIntegerField()
    key = models.CharField(max_length=8)
    text_uthmani = models.TextField()
    word_count = models.PositiveSmallIntegerField()
    page = models.PositiveSmallIntegerField()
    juz = models.PositiveSmallIntegerField()
    hizb = models.PositiveSmallIntegerField()
    rub = models.PositiveSmallIntegerField()
    sha256 = models.CharField(max_length=64)

    class Meta:
        db_table = "quran_ayah"
        unique_together = [("riwayah", "ayah_index")]
        indexes = [models.Index(fields=["riwayah", "surah", "ayah"]), models.Index(fields=["riwayah", "page"])]


class Unit(models.Model):
    riwayah = models.CharField(max_length=32)
    unit_type = models.CharField(max_length=8)   # juz | hizb | rub | manzil | page
    number = models.PositiveSmallIntegerField()
    first_ayah_index = models.PositiveIntegerField()
    last_ayah_index = models.PositiveIntegerField()

    class Meta:
        db_table = "quran_unit"
        unique_together = [("riwayah", "unit_type", "number")]
