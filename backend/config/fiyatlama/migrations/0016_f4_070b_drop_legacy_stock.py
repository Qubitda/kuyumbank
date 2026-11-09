# F4-070b — TedarikciTeklif.stok_adet kolon drop (legacy dual-stock).
# Veri kaybı: legacy ADET sayacı silinir; truth = StockMovement/Balance.
# ACCESS EXCLUSIVE + lock_timeout (fail-fast).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fiyatlama", "0015_f5_041_contract_release"),
    ]

    operations = [
        migrations.RunSQL(
            sql="SET LOCAL lock_timeout = '2s';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(
            model_name="tedarikciteklif",
            name="stok_adet",
        ),
    ]
