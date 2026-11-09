"""QualityInspection — sipariş QC durum makinesi (ADR-0013 F6-K5, F6-010)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class QualityInspection(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        OLCUMDE = "OLCUMDE", "Ölçümde"
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        IPTAL = "IPTAL", "İptal"

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="quality_inspections",
    )
    order_line = models.ForeignKey(
        "siparis.OrderLine",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="quality_inspections",
        help_text="V1 sipariş bazlı; satır rezerv (F6-K cevap 2).",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    shipment_blok = models.BooleanField(
        default=False,
        help_text="FAIL → True; sevkiyat create engeli (F6-010 / F6-K6).",
    )
    notlar = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_qc",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Kalite kontrolü"
        verbose_name_plural = "Kalite kontrolleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_qc", "Kalite kontrolünü yönetebilir"),
            ("view_qc", "Kalite kontrolünü görebilir"),
            ("manage_qc_override", "QC tolerans override (gerekçeli)"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["TASLAK", "OLCUMDE", "PASS", "FAIL", "IPTAL"]
                ),
                name="qualityinspection_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["order", "durum"]),
            models.Index(fields=["shipment_blok"]),
        ]

    def __str__(self) -> str:
        return f"QI#{self.pk or '?'} O#{self.order_id} {self.durum}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "QualityInspection değişmez; geçiş yalnız inspection_servisi (F6-010)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("QualityInspection silinemez.")
