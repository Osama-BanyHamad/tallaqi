from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("audit", "0003_initial")]
    operations = enable_rls("audit_log")
