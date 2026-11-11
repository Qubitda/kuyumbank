"""StockBalance — hareket projeksiyonu (ADR-0011 F4-A4). Doğrudan edit yok."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from stok.birim_constants import StokBirimi


class StockBalance(models.Model):
    warehouse = models.ForeignKey(
        "stok.Warehouse",
        on_delete=models.PROTECT,
        related_name="balances",
    )
    teklif = models.ForeignKey(
        "fiyatlama.TedarikciTeklif",
        on_delete=models.PROTECT,
        related_name="stock_balances",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="stock_balances",
    )
    birim = models.CharField(max_length=8, choices=StokBirimi.CHOICES)
    on_hand = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    reserved = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    blocked = models.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("0")
    )
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    # Servis bayrağı: yalnız ledger servisi günceller
    _allow_ledger_update = False

    class Meta:
        verbose_name = "Stok bakiyesi"
        verbose_name_plural = "Stok bakiyeleri"
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "teklif", "birim"],
                name="stockbalance_wh_teklif_birim_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="stockbalance_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(on_hand__gte=0)
                & models.Q(reserved__gte=0)
                & models.Q(blocked__gte=0),
                name="stockbalance_negatif_degil",
            ),
            # ATP: reserved + blocked asla on_hand'i aşamaz (available >= 0)
            models.CheckConstraint(
                condition=models.Q(on_hand__gte=models.F("reserved") + models.F("blocked")),
                name="stockbalance_reserved_blocked_le_on_hand",
            ),
        ]
        indexes = [
            models.Index(fields=["warehouse", "varyant"]),
            models.Index(fields=["teklif"]),
        ]

    def __str__(self) -> str:
        return (
            f"SB W{self.warehouse_id} T{self.teklif_id} "
            f"{self.on_hand} {self.birim}"
        )

    @property
    def available(self) -> Decimal:
        return self.on_hand - self.reserved - self.blocked

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_ledger_update:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "StockBalance doğrudan güncellenemez; yalnız ledger servisi "
            "(ADR-0011 F4-A4)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("StockBalance silinemez; movement ile düzeltin.")
