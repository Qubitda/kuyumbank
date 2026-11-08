"""CheckoutAttempt — sipariş adayı + idempotency (F4-040; Order F4-050)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class CheckoutAttempt(models.Model):
    class Durum(models.TextChoices):
        BASARILI = "BASARILI", "Başarılı"
        BASARISIZ = "BASARISIZ", "Başarısız"

    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="checkout_attempts",
    )
    cart = models.ForeignKey(
        "siparis.Cart",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="checkout_attempts",
    )
    idempotency_key = models.CharField(max_length=64)
    durum = models.CharField(max_length=16, choices=Durum.choices)
    sonuc = models.JSONField(
        default=dict,
        blank=True,
        help_text="Başarıda lock/rezervasyon satır özeti (kör: tedarikçi adı yok).",
    )
    hata_mesaji = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_checkout_attempts",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Checkout denemesi"
        verbose_name_plural = "Checkout denemeleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["alici_firma", "idempotency_key"],
                name="checkout_firma_idempotency_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(durum__in=["BASARILI", "BASARISIZ"]),
                name="checkout_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["alici_firma", "-olusturma_tarihi"]),
        ]

    def __str__(self) -> str:
        return f"CO#{self.pk or '?'} {self.durum} {self.idempotency_key}"
