"""Shipment — sipariş sevkiyat SM (ADR-0013 F6-K6 / F6-020)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Shipment(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        HAZIR = "HAZIR", "Hazır"
        YOLDA = "YOLDA", "Yolda"
        TESLIM = "TESLIM", "Teslim"
        IPTAL = "IPTAL", "İptal"

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    takip_no = models.CharField(
        max_length=64,
        blank=True,
        help_text="F6-021 carrier port doldurur; v1 elle/boş.",
    )
    notlar = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_shipments",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Sevkiyat"
        verbose_name_plural = "Sevkiyatlar"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_shipment", "Sevkiyat oluşturup yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["TASLAK", "HAZIR", "YOLDA", "TESLIM", "IPTAL"]
                ),
                name="shipment_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["order", "durum"]),
            models.Index(fields=["durum"]),
        ]

    def __str__(self) -> str:
        return f"SH#{self.pk or '?'} O#{self.order_id} {self.durum}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "Shipment değişmez; geçiş yalnız shipment_servisi (F6-020)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("Shipment silinemez.")
