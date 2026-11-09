"""Cart — alıcı firmaya özel sepet başlığı (ADR-0011 F4-A7)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Cart(models.Model):
    """Firma başına tek sepet. Stok düşürmez; checkout’ta lock+rezervasyon (F4-040)."""

    alici_firma = models.OneToOneField(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="cart",
        help_text="Tenant sınırı (ADR-0003). Org scope: sube (ADR-0015 OH-3).",
    )
    sube = models.ForeignKey(
        "firmalar.OrgBirimi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="carts",
        help_text="Opsiyonel org/şube; tenant değil.",
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_carts",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sepet"
        verbose_name_plural = "Sepetler"
        ordering = ["-guncelleme_tarihi", "-pk"]

    def __str__(self) -> str:
        return f"Cart#{self.pk or '?'} firma={self.alici_firma_id}"

    def clean(self):
        super().clean()
        firma = getattr(self, "alici_firma", None)
        if firma is not None and not getattr(firma, "alici_mi", False):
            raise ValidationError(
                {"alici_firma": "Sepet yalnız alıcı firmaya ait olabilir."}
            )
        if self.sube_id and firma is not None and self.sube.firma_id != firma.pk:
            raise ValidationError(
                {"sube": "Org birimi sepet firmasına ait değil (OH-4)."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
