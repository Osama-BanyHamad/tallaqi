from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("reading", "0001_initial")]
    operations = enable_rls("reading_plan", "reading_log")
