"""CariHesap — firma bakiyesi projeksiyonu (F5-011; U-005 interim platform↔alıcı)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class CariHesap(models.Model):
    """Ledger projeksiyonu. Doğrudan edit yok; yalnız cari_servisi.

    bakiye > 0 → alıcı platforma borçlu (BORC − ALACAK).
    karsi_firma: interim U-005 → platform firması.
    """

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="cari_hesaplar",
        help_text="Hesap sahibi (alıcı).",
    )
    karsi_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="karsi_cari_hesaplar",
        help_text="Karşı taraf (interim: platform).",
    )
    para_birimi = models.CharField(max_length=3)
    bakiye = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    kredi_limiti = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="0 = limit kapalı (aşım kontrolü yok). >0 → max borç.",
    )
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_cari_update = False

    class Meta:
        verbose_name = "Cari hesap"
        verbose_name_plural = "Cari hesaplar"
        constraints = [
            models.UniqueConstraint(
                fields=["firma", "karsi_firma", "para_birimi"],
                name="carihesap_firma_karsi_pb_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(kredi_limiti__gte=0),
                name="carihesap_kredi_limiti_negatif_degil",
            ),
        ]
        indexes = [
            models.Index(fields=["firma", "para_birimi"]),
        ]

    def __str__(self) -> str:
        return (
            f"Cari F{self.firma_id}/{self.karsi_firma_id} "
            f"{self.bakiye} {self.para_birimi}"
        )

    def clean(self):
        super().clean()
        if self.firma_id and self.karsi_firma_id and self.firma_id == self.karsi_firma_id:
            raise ValidationError(
                {"karsi_firma": "firma ve karsi_firma aynı olamaz."}
            )
        pb = (self.para_birimi or "").strip().upper()
        if len(pb) != 3 or not pb.isalpha():
            raise ValidationError(
                {"para_birimi": "ISO 4217 para birimi zorunlu (3 harf)."}
            )
        self.para_birimi = pb

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_cari_update:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "CariHesap doğrudan güncellenemez; yalnız cari_servisi (F5-011)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("CariHesap silinemez; ledger contra kullanın.")
