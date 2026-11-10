"""F10-021 — Katalog dışı RFQ satırı ↔ platform katalog varyant eşleştirme."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class RFQEslestirme(models.Model):
    """Platform aracılı eşleştirme önerisi (kör havuz; tedarikçi kimliği yok)."""

    class Durum(models.TextChoices):
        ONERILDI = "ONERILDI", "Önerildi"
        ONAYLANDI = "ONAYLANDI", "Onaylandı"
        REDDEDILDI = "REDDEDILDI", "Reddedildi"

    rfq_line = models.ForeignKey(
        "siparis.RFQLine",
        on_delete=models.CASCADE,
        related_name="eslestirmeler",
    )
    onerilen_varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="rfq_eslestirmeleri",
    )
    durum = models.CharField(
        max_length=16,
        choices=Durum.choices,
        default=Durum.ONERILDI,
    )
    skor = models.PositiveSmallIntegerField(default=0)
    kanit = models.JSONField(default=dict, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rfq_eslestirmeleri",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "RFQ eşleştirme"
        verbose_name_plural = "RFQ eşleştirmeleri"
        ordering = ["-skor", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["ONERILDI", "ONAYLANDI", "REDDEDILDI"]
                ),
                name="rfqeslestirme_durum_gecerli",
            ),
            models.UniqueConstraint(
                fields=["rfq_line", "onerilen_varyant"],
                condition=models.Q(durum="ONERILDI"),
                name="rfqeslestirme_line_varyant_onerildi_uniq",
            ),
            models.UniqueConstraint(
                fields=["rfq_line"],
                condition=models.Q(durum="ONAYLANDI"),
                name="rfqeslestirme_line_onaylandi_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["rfq_line", "durum"]),
            models.Index(fields=["durum", "olusturma_tarihi"]),
        ]

    def __str__(self) -> str:
        return (
            f"RFQE#{self.pk or '?'} L#{self.rfq_line_id} "
            f"V#{self.onerilen_varyant_id} {self.durum}"
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "RFQEslestirme değişmez; geçiş yalnız rfq_eslestirme_servisi (F10-021)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("RFQEslestirme silinemez.")
