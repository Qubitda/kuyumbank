"""Platform SMTP ayarları — tek satır singleton."""

from __future__ import annotations

from django.db import models


class SmtpSettings(models.Model):
    class Encryption(models.TextChoices):
        NONE = "NONE", "Yok"
        STARTTLS = "STARTTLS", "STARTTLS"
        SSL = "SSL", "SSL/TLS"

    host = models.CharField(max_length=255, blank=True, default="")
    port = models.PositiveIntegerField(default=587)
    encryption = models.CharField(
        max_length=16,
        choices=Encryption.choices,
        default=Encryption.STARTTLS,
    )
    username = models.CharField(max_length=255, blank=True, default="")
    # SECRET_KEY türevi sealed; plaintext asla DB'de tutulmaz.
    password_sealed = models.TextField(blank=True, default="")
    from_name = models.CharField(max_length=120, blank=True, default="")
    from_email = models.EmailField(blank=True, default="")
    reply_to = models.EmailField(blank=True, default="")
    enabled = models.BooleanField(default=False)
    max_attempts = models.PositiveSmallIntegerField(
        default=5,
        help_text="EmailDelivery retry üst sınırı.",
    )
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMTP ayarı"
        verbose_name_plural = "SMTP ayarları"
        permissions = [
            ("manage_smtp", "SMTP ayarlarını yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(encryption__in=["NONE", "STARTTLS", "SSL"]),
                name="smtp_encryption_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(port__gte=1) & models.Q(port__lte=65535),
                name="smtp_port_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(max_attempts__gte=1) & models.Q(max_attempts__lte=20),
                name="smtp_max_attempts_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"SMTP {self.host or '(env fallback)'} :{self.port}"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        raise ValidationError("SmtpSettings silinemez; disabled yapın.")
