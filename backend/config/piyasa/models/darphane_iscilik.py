"""Darphane işçilik tablosu — pano bazına otomatik eklenmez (ADR-0022 V2-6/7)."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class DarphaneIscilik(models.Model):
    class Kanal(models.TextChoices):
        YENI_HAS = "YENI_HAS", "Yeni HAS"
        ESKI_HAS = "ESKI_HAS", "Eski HAS"
        BORSA_HAS = "BORSA_HAS", "Borsa HAS"

    urun = models.ForeignKey(
        "piyasa.PiyasaUrun",
        verbose_name="Pano ürünü",
        on_delete=models.CASCADE,
        related_name="darphane_iscilikler",
    )
    kanal = models.CharField("Kanal", max_length=16, choices=Kanal.choices)
    iscilik_tl = models.DecimalField(
        "İşçilik (TL)",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    aktif = models.BooleanField("Aktif", default=True)
    sira = models.PositiveIntegerField("Sıra", default=0)
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Darphane işçilik"
        verbose_name_plural = "Darphane işçilikleri"
        ordering = ["sira", "urun_id", "kanal"]
        constraints = [
            models.UniqueConstraint(
                fields=["urun", "kanal"],
                name="piyasa_darphane_urun_kanal_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.urun.kod} / {self.kanal} = {self.iscilik_tl}"
