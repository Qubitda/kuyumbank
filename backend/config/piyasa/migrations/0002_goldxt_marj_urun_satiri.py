from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def forwards_copy_marj(apps, schema_editor):
    PiyasaUrun = apps.get_model("piyasa", "PiyasaUrun")
    PiyasaFiyatKurali = apps.get_model("piyasa", "PiyasaFiyatKurali")
    for urun in PiyasaUrun.objects.all():
        kurallar = list(PiyasaFiyatKurali.objects.filter(urun_id=urun.pk))
        if not kurallar:
            continue
        modu = "YUZDE"
        alis = Decimal("0")
        satis = Decimal("0")
        for k in kurallar:
            tip = k.marj_tipi or "YOK"
            deger = k.marj_degeri or Decimal("0")
            if tip == "YUZDE":
                modu = "YUZDE"
                if k.taraf == "ALIS":
                    alis = abs(deger)
                elif k.taraf == "SATIS":
                    satis = abs(deger)
            elif tip in ("PB_GRAM", "PB_ADET") or tip == "YOK":
                if tip != "YOK":
                    modu = "TL"
                    if k.taraf == "ALIS":
                        alis = abs(deger)
                    elif k.taraf == "SATIS":
                        satis = abs(deger)
        PiyasaUrun.objects.filter(pk=urun.pk).update(
            marj_modu=modu, alis_marj=alis, satis_marj=satis
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("piyasa", "0001_adr0020_piyasa_panosu"),
    ]

    operations = [
        migrations.AddField(
            model_name="piyasaurun",
            name="marj_modu",
            field=models.CharField(
                choices=[("TL", "TL (tutar)"), ("YUZDE", "Yüzde (%)")],
                default="YUZDE",
                help_text="GoldXT: tüm alış/satış marjı TL veya %.",
                max_length=8,
                verbose_name="Marj modu",
            ),
        ),
        migrations.AddField(
            model_name="piyasaurun",
            name="alis_marj",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("0"),
                help_text="≥0. TL: baz−marj; %: baz×(1−marj/100).",
                max_digits=14,
                validators=[django.core.validators.MinValueValidator(Decimal("0"))],
                verbose_name="Alış marjı",
            ),
        ),
        migrations.AddField(
            model_name="piyasaurun",
            name="satis_marj",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("0"),
                help_text="≥0. TL: baz+marj; %: baz×(1+%/100).",
                max_digits=14,
                validators=[django.core.validators.MinValueValidator(Decimal("0"))],
                verbose_name="Satış marjı",
            ),
        ),
        migrations.RunPython(forwards_copy_marj, noop_reverse),
        migrations.DeleteModel(name="PiyasaFiyatKurali"),
        migrations.AlterField(
            model_name="piyasaurun",
            name="ayar",
            field=models.ForeignKey(
                blank=True,
                help_text="Tanımlar → Milyem tablosu. Boş = has (milyem 1). Seçilirse metal ayardan gelir.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="piyasa_urunleri",
                to="tanimlar.ayarmilyem",
                verbose_name="Ayar / milyem (Tanımlar)",
            ),
        ),
        migrations.AlterField(
            model_name="piyasaurun",
            name="metal",
            field=models.ForeignKey(
                help_text="Tanımlar → Kıymetli metaller. Burada yeni metal tanımlanmaz.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="piyasa_urunleri",
                to="tanimlar.kiymetlimetal",
                verbose_name="Metal (Tanımlar)",
            ),
        ),
    ]
