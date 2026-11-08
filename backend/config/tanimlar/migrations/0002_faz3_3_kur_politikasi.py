# Dilim 3.3 — Kur politikası (ADR-0008 B-03/B-04/B-05, K-019)

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def seed_provider_and_backfill(apps, schema_editor):
    KurSaglayici = apps.get_model("tanimlar", "KurSaglayici")
    KurPolitikasi = apps.get_model("tanimlar", "KurPolitikasi")
    MetalKuru = apps.get_model("tanimlar", "MetalKuru")
    DovizKuru = apps.get_model("tanimlar", "DovizKuru")

    provider, _ = KurSaglayici.objects.get_or_create(
        kod="MANUEL",
        defaults={
            "ad": "Manuel platform girişi",
            "aktif": True,
            "max_gecikme_saniye": 300,
        },
    )
    if not KurSaglayici.objects.filter(aktif=True).exists():
        KurSaglayici.objects.filter(pk=provider.pk).update(aktif=True)

    KurPolitikasi.objects.get_or_create(
        anahtar="default",
        defaults={
            "alici_kur_tipi": "satis",
            "tedarikci_kur_tipi": "alis",
        },
    )

    # Eski satırlar: saglayici/alinma/kur_tipi doldur
    for row in MetalKuru.objects.filter(saglayici_id__isnull=True).iterator():
        MetalKuru.objects.filter(pk=row.pk).update(
            saglayici_id=provider.pk,
            kur_tipi=row.kur_tipi or "satis",
            alinma_zamani=row.girilme_zamani or row.zaman,
        )
    for row in DovizKuru.objects.filter(saglayici_id__isnull=True).iterator():
        DovizKuru.objects.filter(pk=row.pk).update(
            saglayici_id=provider.pk,
            kur_tipi=row.kur_tipi or "satis",
            alinma_zamani=row.girilme_zamani or row.zaman,
        )


def noop_reverse(apps, schema_editor):
    # Sağlayıcı/politika satırları geri alınmaz (veri kaybı riski yok; FK PROTECT).
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tanimlar", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="KurSaglayici",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("kod", models.CharField(max_length=32, unique=True, verbose_name="Kod")),
                ("ad", models.CharField(max_length=80, verbose_name="Ad")),
                ("aktif", models.BooleanField(default=False, verbose_name="Aktif")),
                (
                    "max_gecikme_saniye",
                    models.PositiveIntegerField(
                        help_text="Piyasa zamanı ile alınma/now arasındaki üst sınır; aşılırsa gözlem stale.",
                        verbose_name="Maksimum gecikme (sn)",
                    ),
                ),
                ("olusturma", models.DateTimeField(auto_now_add=True)),
                ("guncelleme", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Kur sağlayıcı",
                "verbose_name_plural": "Kur sağlayıcıları",
                "ordering": ["kod"],
                "permissions": [("manage_kur", "Kur politikası yönetebilir")],
            },
        ),
        migrations.CreateModel(
            name="KurPolitikasi",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "anahtar",
                    models.CharField(
                        default="default",
                        max_length=16,
                        unique=True,
                        verbose_name="Anahtar",
                    ),
                ),
                (
                    "alici_kur_tipi",
                    models.CharField(
                        choices=[
                            ("alis", "Alış"),
                            ("satis", "Satış"),
                            ("efektif", "Efektif"),
                            ("platform", "Platform"),
                        ],
                        default="satis",
                        max_length=16,
                        verbose_name="Alıcı kur tipi",
                    ),
                ),
                (
                    "tedarikci_kur_tipi",
                    models.CharField(
                        choices=[
                            ("alis", "Alış"),
                            ("satis", "Satış"),
                            ("efektif", "Efektif"),
                            ("platform", "Platform"),
                        ],
                        default="alis",
                        max_length=16,
                        verbose_name="Tedarikçi kur tipi",
                    ),
                ),
                ("guncelleme", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Kur politikası",
                "verbose_name_plural": "Kur politikası",
            },
        ),
        migrations.AddConstraint(
            model_name="kursaglayici",
            constraint=models.CheckConstraint(
                condition=models.Q(("max_gecikme_saniye__gt", 0)),
                name="kur_saglayici_max_gecikme_pozitif",
            ),
        ),
        migrations.AddConstraint(
            model_name="kursaglayici",
            constraint=models.UniqueConstraint(
                condition=models.Q(("aktif", True)),
                fields=("aktif",),
                name="tek_aktif_kur_saglayici",
            ),
        ),
        migrations.AddField(
            model_name="satiskanali",
            name="quote_ttl_saniye",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="ADR-0008 B-03: kanal bazlı quote geçerliliği. Boşsa quote üretilmez (3.5).",
                null=True,
                verbose_name="Quote TTL (sn)",
            ),
        ),
        migrations.AddConstraint(
            model_name="satiskanali",
            constraint=models.CheckConstraint(
                condition=models.Q(("quote_ttl_saniye__isnull", True))
                | models.Q(("quote_ttl_saniye__gt", 0)),
                name="satis_kanali_quote_ttl_pozitif",
            ),
        ),
        # --- MetalKuru genişletme (önce nullable) ---
        migrations.AddField(
            model_name="metalkuru",
            name="saglayici",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="metal_kurlar",
                to="tanimlar.kursaglayici",
                verbose_name="Sağlayıcı",
            ),
        ),
        migrations.AddField(
            model_name="metalkuru",
            name="kur_tipi",
            field=models.CharField(
                choices=[
                    ("alis", "Alış"),
                    ("satis", "Satış"),
                    ("efektif", "Efektif"),
                    ("platform", "Platform"),
                ],
                default="satis",
                max_length=16,
                verbose_name="Kur tipi",
            ),
        ),
        migrations.AddField(
            model_name="metalkuru",
            name="alinma_zamani",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Alınma zamanı"
            ),
        ),
        migrations.AddField(
            model_name="metalkuru",
            name="manuel_neden",
            field=models.TextField(blank=True, default="", verbose_name="Manuel neden"),
        ),
        migrations.AddField(
            model_name="metalkuru",
            name="onaylayan_kullanici",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Onaylayan kullanıcı",
            ),
        ),
        migrations.AddField(
            model_name="metalkuru",
            name="onay_zamani",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Onay zamanı"
            ),
        ),
        migrations.AlterField(
            model_name="metalkuru",
            name="giren_kullanici",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Giren kullanıcı",
            ),
        ),
        migrations.AlterField(
            model_name="metalkuru",
            name="zaman",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Piyasa zamanı"
            ),
        ),
        # --- DovizKuru genişletme ---
        migrations.AddField(
            model_name="dovizkuru",
            name="saglayici",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="doviz_kurlar",
                to="tanimlar.kursaglayici",
                verbose_name="Sağlayıcı",
            ),
        ),
        migrations.AddField(
            model_name="dovizkuru",
            name="kur_tipi",
            field=models.CharField(
                choices=[
                    ("alis", "Alış"),
                    ("satis", "Satış"),
                    ("efektif", "Efektif"),
                    ("platform", "Platform"),
                ],
                default="satis",
                max_length=16,
                verbose_name="Kur tipi",
            ),
        ),
        migrations.AddField(
            model_name="dovizkuru",
            name="alinma_zamani",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Alınma zamanı"
            ),
        ),
        migrations.AddField(
            model_name="dovizkuru",
            name="manuel_neden",
            field=models.TextField(blank=True, default="", verbose_name="Manuel neden"),
        ),
        migrations.AddField(
            model_name="dovizkuru",
            name="onaylayan_kullanici",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Onaylayan kullanıcı",
            ),
        ),
        migrations.AddField(
            model_name="dovizkuru",
            name="onay_zamani",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Onay zamanı"
            ),
        ),
        migrations.AlterField(
            model_name="dovizkuru",
            name="giren_kullanici",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Giren kullanıcı",
            ),
        ),
        migrations.AlterField(
            model_name="dovizkuru",
            name="zaman",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Piyasa zamanı"
            ),
        ),
        migrations.RunPython(seed_provider_and_backfill, noop_reverse),
        migrations.AlterField(
            model_name="metalkuru",
            name="saglayici",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="metal_kurlar",
                to="tanimlar.kursaglayici",
                verbose_name="Sağlayıcı",
            ),
        ),
        migrations.AlterField(
            model_name="dovizkuru",
            name="saglayici",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="doviz_kurlar",
                to="tanimlar.kursaglayici",
                verbose_name="Sağlayıcı",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="metalkuru",
            name="benzersiz_metal_zaman",
        ),
        migrations.RemoveConstraint(
            model_name="dovizkuru",
            name="benzersiz_doviz_zaman",
        ),
        migrations.AddConstraint(
            model_name="metalkuru",
            constraint=models.UniqueConstraint(
                fields=("metal", "kur_tipi", "zaman"),
                name="benzersiz_metal_kur_tipi_zaman",
            ),
        ),
        migrations.AddConstraint(
            model_name="dovizkuru",
            constraint=models.UniqueConstraint(
                fields=("para_birimi", "kur_tipi", "zaman"),
                name="benzersiz_doviz_kur_tipi_zaman",
            ),
        ),
        migrations.RemoveIndex(
            model_name="metalkuru",
            name="tanimlar_me_metal_i_aab7f5_idx",
        ),
        migrations.RemoveIndex(
            model_name="dovizkuru",
            name="tanimlar_do_para_bi_4f1af9_idx",
        ),
        migrations.AddIndex(
            model_name="metalkuru",
            index=models.Index(
                fields=["metal", "kur_tipi", "-zaman"],
                name="tanimlar_me_metal_i_kur_tip_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="metalkuru",
            index=models.Index(
                fields=["saglayici", "metal", "-zaman"],
                name="tanimlar_me_saglayi_metal_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="dovizkuru",
            index=models.Index(
                fields=["para_birimi", "kur_tipi", "-zaman"],
                name="tanimlar_do_para_kur_tip_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="dovizkuru",
            index=models.Index(
                fields=["saglayici", "para_birimi", "-zaman"],
                name="tanimlar_do_saglayi_para_idx",
            ),
        ),
    ]
