"""Otomatik bildirim kuralları — outbox event → şablon."""

from __future__ import annotations

from django.db import models


class NotificationRule(models.Model):
    class RecipientMode(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Müşteri (alıcı firma)"
        ADMIN = "ADMIN", "Platform admin"
        BOTH = "BOTH", "Her ikisi"

    event_type = models.CharField(max_length=64, db_index=True)
    enabled = models.BooleanField(default=True)
    template = models.ForeignKey(
        "bildirim.EmailTemplate",
        on_delete=models.PROTECT,
        related_name="rules",
    )
    recipient_mode = models.CharField(
        max_length=16,
        choices=RecipientMode.choices,
        default=RecipientMode.CUSTOMER,
    )
    cc = models.JSONField(default=list, blank=True)
    bcc = models.JSONField(default=list, blank=True)
    attach_document_tips = models.BooleanField(
        default=False,
        help_text="İlgili Document metadata varsa body'ye storage_key notu ekle (PDF yok).",
    )
    aciklama = models.CharField(max_length=255, blank=True, default="")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bildirim kuralı"
        verbose_name_plural = "Bildirim kuralları"
        ordering = ["event_type", "pk"]
        permissions = [
            ("manage_notification_rule", "Bildirim kurallarını yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    recipient_mode__in=["CUSTOMER", "ADMIN", "BOTH"]
                ),
                name="notification_rule_recipient_mode_gecerli",
            ),
            models.UniqueConstraint(
                fields=["event_type", "template", "recipient_mode"],
                name="notification_rule_event_tpl_mode_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} → {self.template_id} ({self.recipient_mode})"
