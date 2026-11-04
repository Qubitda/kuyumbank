from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .kiymetli_metal import KiymetliMetal


class MetalKuru(models.Model):
    KAYNAK = [("manuel", "Manuel"), ("api", "API"), ("websocket", "WebSocket")]

    metal = models.ForeignKey(KiymetliMetal, verbose_name="Metal", on_delete=models.PROTECT)
    zaman = models.DateTimeField("Kur zamanı", default=timezone.now)
    saf_birim_fiyat = models.DecimalField(
        "Saf birim fiyat (TL/gr)",
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    kaynak = models.CharField("Kaynak", max_length=10, choices=KAYNAK, default="manuel")
    girilme_zamani = models.DateTimeField(auto_now_add=True)
    giren_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Giren kullanıcı",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Metal kuru"
        verbose_name_plural = "Metal kurları"
        ordering = ["-zaman"]
        indexes = [models.Index(fields=["metal", "-zaman"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(saf_birim_fiyat__gt=0),
                name="metal_kuru_fiyat_pozitif",
            ),
            models.UniqueConstraint(
                fields=["metal", "zaman"], name="benzersiz_metal_zaman"
            ),
        ]

    def clean(self):
        super().clean()
        if self.metal_id and not self.metal.gram_bazli:
            raise ValidationError(
                {"metal": f"{self.metal.ad} gram bazlı değildir, kur girilemez."}
            )

    def __str__(self):
        return f"{self.metal.ad} {self.saf_birim_fiyat} ({self.zaman:%d.%m.%Y %H:%M})"