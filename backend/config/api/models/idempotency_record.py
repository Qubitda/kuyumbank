"""HTTP Idempotency-Key kayıtları (PRE-005) — firma-scoped."""

from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    """Tamamlanmış POST/PUT/PATCH yanıt önbelleği; tenant = firma."""

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.CASCADE,
        related_name="idempotency_records",
    )
    key = models.CharField(max_length=128)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    status_code = models.PositiveSmallIntegerField()
    response_body = models.JSONField(default=dict)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["firma", "key"],
                name="api_idempotency_firma_key_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["firma", "key"], name="api_idem_firma_key_idx"),
        ]

    def __str__(self) -> str:
        return f"Idem#{self.pk or '?'} {self.key}"
