"""Firma kullanıcı daveti — token ile kabul."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from firmalar import roles


class FirmaInvite(models.Model):
    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.CASCADE,
        related_name="invites",
    )
    email = models.EmailField()
    rol = models.CharField(max_length=30, choices=roles.ROLE_CHOICES)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_invites",
    )
    kabul_edildi_at = models.DateTimeField(null=True, blank=True)
    kabul_eden = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="kabul_ettigi_invites",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Firma daveti"
        verbose_name_plural = "Firma davetleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        indexes = [
            models.Index(fields=["firma", "email"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["firma", "email"],
                condition=models.Q(kabul_edildi_at__isnull=True),
                name="firma_invite_pending_email_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"Invite {self.email} → {self.firma_id} ({self.rol})"

    @property
    def is_pending(self) -> bool:
        return self.kabul_edildi_at is None

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
