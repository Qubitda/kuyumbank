"""E-posta kuyruğu / log."""

from __future__ import annotations

from django.db import models


class EmailDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Bekliyor"
        SENT = "SENT", "Gönderildi"
        FAILED = "FAILED", "Başarısız"

    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error = models.CharField(max_length=255, blank=True, default="")
    attempts = models.PositiveSmallIntegerField(default=0)
    template = models.ForeignKey(
        "bildirim.EmailTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deliveries",
    )
    rule = models.ForeignKey(
        "bildirim.NotificationRule",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deliveries",
    )
    event_type = models.CharField(max_length=64, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=191, unique=True)
    order_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    related_refs = models.JSONField(default=dict, blank=True)
    attachment_notes = models.TextField(
        blank=True,
        default="",
        help_text="Document storage_key notları (binary ek yok).",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "E-posta gönderimi"
        verbose_name_plural = "E-posta logları"
        ordering = ["-created_at", "-pk"]
        permissions = [
            ("send_manual_email", "Manuel e-posta gönderebilir"),
            ("view_email_log", "E-posta loglarını görebilir"),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["PENDING", "SENT", "FAILED"]),
                name="email_delivery_status_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"ED#{self.pk or '?'} {self.status} {self.subject[:40]}"
