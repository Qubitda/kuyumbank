"""ADR-0005: Urun.tedarikci → olusturan_firma; kimlik alanları; gram bandı.

Faz 2.0: RemoveField öncesi tedarikci / tedarikci_urun_kodu → TedarikciTeklif taslağı.
"""

import django.db.models.deletion
from django.db import migrations, models


def _teklif_defaults_for_varyant(varyant):
    """Taslak teklif için fiyat_modeli kısıtını sağlayan alanlar."""
    if varyant.gram is not None:
        return {
            "fiyat_modeli": "METAL_BAZLI",
            "gram": varyant.gram,
            "birim_fiyat": None,
        }
    if varyant.sabit_fiyat is not None:
        return {
            "fiyat_modeli": "SABIT_PARCA",
            "gram": None,
            "birim_fiyat": varyant.sabit_fiyat,
        }
    return None


def copy_tedarikci_to_olusturan_and_teklif(apps, schema_editor):
    Urun = apps.get_model("urunler", "Urun")
    Varyant = apps.get_model("urunler", "Varyant")
    TedarikciTeklif = apps.get_model("fiyatlama", "TedarikciTeklif")

    blocked = []
    for urun in Urun.objects.all().iterator():
        tedarikci_id = getattr(urun, "tedarikci_id", None)
        if tedarikci_id and not urun.olusturan_firma_id:
            Urun.objects.filter(pk=urun.pk).update(olusturan_firma_id=tedarikci_id)

        urun.refresh_from_db()
        if not urun.olusturan_firma_id and not tedarikci_id:
            blocked.append(f"Urun pk={urun.pk}: tedarikci/olusturan_firma yok")
            continue

        firma_id = urun.olusturan_firma_id or tedarikci_id
        kod = (getattr(urun, "tedarikci_urun_kodu", None) or "").strip()
        varyantlar = list(Varyant.objects.filter(urun_id=urun.pk))
        if not varyantlar:
            if kod or tedarikci_id:
                blocked.append(
                    f"Urun pk={urun.pk} platform_kodu={urun.platform_kodu!r}: "
                    "varyant yok; TedarikciTeklif taslağı oluşturulamaz"
                )
            continue

        for varyant in varyantlar:
            defaults = _teklif_defaults_for_varyant(varyant)
            if defaults is None:
                blocked.append(
                    f"Varyant pk={varyant.pk} (urun={urun.pk}): gram/sabit_fiyat yok; "
                    "teklif taslağı fiyat kısıtı sağlanamıyor"
                )
                continue
            teklif_kod = kod or (getattr(varyant, "tedarikci_sku", None) or "")
            existing = TedarikciTeklif.objects.filter(
                varyant_id=varyant.pk, tedarikci_id=firma_id
            ).first()
            if existing:
                if teklif_kod and not (existing.tedarikci_kodu or "").strip():
                    TedarikciTeklif.objects.filter(pk=existing.pk).update(
                        tedarikci_kodu=teklif_kod
                    )
                continue
            TedarikciTeklif.objects.create(
                varyant_id=varyant.pk,
                tedarikci_id=firma_id,
                tedarikci_kodu=teklif_kod,
                durum="TASLAK",
                stok_adet=0,
                **defaults,
            )

    if blocked:
        detail = "; ".join(blocked[:20])
        more = f" (+{len(blocked) - 20} daha)" if len(blocked) > 20 else ""
        raise RuntimeError(
            "urunler.0005 veri taşıma durdu — taşınamayan satırlar var. "
            f"{detail}{more}. "
            "Varyant/gram eksiklerini düzeltip migration'ı yeniden deneyin."
        )


def reverse_olusturan_and_teklif(apps, schema_editor):
    """Geri alma: olusturan_firma → tedarikci alanları henüz şemada yoksa no-op aşaması.

    NOT (veri kaybı): Bu reverse, RemoveField *sonrası* çalışmaz (tedarikci kolonları
    yok). RemoveField öncesi reverse için: olusturan_firma_id ve ilk taslak
    teklif.tedarikci_kodu bilgisi yedekten / tekliften elle geri yazılmalıdır.
    Otomatik reverse RemoveField sonrası tedarikci_urun_kodu'yu tüm varyant
    tekliflerinden tek ürüne güvenli birleştirmez — bilinçli veri kaybı riski.
    """
    # RemoveField'dan önceki state'te reverse RunPython çağrılırken alanlar vardır.
    Urun = apps.get_model("urunler", "Urun")
    TedarikciTeklif = apps.get_model("fiyatlama", "TedarikciTeklif")
    # Historical state during reverse of this RunPython: tedarikci still exists
    # (RemoveField is later). Restore tedarikci from olusturan_firma.
    for urun in Urun.objects.all().iterator():
        updates = {}
        if urun.olusturan_firma_id and not getattr(urun, "tedarikci_id", None):
            updates["tedarikci_id"] = urun.olusturan_firma_id
        teklif = (
            TedarikciTeklif.objects.filter(
                varyant__urun_id=urun.pk, tedarikci_id=urun.olusturan_firma_id
            )
            .exclude(tedarikci_kodu="")
            .order_by("pk")
            .first()
        )
        if teklif and not (getattr(urun, "tedarikci_urun_kodu", None) or "").strip():
            updates["tedarikci_urun_kodu"] = teklif.tedarikci_kodu
        if updates:
            Urun.objects.filter(pk=urun.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("firmalar", "0004_faz1_firma_not_null"),
        ("fiyatlama", "0003_faz2_eslestirme_alanlari"),
        ("urunler", "0004_faz1_kimlik_rbac"),
    ]

    operations = [
        migrations.AddField(
            model_name="urun",
            name="olusturan_firma",
            field=models.ForeignKey(
                help_text="Denetim alanı. Alıcıya hiçbir yüzeyde gösterilmez (ADR-0005 K6).",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="olusturdugu_katalog_urunleri",
                to="firmalar.firma",
                verbose_name="Oluşturan firma",
            ),
        ),
        migrations.AddField(
            model_name="urun",
            name="kimlik_sinifi",
            field=models.CharField(
                choices=[
                    ("A", "Seri / sertifikalı"),
                    ("B", "Markalı / model kodlu"),
                    ("C", "Jenerik kalıp"),
                ],
                default="C",
                max_length=1,
                verbose_name="Kimlik sınıfı",
            ),
        ),
        migrations.AddField(
            model_name="urun",
            name="kimlik_anahtari",
            field=models.CharField(
                blank=True,
                default="",
                help_text="A/B: sertifika/parça veya marka+model(+GTIN). C: platform spec anahtarı.",
                max_length=255,
                verbose_name="Kimlik anahtarı",
            ),
        ),
        migrations.AddField(
            model_name="varyant",
            name="gram_bandi_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                help_text="Boşsa settings VARYANT_GRAM_BANDI_ORAN ile hesaplanır (ADR-0005 K3).",
                max_digits=10,
                null=True,
                verbose_name="Gram bandı min",
            ),
        ),
        migrations.AddField(
            model_name="varyant",
            name="gram_bandi_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=10,
                null=True,
                verbose_name="Gram bandı max",
            ),
        ),
        # Reverse için: önce nullable yap → RunPython geri yazar → sonra RemoveField
        migrations.AlterField(
            model_name="urun",
            name="tedarikci",
            field=models.ForeignKey(
                help_text="Müşteriye hiçbir ekranda gösterilmez.",
                limit_choices_to={"tedarikci_mi": True},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="urunler",
                to="firmalar.firma",
                verbose_name="Tedarikçi",
            ),
        ),
        migrations.RunPython(
            copy_tedarikci_to_olusturan_and_teklif,
            reverse_olusturan_and_teklif,
        ),
        migrations.RemoveIndex(
            model_name="urun",
            name="urunler_uru_tedarik_142c09_idx",
        ),
        migrations.RemoveField(
            model_name="urun",
            name="tedarikci",
        ),
        migrations.RemoveField(
            model_name="urun",
            name="tedarikci_urun_kodu",
        ),
        migrations.AlterField(
            model_name="urun",
            name="olusturan_firma",
            field=models.ForeignKey(
                help_text="Denetim alanı. Alıcıya hiçbir yüzeyde gösterilmez (ADR-0005 K6).",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="olusturdugu_katalog_urunleri",
                to="firmalar.firma",
                verbose_name="Oluşturan firma",
            ),
        ),
        migrations.AddIndex(
            model_name="urun",
            index=models.Index(
                fields=["olusturan_firma", "onay_durumu"],
                name="urunler_uru_olustur_7a2b1c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="urun",
            index=models.Index(
                fields=["kimlik_sinifi", "kimlik_anahtari"],
                name="urunler_uru_kimlik__9c4d2e_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="urun",
            constraint=models.UniqueConstraint(
                condition=models.Q(kimlik_sinifi__in=["A", "B"])
                & ~models.Q(kimlik_anahtari=""),
                fields=("kimlik_sinifi", "kimlik_anahtari"),
                name="urun_kimlik_ab_anahtar_uniq",
            ),
        ),
    ]
