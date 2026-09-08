from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("rbac", "0001_initial")]
    operations = enable_rls("rbac_role", "rbac_role_permission", "rbac_role_assignment")
