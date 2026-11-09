"""ReturnLine — iade satırı miktarı (F6-030/031)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from siparis.birim_constants import SepetBirimi


class ReturnLine(models.Model):
    return_request = models.ForeignKey(
        "lojistik.ReturnRequest",
        on_delete=models.PROTECT,
        related_name="lines",
    )
    order_line = models.ForeignKey(
        "siparis.OrderLine",
        on_delete=models.PROTECT,
        related_name="return_lines",
    )
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    birim = models.CharField(max_length=8, choices=SepetBirimi.CHOICES)

    class Meta:
        verbose_name = "İade satırı"
        verbose_name_plural = "İade satırları"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["return_request", "order_line"],
                name="returnline_request_orderline_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="returnline_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="returnline_birim_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"RL#{self.pk or '?'} RR#{self.return_request_id} "
            f"{self.miktar} {self.birim}"
        )

    def clean(self):
        super().clean()
        if self.miktar is not None and self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar pozitif olmalı."})
        if self.order_line_id and self.return_request_id:
            if self.order_line.order_id != self.return_request.order_id:
                raise ValidationError(
                    {"order_line": "Satır bu iade talebinin siparişine ait değil."}
                )
            if self.birim and self.birim != self.order_line.birim:
                raise ValidationError(
                    {"birim": "İade birimi sipariş satırı ile aynı olmalı."}
                )
            if self.miktar is not None and self.miktar > self.order_line.miktar:
                raise ValidationError(
                    {"miktar": "İade miktarı sipariş satırını aşamaz."}
                )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("ReturnLine değişmez.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("ReturnLine silinemez.")
