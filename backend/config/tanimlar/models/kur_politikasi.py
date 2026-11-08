"""Alıcı/tedarikçi kur tipi politikası (ADR-0008 B-05 / Dilim 3.3)."""

from django.db import models

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
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kur politikası"
        verbose_name_plural = "Kur politikası"

    def __str__(self):
        return (
            f"alıcı={self.alici_kur_tipi} / tedarikçi={self.tedarikci_kur_tipi}"
        )
