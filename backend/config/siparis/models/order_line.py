"""OrderLine — fiyat snapshot + PriceLock bağ (ADR-0010 L-11 / F4-A10)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from siparis.birim_constants import SepetBirimi


class OrderLine(models.Model):
    """Kur değişimi satır tutarını etkilemez — snapshot alanları sabit."""

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="lines",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    price_lock = models.OneToOneField(
        "fiyatlama.PriceLock",
        on_delete=models.PROTECT,
        related_name="order_line",
        help_text="L-11: sipariş satırı kilide bağlanır.",
    )
    stock_reservation = models.OneToOneField(
        "stok.StockReservation",
        on_delete=models.PROTECT,
        related_name="order_line",
    )
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    birim = models.CharField(max_length=8, choices=SepetBirimi.CHOICES)
    # Snapshot — lock.toplam_vergisiz kopyası (birim fiyat referansı)
    snapshot_birim_fiyat_vergisiz = models.DecimalField(
        max_digits=18, decimal_places=2
    )
    snapshot_satir_tutari_vergisiz = models.DecimalField(
        max_digits=18, decimal_places=2
    )
    para_birimi = models.CharField(max_length=3)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sipariş satırı"
        verbose_name_plural = "Sipariş satırları"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="orderline_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="orderline_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(snapshot_birim_fiyat_vergisiz__gte=0),
                name="orderline_birim_fiyat_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(snapshot_satir_tutari_vergisiz__gte=0),
                name="orderline_satir_tutar_negatif_degil",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"OL#{self.pk or '?'} O#{self.order_id} "
            f"{self.miktar} {self.birim}"
        )

    def clean(self):
        super().clean()
        if self.miktar is not None and self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar pozitif olmalı."})
        if self.price_lock_id and self.order_id:
            if self.price_lock.alici_firma_id != self.order.alici_firma_id:
                raise ValidationError(
                    {"price_lock": "Lock, sipariş firmasına ait olmalı."}
                )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "OrderLine değişmez; snapshot sonradan güncellenemez (L-11)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("OrderLine silinemez.")
