"""QualityMeasurement — append-only QC ölçüm kaydı (ADR-0013 F6-K9 / F6-011)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from siparis.birim_constants import SepetBirimi


class QualityMeasurementQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "QualityMeasurement değişmez; QuerySet.update yasak (F6-K9)."
        )

    def delete(self):
        raise ValidationError(
            "QualityMeasurement değişmez; QuerySet.delete yasak (F6-K9)."
        )


class QualityMeasurementManager(models.Manager.from_queryset(QualityMeasurementQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "QualityMeasurement değişmez; bulk_update yasak (F6-K9)."
        )


class QualityMeasurement(models.Model):
    class Sonuc(models.TextChoices):
        UYGUN = "UYGUN", "Tolerans içinde"
        SAPMA = "SAPMA", "Tolerans dışı"

    inspection = models.ForeignKey(
        "kalite.QualityInspection",
        on_delete=models.PROTECT,
        related_name="measurements",
    )
    order_line = models.ForeignKey(
        "siparis.OrderLine",
        on_delete=models.PROTECT,
        related_name="quality_measurements",
    )
    birim = models.CharField(max_length=8, choices=SepetBirimi.CHOICES)
    beklenen = models.DecimalField(max_digits=18, decimal_places=6)
    olculen = models.DecimalField(max_digits=18, decimal_places=6)
    sapma_abs = models.DecimalField(max_digits=18, decimal_places=6)
    tolerans_pct = models.DecimalField(max_digits=8, decimal_places=4)
    tolerans_abs = models.DecimalField(max_digits=18, decimal_places=6)
    izin_verilen_sapma = models.DecimalField(max_digits=18, decimal_places=6)
    sonuc = models.CharField(max_length=8, choices=Sonuc.choices)
    override_uygulandi = models.BooleanField(default=False)
    override_gerekce = models.CharField(max_length=255, blank=True)
    quote_gram = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="F6-K2 zincir kanıtı: PriceLock.quote.gram (GRAM satırında).",
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_qc_olcum",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    objects = QualityMeasurementManager()

    class Meta:
        verbose_name = "QC ölçüm"
        verbose_name_plural = "QC ölçümleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        indexes = [
            models.Index(fields=["inspection", "-olusturma_tarihi"]),
            models.Index(fields=["order_line"]),
            models.Index(fields=["sonuc"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(beklenen__gt=0),
                name="qualitymeasurement_beklenen_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(olculen__gte=0),
                name="qualitymeasurement_olculen_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(sapma_abs__gte=0),
                name="qualitymeasurement_sapma_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(izin_verilen_sapma__gte=0),
                name="qualitymeasurement_izin_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(tolerans_pct__gte=0),
                name="qualitymeasurement_pct_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(tolerans_abs__gte=0),
                name="qualitymeasurement_abs_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="qualitymeasurement_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(sonuc__in=["UYGUN", "SAPMA"]),
                name="qualitymeasurement_sonuc_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"QM#{self.pk or '?'} QI#{self.inspection_id} "
            f"{self.olculen}/{self.beklenen} {self.birim} {self.sonuc}"
        )

    def clean(self):
        super().clean()
        if self.beklenen is not None and self.beklenen <= 0:
            raise ValidationError({"beklenen": "Beklenen pozitif olmalı."})
        if self.olculen is not None and self.olculen < 0:
            raise ValidationError({"olculen": "Ölçülen negatif olamaz."})
        if self.override_uygulandi and len((self.override_gerekce or "").strip()) < 10:
            raise ValidationError(
                {"override_gerekce": "Override gerekçesi en az 10 karakter (F6-K4)."}
            )
        if self.order_line_id and self.inspection_id:
            if self.order_line.order_id != self.inspection.order_id:
                raise ValidationError(
                    {"order_line": "Ölçüm satırı inspection siparişine ait olmalı."}
                )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "QualityMeasurement değişmez; UPDATE yasak (F6-K9)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("QualityMeasurement silinemez (F6-K9).")
