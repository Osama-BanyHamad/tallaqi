from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("hifz", "0002_initial")]
    operations = enable_rls("hifz_journey", "hifz_journey_event", "hifz_ayah_state", "hifz_ayah_state_event", "hifz_daily_plan",
                            "hifz_plan_segment", "hifz_plan_action", "hifz_mistake_type", "hifz_recitation_session", "hifz_mistake_event")
