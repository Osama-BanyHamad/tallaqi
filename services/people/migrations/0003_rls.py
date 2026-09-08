from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("people", "0002_initial")]
    operations = enable_rls("people_person", "people_student", "people_guardian", "people_guardian_link", "people_consent",
                            "people_staff", "people_halaqah", "people_halaqah_staff", "people_enrollment", "people_attendance")
