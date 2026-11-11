"""Platform alıcı / BCC varsayılanları — singleton."""

from __future__ import annotations

from django.db import models


class RecipientSettings(models.Model):
    admin_notify_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Platform admin bildirim adresleri.",
    )
    default_bcc = models.JSONField(default=list, blank=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Alıcı ayarı"
        verbose_name_plural = "Alıcı ayarları"

    def __str__(self) -> str:
        n = len(self.admin_notify_emails or [])
        return f"Alıcı ayarları ({n} admin)"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        raise ValidationError("RecipientSettings silinemez.")
