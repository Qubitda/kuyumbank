from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class FiyatSozlesmesiKalemi(models.Model):
    """
    Sözleşme kalemi: metal + (opsiyonel) ayar bazında marj/işçilik tanımı.

    `ayar` boşsa "tüm ayarlar için geçerli" demektir. Aynı metal için hem
    genel (ayar=None) hem de spesifik (ayar=24K) kalem olamaz; en spesifik
    kazanır kuralı çözümleme motorunda uygulanır ve çakışma `clean()` ile
    engellenir.
    """

    class MarjTipi(models.TextChoices):
        YUZDE = "YUZDE", "Yüzde (%)"
        TL_GR = "TL_GR", "TL / gram"
        TL_PARCA = "TL_PARCA", "TL / parça (işçilik)"

    sozlesme = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesi",
        on_delete=models.CASCADE,
        related_name="kalemler",
    )
    metal = models.ForeignKey(
        "tanimlar.KiymetliMetal",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sozlesme_kalemleri",
        help_text="Takı ailesi gibi metal dışı durumlar için boş bırakılabilir.",
    )
    ayar = models.ForeignKey(
        "tanimlar.AyarMilyem",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sozlesme_kalemleri",
        help_text="Boş = tüm ayarlar.",
    )
    marj_tipi = models.CharField(max_length=16, choices=MarjTipi.choices)
    marj_degeri = models.DecimalField(max_digits=14, decimal_places=4)
    iscilik = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        help_text="Parça başına işçilik. Marj yüzde ise tabanı etkiler.",
    )
    islcilik_dahil_mi = models.BooleanField(
        default=False,
        help_text="Yüzde marjda taban: metal + işçilik olsun mu?",
    )
    sira = models.PositiveIntegerField(default=0)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sözleşme Kalemi"
        verbose_name_plural = "Sözleşme Kalemleri"
        ordering = ["sozlesme", "sira", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(marj_tipi="YUZDE")
                    | models.Q(marj_tipi="TL_GR")
                    | models.Q(marj_tipi="TL_PARCA")
                ),
                name="kalem_marj_tipi_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.sozlesme} — {self.metal or '—'} {self.ayar or 'tüm ayar'} "
            f"/ {self.marj_tipi}={self.marj_degeri}"
        )

    def clean(self):
        super().clean()
        if self.marj_degeri is not None and self.marj_degeri < 0:
            raise ValidationError("Marj değeri negatif olamaz.")

        if not self.sozlesme_id:
            return

        qs = FiyatSozlesmesiKalemi.objects.filter(
            sozlesme_id=self.sozlesme_id, metal=self.metal
        ).exclude(pk=self.pk)

        if self.ayar_id is None:
            # Genel kalem (tüm ayarlar): aynı metal için başka bir genel kalem olmamalı.
            if qs.filter(ayar__isnull=True).exists():
                raise ValidationError(
                    "Aynı metal için zaten bir 'tüm ayarlar' kalemi var."
                )
        else:
            # Spesifik ayar: aynı metal+ayar çifti bir kez olabilir.
            # Genel kalem de aynı anda olamaz (çakışma çözümleme motorunu kırar).
            if qs.filter(ayar__isnull=True).exists():
                raise ValidationError(
                    "Aynı metal için 'tüm ayarlar' kalemi zaten var; "
                    "spesifik kalem eklemek için önce onu kaldırın."
                )
            if qs.filter(ayar=self.ayar).exists():
                raise ValidationError("Aynı metal+ayar için kalem zaten mevcut.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)