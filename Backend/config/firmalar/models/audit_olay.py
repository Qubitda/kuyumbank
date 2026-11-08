from django.conf import settings
from django.db import models


class AuditOlay(models.Model):
    """Kritik işlem denetim kaydı — silinmez, güncellenmez (uygulama disiplini)."""

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
    created_at = models.DateTimeField(auto_now_add=True)

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
