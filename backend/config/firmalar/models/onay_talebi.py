"""OnayTalebi — limit aşımı / satın alma onay SM (F10-013)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class OnayTalebi(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        BEKLEMEDE = "BEKLEMEDE", "Beklemede"
        ONAYLANDI = "ONAYLANDI", "Onaylandı"
        REDDEDILDI = "REDDEDILDI", "Reddedildi"

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="onay_talepleri",
    )
    org_birimi = models.ForeignKey(
        "firmalar.OrgBirimi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="onay_talepleri",
    )
    order = models.ForeignKey(
        "siparis.Order",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="onay_talepleri",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    tutar = models.DecimalField(max_digits=18, decimal_places=2)
    para_birimi = models.CharField(max_length=3, default="TRY")
    gerekce = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_onaylar",
    )
    karar_veren = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="karar_verdigi_onaylar",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Onay talebi"
        verbose_name_plural = "Onay talepleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_approval", "Onay talebi yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["TASLAK", "BEKLEMEDE", "ONAYLANDI", "REDDEDILDI"]
                ),
                name="onaytalebi_durum_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(tutar__gt=0),
                name="onaytalebi_tutar_pozitif",
            ),
        ]
        indexes = [
            models.Index(fields=["firma", "durum"]),
        ]

    def __str__(self) -> str:
        return f"OT#{self.pk or '?'} {self.durum} {self.tutar}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "OnayTalebi değişmez; geçiş yalnız onay_servisi (F10-013)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("OnayTalebi silinemez.")
