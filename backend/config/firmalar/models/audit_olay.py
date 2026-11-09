from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditOlayQuerySet(models.QuerySet):
    """AUD-001 — bulk UPDATE/DELETE yasak."""

    def update(self, **kwargs):
        raise ValidationError(
            "AuditOlay değişmez; QuerySet.update yasak (AUD-001)."
        )

    def delete(self):
        raise ValidationError(
            "AuditOlay değişmez; QuerySet.delete yasak (AUD-001)."
        )


class AuditOlayManager(models.Manager.from_queryset(AuditOlayQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "AuditOlay değişmez; bulk_update yasak (AUD-001)."
        )


class AuditOlay(models.Model):
    """Kritik işlem denetim kaydı — silinmez, güncellenmez (AUD-001)."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_olaylari",
    )
    actor_firma = models.ForeignKey(
        "firmalar.Firma",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_olaylari",
    )
    action = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64, blank=True)
    entity_id = models.CharField(max_length=64, blank=True)
    success = models.BooleanField(default=True)
    detail = models.JSONField(default=dict, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    # AUD-001b — isteğe bağlı; mevcut detail korunur
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AuditOlayManager()

    class Meta:
        verbose_name = "Audit olayı"
        verbose_name_plural = "Audit olayları"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.action} ({self.entity_type}:{self.entity_id})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "AuditOlay değişmez; UPDATE yasak (AUD-001)."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "AuditOlay değişmez; DELETE yasak (AUD-001)."
        )
