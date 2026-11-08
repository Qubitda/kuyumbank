"""CartLine — quote referanslı sepet satırı (F4-A7; kilit checkout’ta)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from siparis.birim_constants import SepetBirimi


class CartLine(models.Model):
    """Fiyat: PriceQuote FK (referans). Snapshot/kilit F4-040/051’de.

    Tedarikçi / maliyet alanı yok (kör havuz).
    """

    cart = models.ForeignKey(
        "siparis.Cart",
        on_delete=models.CASCADE,
        related_name="lines",
    )
    price_quote = models.ForeignKey(
        "fiyatlama.PriceQuote",
        on_delete=models.PROTECT,
        related_name="cart_lines",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="cart_lines",
    )
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    birim = models.CharField(max_length=8, choices=SepetBirimi.CHOICES)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sepet satırı"
        verbose_name_plural = "Sepet satırları"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="cartline_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="cartline_birim_gecerli",
            ),
            models.UniqueConstraint(
                fields=["cart", "varyant"],
                name="cartline_cart_varyant_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["cart", "varyant"]),
        ]

    def __str__(self) -> str:
        return (
            f"CL#{self.pk or '?'} Q#{self.price_quote_id} "
            f"{self.miktar} {self.birim}"
        )

    def clean(self):
        super().clean()
        if self.miktar is not None and self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar pozitif olmalı."})
        if not self.price_quote_id or not self.cart_id:
            return
        quote = self.price_quote
        cart = self.cart
        if quote.alici_firma_id != cart.alici_firma_id:
            raise ValidationError(
                {"price_quote": "Quote, sepet firmasına ait olmalı."}
            )
        if self.varyant_id and quote.varyant_id != self.varyant_id:
            raise ValidationError(
                {"varyant": "varyant, price_quote.varyant ile eşit olmalı."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
