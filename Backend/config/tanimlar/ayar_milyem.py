from django.core.validators import MaxValueValidator
from django.db import models

from .kiymetli_metal import KiymetliMetal


class AyarMilyem(models.Model):
    metal = models.ForeignKey(
        KiymetliMetal,
        verbose_name="Metal",
        related_name="ayarlar",
        on_delete=models.PROTECT,
    )
    ayar_kodu = models.CharField("Ayar", max_length=10)
    milyem = models.PositiveIntegerField(
        "Milyem (‰)", validators=[MaxValueValidator(1000)]
    )

    class Meta:
        verbose_name = "Ayar / milyem"
        verbose_name_plural = "Milyem tablosu"
        ordering = ["metal", "milyem"]
        constraints = [
            models.UniqueConstraint(
                fields=["metal", "ayar_kodu"], name="benzersiz_metal_ayar"
            ),
        ]

    def __str__(self):
        return f"{self.metal.ad} {self.ayar_kodu}"