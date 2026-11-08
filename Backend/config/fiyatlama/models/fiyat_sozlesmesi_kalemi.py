from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class FiyatSozlesmesiKalemi(models.Model):
    """
    Sözleşme kalemi: metal + (opsiyonel) ayar bazında marj/işçilik tanımı.

    `ayar` boşsa "tüm ayarlar için geçerli" (fallback). Aynı metal için genel
    ve spesifik kalemler birlikte olabilir (ADR-0007 §2.2 / K-007).
    Tekillik: (sozlesme, metal, ayar) NULL-safe unique.
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
        help_text="Boş = tüm ayarlar (fallback).",
    )
    marj_tipi = models.CharField(max_length=16, choices=MarjTipi.choices)
    marj_degeri = models.DecimalField(max_digits=14, decimal_places=4)
    iscilik = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
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
            # K-007: PostgreSQL NULL'ları aynı kabul et (Django 6.1 nulls_distinct=False)
            models.UniqueConstraint(
                fields=["sozlesme", "metal", "ayar"],
                nulls_distinct=False,
                name="kalem_sozlesme_metal_ayar_uniq",
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

        if self.sozlesme_id:
            from fiyatlama.models import FiyatSozlesmesi

            # Bellekteki stale durum değil; DB'den oku (AKTIF immutability)
            durum = (
                FiyatSozlesmesi.objects.filter(pk=self.sozlesme_id)
                .values_list("durum", flat=True)
                .first()
            )
            if durum == FiyatSozlesmesi.Durum.AKTIF:
                raise ValidationError(
                    "AKTIF sözleşme kalemi değiştirilemez; yeni versiyon açın."
                )

            qs = FiyatSozlesmesiKalemi.objects.filter(
                sozlesme_id=self.sozlesme_id,
                metal=self.metal,
                ayar=self.ayar,
            ).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Aynı sözleşme + metal + ayar için kalem zaten mevcut."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
