from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("firmalar", "0003_faz1_backfill_platform"),
    ]

    operations = [
        migrations.AlterField(
            model_name="firma",
            name="firma_kodu",
            field=models.CharField(
                help_text="Değişmez iş anahtarı. Platform için PLATFORM.",
                max_length=32,
                unique=True,
                verbose_name="Firma kodu",
            ),
        ),
        migrations.AlterField(
            model_name="kullanici",
            name="firma",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="kullanicilar",
                to="firmalar.firma",
                verbose_name="Firma",
            ),
        ),
    ]
