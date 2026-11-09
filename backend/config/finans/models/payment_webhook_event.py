"""PaymentWebhookEvent — sağlayıcı webhook kaydı (F5-021); tekrarlayan event tek sonuç."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PaymentWebhookEvent(models.Model):
    class Sonuc(models.TextChoices):
        ISLENDI = "ISLENDI", "İşlendi"
        TEKRAR = "TEKRAR", "Tekrar (idempotent)"
        YOK_SAYILDI = "YOK_SAYILDI", "Yok sayıldı"
        HATA = "HATA", "Hata"

    provider = models.CharField(max_length=32, default="fake")
    event_id = models.CharField(max_length=128)
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    payment_intent = models.ForeignKey(
        "finans.PaymentIntent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="webhook_events",
    )
    sonuc = models.CharField(max_length=16, choices=Sonuc.choices)
    detail = models.CharField(max_length=255, blank=True)
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Ödeme webhook olayı"
        verbose_name_plural = "Ödeme webhook olayları"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"],
                name="paymentwebhook_provider_event_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "event_id"]),
        ]

    def __str__(self) -> str:
        return f"WH#{self.pk or '?'} {self.provider}:{self.event_id} {self.sonuc}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "PaymentWebhookEvent değişmez; UPDATE yasak (F5-021)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("PaymentWebhookEvent silinemez (F5-021).")
