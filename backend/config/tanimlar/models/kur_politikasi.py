"""Alıcı/tedarikçi kur tipi politikası (ADR-0008 B-05 / Dilim 3.3 + ADR-0018)."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from tanimlar.fiyat_kaynagi import FeedHealth, FiyatKaynagi

from .kur_tipi import KurTipi


class KurPolitikasi(models.Model):
    """Tek satır beklenir (`anahtar=default`); servis get_or_create ile okur."""

    anahtar = models.CharField("Anahtar", max_length=16, unique=True, default="default")
    alici_kur_tipi = models.CharField(
        "Alıcı kur tipi",
        max_length=16,
        choices=KurTipi.choices,
        default=KurTipi.SATIS,
    )
    tedarikci_kur_tipi = models.CharField(
        "Tedarikçi kur tipi",
        max_length=16,
        choices=KurTipi.choices,
        default=KurTipi.ALIS,
    )
    # ADR-0018 CAP-PIYASA
    fiyat_kaynagi = models.CharField(
        "Varsayılan fiyat kaynağı",
        max_length=16,
        choices=FiyatKaynagi.CHOICES_POLITIKA,
        default=FiyatKaynagi.CANLI_PIYASA,
    )
    feed_health = models.CharField(
        "Feed health",
        max_length=24,
        choices=FeedHealth.CHOICES,
        default=FeedHealth.FEED_OK,
    )
    feed_banner = models.CharField("Feed banner", max_length=255, blank=True, default="")
    sok_esigi_yuzde = models.DecimalField(
        "Şok eşiği %",
        max_digits=6,
        decimal_places=2,
        default=Decimal("5.00"),
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
    )
    capraz_makas_esigi_yuzde = models.DecimalField(
        "Çapraz makas eşiği %",
        max_digits=6,
        decimal_places=2,
        default=Decimal("2.00"),
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
    )
    min_marj_pct = models.DecimalField(
        "Min marj % (guardrail)",
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    max_batch_satir = models.PositiveIntegerField(
        "Max batch satır",
        default=500,
        validators=[MinValueValidator(1)],
    )
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kur politikası"
        verbose_name_plural = "Kur politikası"

    def __str__(self):
        return (
            f"alıcı={self.alici_kur_tipi} / tedarikçi={self.tedarikci_kur_tipi}"
        )
