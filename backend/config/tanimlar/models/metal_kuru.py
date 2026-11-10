from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .kiymetli_metal import KiymetliMetal
from .kur_saglayici import KurSaglayici
from .kur_tipi import KurTipi


class MetalKuru(models.Model):
    KAYNAK = [
        ("manuel", "Manuel"),
        ("api", "API"),
        ("websocket", "WebSocket"),
        ("tcmb", "TCMB EOD"),
    ]

    metal = models.ForeignKey(KiymetliMetal, verbose_name="Metal", on_delete=models.PROTECT)
    saglayici = models.ForeignKey(
        KurSaglayici,
        verbose_name="Sağlayıcı",
        on_delete=models.PROTECT,
        related_name="metal_kurlar",
    )
    kur_tipi = models.CharField(
        "Kur tipi", max_length=16, choices=KurTipi.choices, default=KurTipi.SATIS
    )
    zaman = models.DateTimeField("Piyasa zamanı", default=timezone.now)
    alinma_zamani = models.DateTimeField("Alınma zamanı", default=timezone.now)
    saf_birim_fiyat = models.DecimalField(
        "Saf birim fiyat (TL/gr)",
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    kaynak = models.CharField("Kaynak", max_length=10, choices=KAYNAK, default="manuel")
    manuel_neden = models.TextField("Manuel neden", blank=True, default="")
    girilme_zamani = models.DateTimeField(auto_now_add=True)
    giren_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Giren kullanıcı",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    onaylayan_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Onaylayan kullanıcı",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    onay_zamani = models.DateTimeField("Onay zamanı", null=True, blank=True)

    class Meta:
        verbose_name = "Metal kuru"
        verbose_name_plural = "Metal kurları"
        ordering = ["-zaman"]
        indexes = [
            models.Index(fields=["metal", "kur_tipi", "-zaman"]),
            models.Index(fields=["saglayici", "metal", "-zaman"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(saf_birim_fiyat__gt=0),
                name="metal_kuru_fiyat_pozitif",
            ),
            models.UniqueConstraint(
                fields=["metal", "kur_tipi", "zaman"],
                name="benzersiz_metal_kur_tipi_zaman",
            ),
        ]

    def clean(self):
        super().clean()
        if self.metal_id and not self.metal.gram_bazli:
            raise ValidationError(
                {"metal": f"{self.metal.ad} gram bazlı değildir, kur girilemez."}
            )
        if self.kaynak == "manuel" and not (self.manuel_neden or "").strip():
            raise ValidationError({"manuel_neden": "Manuel kur girişinde neden zorunludur."})

    def __str__(self):
        return (
            f"{self.metal.ad} {self.kur_tipi} {self.saf_birim_fiyat} "
            f"({self.zaman:%d.%m.%Y %H:%M})"
        )
