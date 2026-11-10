"""CAP-ALERT — canlı metal kur eşik bildirimi (stale’de tetik yok)."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from .kiymetli_metal import KiymetliMetal
from .kur_tipi import KurTipi


class KurAlertKurali(models.Model):
    class Yon(models.TextChoices):
        YUKARI = "YUKARI", "Yukarı (fiyat ≥ eşik)"
        ASAGI = "ASAGI", "Aşağı (fiyat ≤ eşik)"

    metal = models.ForeignKey(
        KiymetliMetal,
        on_delete=models.CASCADE,
        related_name="kur_alert_kurallari",
    )
    kur_tipi = models.CharField(
        max_length=16, choices=KurTipi.choices, default=KurTipi.SATIS
    )
    yon = models.CharField(max_length=8, choices=Yon.choices)
    esik_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="TL/gr eşik; 0 yasak.",
    )
    aktif = models.BooleanField(default=True)
    son_tetik_gozlem = models.ForeignKey(
        "tanimlar.MetalKuru",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kur alert kuralı"
        verbose_name_plural = "Kur alert kuralları"
        ordering = ["metal_id", "kur_tipi", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(esik_fiyat__gt=0),
                name="kuralert_esik_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(yon__in=["YUKARI", "ASAGI"]),
                name="kuralert_yon_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"Alert#{self.pk or '?'} {self.metal_id} {self.yon} {self.esik_fiyat}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
