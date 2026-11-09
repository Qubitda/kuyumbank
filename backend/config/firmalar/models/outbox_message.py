"""Transactional outbox satırı — F4-090 (domain atomic ile aynı tx)."""

from django.db import models


class OutboxMessage(models.Model):
    class Durum(models.TextChoices):
        PENDING = "PENDING", "Bekliyor"
        PROCESSED = "PROCESSED", "İşlendi"
        FAILED = "FAILED", "Başarısız"

    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    durum = models.CharField(
        max_length=16,
        choices=Durum.choices,
        default=Durum.PENDING,
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Outbox mesajı"
        verbose_name_plural = "Outbox mesajları"
        ordering = ["pk"]
        indexes = [
            models.Index(
                fields=["durum", "created_at"],
                name="outbox_durum_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(durum__in=["PENDING", "PROCESSED", "FAILED"]),
                name="outbox_durum_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"Outbox#{self.pk or '?'} {self.event_type} {self.durum}"
