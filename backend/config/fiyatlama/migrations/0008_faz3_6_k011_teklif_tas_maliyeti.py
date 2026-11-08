# Dilim 3.6 K-011: fiyatlama.UrunTasi → TeklifTasMaliyeti (RenameModel)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fiyatlama", "0007_faz3_5_price_quote"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="UrunTasi",
            new_name="TeklifTasMaliyeti",
        ),
        migrations.AlterModelOptions(
            name="tekliftasmaliyeti",
            options={
                "ordering": ["teklif", "id"],
                "verbose_name": "Teklif taş maliyeti",
                "verbose_name_plural": "Teklif taş maliyetleri",
            },
        ),
    ]
