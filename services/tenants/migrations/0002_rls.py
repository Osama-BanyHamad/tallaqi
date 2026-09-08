from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("tenants", "0001_initial")]
    operations = enable_rls("tenants_branch", "tenants_module")
