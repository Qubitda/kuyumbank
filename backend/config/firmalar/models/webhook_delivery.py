"""WebhookDelivery — outbox delivery kaydı (F7-020; idempotent)."""

from __future__ import annotations

from django.db import models


class WebhookDelivery(models.Model):
    class Durum(models.TextChoices):
        PENDING = "PENDING", "Bekliyor"
        DELIVERED = "DELIVERED", "Teslim"
        FAILED = "FAILED", "Başarısız"

    outbox = models.ForeignKey(
        "firmalar.OutboxMessage",
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    endpoint_key = models.CharField(
        max_length=64,
        help_text="Hedef anahtar (fake/erp/crm); URL/secret yok.",
    )
    idempotency_key = models.CharField(max_length=128)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=255, blank=True)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Webhook delivery"
        verbose_name_plural = "Webhook deliveries"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["outbox", "endpoint_key", "idempotency_key"],
                name="webhook_delivery_idempotent_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["PENDING", "DELIVERED", "FAILED"]
                ),
                name="webhook_delivery_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["durum", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"WD#{self.pk or '?'} {self.endpoint_key} {self.durum}"
