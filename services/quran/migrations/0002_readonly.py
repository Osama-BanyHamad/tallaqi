from django.db import migrations

from services.common.rls import make_readonly


class Migration(migrations.Migration):
    dependencies = [("quran", "0001_initial")]
    operations = make_readonly("quran_release", "quran_surah", "quran_ayah", "quran_unit")
