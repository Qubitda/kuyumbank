"""ADR-0018 CAP-PIYASA — batch dry-run / atomic publish işlek."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FiyatBatchIslek(models.Model):
    class Tip(models.TextChoices):
        CANLI_SENKRON = "CANLI_SENKRON", "Canlı senkron"
        MANUEL_FREEZE = "MANUEL_FREEZE", "Manuel freeze"

    class Durum(models.TextChoices):
        DRY_RUN = "DRY_RUN", "Dry-run"
        YAYINLANDI = "YAYINLANDI", "Yayınlandı"
        IPTAL = "IPTAL", "İptal"

    tip = models.CharField(max_length=16, choices=Tip.choices)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.DRY_RUN
    )
    filtre = models.JSONField(default=dict, blank=True)
    ozet = models.JSONField(default=dict, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fiyat_batch_islekleri",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    yayin_tarihi = models.DateTimeField(null=True, blank=True)

    _allow_transition = False

    class Meta:
        verbose_name = "Fiyat batch işlek"
        verbose_name_plural = "Fiyat batch işlekleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    tip__in=["CANLI_SENKRON", "MANUEL_FREEZE"]
                ),
                name="fiyatbatch_tip_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["DRY_RUN", "YAYINLANDI", "IPTAL"]
                ),
                name="fiyatbatch_durum_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"FB#{self.pk or '?'} {self.tip} {self.durum}"

    def save(self, *args, **kwargs):
        if self._state.adding or self._allow_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "FiyatBatchIslek yalnız fiyat_batch_servisi ile güncellenir."
        )


class FiyatBatchSatir(models.Model):
    class Sonuc(models.TextChoices):
        ADAY = "ADAY", "Aday"
        SOK = "SOK", "Şok eşiği"
        BLOKE = "BLOKE", "Guardrail bloke"
        UYGULANDI = "UYGULANDI", "Uygulandı"
        AT = "ATLANDI", "Atlandı"

    islek = models.ForeignKey(
        FiyatBatchIslek, on_delete=models.CASCADE, related_name="satirlar"
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="fiyat_batch_satirlari",
    )
    onceki_sabit_fiyat = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    yeni_sabit_fiyat = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    delta_yuzde = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    sonuc = models.CharField(
        max_length=16, choices=Sonuc.choices, default=Sonuc.ADAY
    )
    neden = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Fiyat batch satır"
        verbose_name_plural = "Fiyat batch satırları"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["islek", "varyant"],
                name="fiyatbatchsatir_islek_varyant_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"FBS#{self.pk or '?'} V#{self.varyant_id} {self.sonuc}"

    def save(self, *args, **kwargs):
        if not self._state.adding and not getattr(
            self, "_allow_update", False
        ):
            raise ValidationError("FiyatBatchSatir değişmez (publish hariç).")
        if self._state.adding:
            self.full_clean()
        return super().save(*args, **kwargs)
