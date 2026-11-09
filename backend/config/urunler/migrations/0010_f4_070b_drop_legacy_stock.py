# F4-070b — Varyant.stok kolon drop (legacy dual-stock).
# Veri kaybı: legacy ADET sayacı silinir; truth = StockMovement/Balance.
# ACCESS EXCLUSIVE + lock_timeout (fail-fast).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("urunler", "0009_f4_070_legacy_stock_readonly"),
    ]

    operations = [
        migrations.RunSQL(
            sql="SET LOCAL lock_timeout = '2s';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveConstraint(
            model_name="varyant",
            name="varyant_benzersiz_parca_stok",
        ),
        migrations.RemoveField(
            model_name="varyant",
            name="stok",
        ),
    ]
