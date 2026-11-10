"""Kar sim varsayılan kesintileri — birimli (ADR-0022 V2-8 / V2-10)."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class KesintiTipi(models.TextChoices):
    YUZDE = "YUZDE", "Yüzde (%)"
    TL = "TL", "Türk Lirası (TL)"


class PiyasaKarPolitikasi(models.Model):
    """Tek satır (`anahtar=default`); kar yardımcısı default alır."""

    anahtar = models.CharField("Anahtar", max_length=16, unique=True, default="default")
    banka_tipi = models.CharField(
        "Banka kesintisi birimi",
        max_length=8,
        choices=KesintiTipi.choices,
        default=KesintiTipi.YUZDE,
    )
    banka_degeri = models.DecimalField(
        "Banka kesintisi",
        max_digits=14,
        decimal_places=4,
        default=Decimal("2"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    isletme_tipi = models.CharField(
        "İşletme gideri birimi",
        max_length=8,
        choices=KesintiTipi.choices,
        default=KesintiTipi.YUZDE,
    )
    isletme_degeri = models.DecimalField(
        "İşletme gideri",
        max_digits=14,
        decimal_places=4,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    gelir_vergisi_tipi = models.CharField(
        "Gelir vergisi birimi",
        max_length=8,
        choices=KesintiTipi.choices,
        default=KesintiTipi.YUZDE,
    )
    gelir_vergisi_degeri = models.DecimalField(
        "Gelir vergisi",
        max_digits=14,
        decimal_places=4,
        default=Decimal("20"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    diger_tipi = models.CharField(
        "Diğer kesintiler birimi",
        max_length=8,
        choices=KesintiTipi.choices,
        default=KesintiTipi.TL,
    )
    diger_degeri = models.DecimalField(
        "Diğer kesintiler",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Piyasa kar politikası"
        verbose_name_plural = "Piyasa kar politikası"

    def __str__(self):
        return f"kar politikası ({self.anahtar})"

    def kesinti_dict(self) -> dict:
        return {
            "banka": {"tip": self.banka_tipi, "deger": self.banka_degeri},
            "isletme": {"tip": self.isletme_tipi, "deger": self.isletme_degeri},
            "gelir_vergisi": {
                "tip": self.gelir_vergisi_tipi,
                "deger": self.gelir_vergisi_degeri,
            },
            "diger": {"tip": self.diger_tipi, "deger": self.diger_degeri},
        }
