# StockBalance ATP check + StockMovement tip / queryset koruması için constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stok", "0003_faz4_3_stock_reservation"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="stockbalance",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    on_hand__gte=models.F("reserved") + models.F("blocked")
                ),
                name="stockbalance_reserved_blocked_le_on_hand",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    tip__in=[
                        "GIRIS",
                        "CIKIS",
                        "DUZELTME",
                        "REZERVASYON",
                        "REZERVASYON_IPTAL",
                        "SATIS",
                        "IADE",
                    ]
                ),
                name="stockmovement_tip_gecerli",
            ),
        ),
    ]
