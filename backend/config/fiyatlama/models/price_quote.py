"""PriceQuote + Line — değişmez proforma snapshot (ADR-0008 Dilim 3.5).

Belge dili: proforma / fiyat teklifi (fatura değil).
B-01 platform_servis ve B-06 vergi satırı üretilmez.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PriceQuote(models.Model):
    """Alıcıya sunulan vergisiz fiyat teklifinin değişmez başlığı."""

    class BelgeTuru(models.TextChoices):
        PROFORMA = "PROFORMA", "Proforma / fiyat teklifi"

    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="price_quotes",
    )
    satis_kanali = models.ForeignKey(
        "tanimlar.SatisKanali",
        on_delete=models.PROTECT,
        related_name="price_quotes",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="price_quotes",
    )
    teklif = models.ForeignKey(
        "fiyatlama.TedarikciTeklif",
        on_delete=models.PROTECT,
        related_name="price_quotes",
    )
    teklif_versiyon = models.PositiveIntegerField()
    fiyat_modeli = models.CharField(max_length=16)

    alici_sozlesme = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesi",
        on_delete=models.PROTECT,
        related_name="alici_price_quotes",
    )
    alici_sozlesme_versiyon = models.PositiveIntegerField()
    alici_kalem = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesiKalemi",
        on_delete=models.PROTECT,
        related_name="alici_price_quotes",
    )

    tedarikci_sozlesme = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tedarikci_price_quotes",
    )
    tedarikci_sozlesme_versiyon = models.PositiveIntegerField(null=True, blank=True)
    tedarikci_kalem = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesiKalemi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tedarikci_price_quotes",
    )

    para_birimi = models.CharField(max_length=3, default="TRY")
    toplam_vergisiz = models.DecimalField(max_digits=18, decimal_places=2)
    gram = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    gecerlilik_sonu = models.DateTimeField()
    hesap_zamani = models.DateTimeField()
    quote_ttl_saniye = models.PositiveIntegerField()

    alici_kur_tipi = models.CharField(max_length=16)
    tedarikci_kur_tipi = models.CharField(max_length=16)
    metal_kuru_alici = models.ForeignKey(
        "tanimlar.MetalKuru",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="price_quotes_alici",
    )
    metal_kuru_tedarikci = models.ForeignKey(
        "tanimlar.MetalKuru",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="price_quotes_tedarikci",
    )
    doviz_gozlem_idler = models.JSONField(default=list, blank=True)
    hesap_girdisi = models.JSONField(default=dict, blank=True)

    belge_turu = models.CharField(
        max_length=16,
        choices=BelgeTuru.choices,
        default=BelgeTuru.PROFORMA,
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_price_quotes",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fiyat teklifi (proforma)"
        verbose_name_plural = "Fiyat teklifleri (proforma)"
        ordering = ["-hesap_zamani", "-pk"]
        indexes = [
            models.Index(fields=["alici_firma", "-hesap_zamani"]),
            models.Index(fields=["varyant", "-hesap_zamani"]),
            models.Index(fields=["teklif", "-hesap_zamani"]),
            models.Index(fields=["gecerlilik_sonu"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(toplam_vergisiz__gte=0),
                name="pricequote_toplam_vergisiz_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(quote_ttl_saniye__gt=0),
                name="pricequote_ttl_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(belge_turu="PROFORMA"),
                name="pricequote_belge_proforma",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"PQ#{self.pk or '?'} {self.alici_firma_id}/{self.varyant_id} "
            f"{self.toplam_vergisiz} {self.para_birimi}"
        )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "PriceQuote değişmez; UPDATE yasak (ADR-0008 §2.4)."
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "PriceQuote değişmez; DELETE yasak (ADR-0008 §2.4)."
        )


class PriceQuoteLine(models.Model):
    """Quote kalem satırı — uygulama + DB immutability."""

    class KalemTipi(models.TextChoices):
        METAL = "metal", "Metal"
        ISCILIK = "iscilik", "İşçilik"
        KANAL_MARJ = "kanal_marj", "Kanal marjı"
        TAS = "tas", "Taş"
        EK_BEDEL = "ek_bedel", "Ek bedel"
        GRAM_BIRIM = "gram_birim", "Gram × birim"
        SABIT_PARCA = "sabit_parca", "Sabit parça"
        HEDEF_TOPLAM = "hedef_toplam", "Hedef toplam (KS-6)"
        # platform_servis (B-01) ve vergi (B-06) yok

    quote = models.ForeignKey(
        PriceQuote,
        on_delete=models.CASCADE,
        related_name="satirlar",
    )
    kalem_tipi = models.CharField(max_length=16, choices=KalemTipi.choices)
    tutar = models.DecimalField(max_digits=18, decimal_places=2)
    sira = models.PositiveIntegerField(default=0)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Fiyat teklifi satırı"
        verbose_name_plural = "Fiyat teklifi satırları"
        ordering = ["quote", "sira", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tutar__gte=0),
                name="pricequoteline_tutar_negatif_degil",
            ),
            models.UniqueConstraint(
                fields=["quote", "kalem_tipi"],
                name="pricequoteline_quote_kalem_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kalem_tipi}={self.tutar}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "PriceQuoteLine değişmez; UPDATE yasak (ADR-0008 §2.4)."
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "PriceQuoteLine değişmez; DELETE yasak (ADR-0008 §2.4)."
        )
