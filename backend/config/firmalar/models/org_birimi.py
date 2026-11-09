"""OrgBirimi — firma-içi şube/org birimi (ADR-0015 OH-1; U-014 A)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class OrgBirimi(models.Model):
    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="org_birimleri",
        help_text="Tenant sınırı; org firma dışına taşamaz (OH-1).",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cocuklar",
    )
    kod = models.CharField(max_length=32)
    ad = models.CharField(max_length=128)
    aktif = models.BooleanField(default=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Org birimi"
        verbose_name_plural = "Org birimleri"
        ordering = ["firma_id", "kod"]
        permissions = [
            ("manage_org", "Firma içi org/şube yönetebilir"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["firma", "kod"],
                name="orgbirimi_firma_kod_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["firma", "aktif"]),
        ]

    def __str__(self) -> str:
        return f"OB#{self.pk or '?'} {self.kod}@{self.firma_id}"

    def clean(self):
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "Org birimi kendisinin parent'ı olamaz."})
        if self.parent_id and self.firma_id:
            if self.parent.firma_id != self.firma_id:
                raise ValidationError(
                    {"parent": "Parent aynı firmaya ait olmalı (OH-4)."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
