"""ADR-0005: TedarikciTeklif eşleştirme alanları."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("fiyatlama", "0002_faz1_kimlik_rbac"),
    ]

    operations = [
        migrations.AddField(
            model_name="tedarikciteklif",
            name="eslestirme_durumu",
            field=models.CharField(
                blank=True,
                choices=[
                    ("onerildi", "Önerildi"),
                    ("onaylandi", "Onaylandı"),
                    ("reddedildi", "Reddedildi"),
                    ("ayrildi", "Ayrıldı"),
                ],
                default="",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="tedarikciteklif",
            name="eslestirme_guveni",
            field=models.CharField(
                blank=True,
                choices=[
                    ("kesin", "Kesin"),
                    ("manuel", "Manuel"),
                    ("cikarim", "Çıkarım"),
                ],
                default="",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="tedarikciteklif",
            name="eslestiren_kullanici",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="eslestirdigi_teklifler",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="tedarikciteklif",
            name="eslestirme_kaniti",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="tedarikciteklif",
            name="esdegerlik_seviyesi",
            field=models.CharField(
                blank=True,
                choices=[
                    ("birebir", "Birebir"),
                    ("esdeger", "Eşdeğer"),
                ],
                default="",
                max_length=16,
            ),
        ),
    ]
