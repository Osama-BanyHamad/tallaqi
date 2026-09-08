from django.db import migrations

from services.common.rls import enable_rls


class Migration(migrations.Migration):
    dependencies = [("finance", "0001_initial")]
    operations = enable_rls("finance_number_sequence", "finance_fee_plan", "finance_student_fee_plan", "finance_invoice",
                            "finance_invoice_line", "finance_payment")
