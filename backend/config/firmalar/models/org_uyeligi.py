"""OrgUyeligi — kullanıcı ↔ org birimi (ADR-0015 OH-2)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class OrgUyeligi(models.Model):
    kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_uyelikleri",
    )
    org_birimi = models.ForeignKey(
        "firmalar.OrgBirimi",
        on_delete=models.CASCADE,
        related_name="uyelikler",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Org üyeliği"
        verbose_name_plural = "Org üyelikleri"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["kullanici", "org_birimi"],
                name="orguyeligi_kullanici_org_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"OU#{self.pk or '?'} U{self.kullanici_id}→OB{self.org_birimi_id}"

    def clean(self):
        super().clean()
        if self.kullanici_id and self.org_birimi_id:
            if self.kullanici.firma_id != self.org_birimi.firma_id:
                raise ValidationError(
                    "Org üyeliği yalnız kullanıcının firması içinde (OH-2/OH-4)."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
