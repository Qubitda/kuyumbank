import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("firmalar", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="kullanici",
            name="firma",
            field=models.ForeignKey(
                blank=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="kullanicilar",
                to="firmalar.firma",
                verbose_name="Firma",
            ),
        ),
        migrations.AlterField(
            model_name="kullanici",
            name="rol",
            field=models.CharField(
                choices=[
                    ("platform_ops", "Platform: Ops"),
                    ("platform_admin", "Platform: Admin"),
                    ("platform_super", "Platform: Super"),
                    ("alici_yonetici", "Alıcı: Yönetici"),
                    ("alici_satinalmaci", "Alıcı: Satın almacı"),
                    ("alici_onaylayici", "Alıcı: Sipariş onaylayıcı"),
                    ("alici_finans", "Alıcı: Finans"),
                    ("alici_denetci", "Alıcı: Salt okunur denetçi"),
                    ("tedarikci_sahip", "Tedarikçi: Sahip"),
                    ("tedarikci_yonetici", "Tedarikçi: Yönetici"),
                    ("tedarikci_satis", "Tedarikçi: Satış temsilcisi"),
                    ("tedarikci_depo", "Tedarikçi: Depo/sevkiyat"),
                    ("tedarikci_finans", "Tedarikçi: Finans"),
                ],
                max_length=30,
                verbose_name="Rol",
            ),
        ),
    ]
