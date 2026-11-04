from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class DovizKuru(models.Model):
    KAYNAK = [("manuel", "Manuel"), ("api", "API")]
    PARA_BIRIMI = [("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")]

    para_birimi = models.CharField("Para birimi", max_length=10, choices=PARA_BIRIMI)
    zaman = models.DateTimeField("Kur zamanı", default=timezone.now)
    kur = models.DecimalField(
        "Kur (TL)",
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
        verbose_name = "Döviz kuru"
        verbose_name_plural = "Döviz kurları"
        ordering = ["-zaman"]
        indexes = [models.Index(fields=["para_birimi", "-zaman"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kur__gt=0),
                name="doviz_kuru_pozitif",
            ),
            models.UniqueConstraint(
                fields=["para_birimi", "zaman"], name="benzersiz_doviz_zaman"
            ),
        ]

    def __str__(self):
        return f"{self.para_birimi} {self.kur} ({self.zaman:%d.%m.%Y %H:%M})"