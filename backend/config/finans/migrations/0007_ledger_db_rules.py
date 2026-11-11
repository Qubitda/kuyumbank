# LedgerEntry: hareket_tipi / ISO PB / CONTRA⇒contra_of DB kuralları

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finans", "0006_f5_022_tedarikci_hak_edis"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    hareket_tipi__in=[
                        "SATIS",
                        "TAHSILAT",
                        "IADE",
                        "MAHSUP",
                        "CONTRA",
                        "DUZELTME",
                    ]
                ),
                name="ledgerentry_hareket_tipi_gecerli",
            ),
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.CheckConstraint(
                condition=models.Q(para_birimi__regex=r"^[A-Z]{3}$"),
                name="ledgerentry_para_birimi_iso",
            ),
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(hareket_tipi="CONTRA")
                    | models.Q(contra_of__isnull=False)
                ),
                name="ledgerentry_contra_of_zorunlu",
            ),
        ),
    ]
