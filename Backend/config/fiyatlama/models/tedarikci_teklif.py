from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TedarikciTeklif(models.Model):
    class FiyatModeli(models.TextChoices):
        METAL_BAZLI = "METAL_BAZLI", "Metal bazlı (gram × milyem × birim)"
        GRAM_BIRIM = "GRAM_BIRIM", "Gram × birim fiyat"
        SABIT_PARCA = "SABIT_PARCA", "Parça başı sabit tutar"

    class TeminTipi(models.TextChoices):
        HAZIR = "HAZIR", "Hazır"
        SIPARISE_OZEL = "SIPARISE_OZEL", "Siparişe özel"
        BENZERSIZ = "BENZERSIZ", "Benzersiz (tek parça)"

    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        ONAY_BEKLIYOR = "ONAY_BEKLIYOR", "Onay bekliyor"
        YAYINDA = "YAYINDA", "Yayında"
        PASIF = "PASIF", "Pasif"

    class EslestirmeDurumu(models.TextChoices):
        ONERILDI = "onerildi", "Önerildi"
        ONAYLANDI = "onaylandi", "Onaylandı"
        REDDEDILDI = "reddedildi", "Reddedildi"
        AYRILDI = "ayrildi", "Ayrıldı"

    class EslestirmeGuveni(models.TextChoices):
        KESIN = "kesin", "Kesin"
        MANUEL = "manuel", "Manuel"
        CIKARIM = "cikarim", "Çıkarım"

    class EsdegerlikSeviyesi(models.TextChoices):
        BIREBIR = "birebir", "Birebir"
        ESDEGER = "esdeger", "Eşdeğer"

    varyant = models.ForeignKey(
        "urunler.Varyant",          # ← DÜZELTİLDİ: UrunVaryant → Varyant
        on_delete=models.CASCADE,
        related_name="teklifler",
    )
    tedarikci = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="teklifler",
    )
    tedarikci_kodu = models.CharField(max_length=64, blank=True)
    fiyat_modeli = models.CharField(max_length=16, choices=FiyatModeli.choices)
    gram = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    gram_tolerans = models.DecimalField(
        max_digits=6, decimal_places=4, default=Decimal("0.05")
    )
    birim_fiyat = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    para_birimi = models.CharField(max_length=3, default="TRY")
    iscilik_override = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    temin_tipi = models.CharField(
        max_length=16, choices=TeminTipi.choices, default=TeminTipi.HAZIR
    )
    stok_adet = models.PositiveIntegerField(default=0)
    uretim_suresi_gun = models.PositiveIntegerField(null=True, blank=True)
    oncelik = models.PositiveIntegerField(default=0)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    onaylayan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="onayladigi_teklifler",
    )
    onay_zamani = models.DateTimeField(null=True, blank=True)
    eslestirme_durumu = models.CharField(
        max_length=16,
        choices=EslestirmeDurumu.choices,
        blank=True,
        default="",
    )
    eslestirme_guveni = models.CharField(
        max_length=16,
        choices=EslestirmeGuveni.choices,
        blank=True,
        default="",
    )
    eslestiren_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eslestirdigi_teklifler",
    )
    eslestirme_kaniti = models.JSONField(default=dict, blank=True)
    esdegerlik_seviyesi = models.CharField(
        max_length=16,
        choices=EsdegerlikSeviyesi.choices,
        blank=True,
        default="",
    )
    hedef_urun = models.ForeignKey(
        "urunler.Urun",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eslestirme_teklifleri",
        help_text="Eşleştirme önerisinin hedef katalog ürünü (ADR-0005).",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tedarikçi Teklifi"
        verbose_name_plural = "Tedarikçi Teklifleri"
        ordering = ["oncelik", "-olusturma_tarihi"]
        permissions = [
            ("manage_own_teklif", "Kendi tedarikçi tekliflerini yönetebilir"),
            ("approve_teklif", "Tedarikçi teklifini onaylayabilir"),
            ("approve_eslestirme", "Teklif-katalog eşleştirmesini onaylayabilir"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tedarikci", "tedarikci_kodu"],
                condition=~models.Q(tedarikci_kodu=""),
                name="teklif_tedarikci_kod_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(fiyat_modeli="METAL_BAZLI", gram__isnull=False)
                    | models.Q(
                        fiyat_modeli="GRAM_BIRIM",
                        gram__isnull=False,
                        birim_fiyat__isnull=False,
                    )
                    | models.Q(fiyat_modeli="SABIT_PARCA", birim_fiyat__isnull=False)
                ),
                name="teklif_fiyat_modeli_alanlari_dolu",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tedarikci} — {self.varyant.sku} ({self.fiyat_modeli})"

    def clean(self):
        super().clean()
        if self.fiyat_modeli == self.FiyatModeli.METAL_BAZLI and self.gram is None:
            raise ValidationError({"gram": "METAL_BAZLI teklifte gram zorunlu."})
        if self.fiyat_modeli == self.FiyatModeli.GRAM_BIRIM:
            if self.gram is None or self.birim_fiyat is None:
                raise ValidationError(
                    "GRAM_BIRIM teklifte gram ve birim fiyat zorunlu."
                )
        if (
            self.fiyat_modeli == self.FiyatModeli.SABIT_PARCA
            and self.birim_fiyat is None
        ):
            raise ValidationError(
                {"birim_fiyat": "SABIT_PARCA teklifte birim fiyat zorunlu."}
            )