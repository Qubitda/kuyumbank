from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .kur_saglayici import KurSaglayici
from .kur_tipi import KurTipi


class DovizKuru(models.Model):
    KAYNAK = [("manuel", "Manuel"), ("api", "API")]
    PARA_BIRIMI = [("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")]

    para_birimi = models.CharField("Para birimi", max_length=10, choices=PARA_BIRIMI)
    saglayici = models.ForeignKey(
        KurSaglayici,
        verbose_name="Sağlayıcı",
        on_delete=models.PROTECT,
        related_name="doviz_kurlar",
    )
    kur_tipi = models.CharField(
        "Kur tipi", max_length=16, choices=KurTipi.choices, default=KurTipi.SATIS
    )
    zaman = models.DateTimeField("Piyasa zamanı", default=timezone.now)
    alinma_zamani = models.DateTimeField("Alınma zamanı", default=timezone.now)
    kur = models.DecimalField(
        "Kur (TL)",
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
        verbose_name = "Döviz kuru"
        verbose_name_plural = "Döviz kurları"
        ordering = ["-zaman"]
        indexes = [
            models.Index(fields=["para_birimi", "kur_tipi", "-zaman"]),
            models.Index(fields=["saglayici", "para_birimi", "-zaman"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kur__gt=0),
                name="doviz_kuru_pozitif",
            ),
            models.UniqueConstraint(
                fields=["para_birimi", "kur_tipi", "zaman"],
                name="benzersiz_doviz_kur_tipi_zaman",
            ),
        ]

    def clean(self):
        super().clean()
        if self.kaynak == "manuel" and not (self.manuel_neden or "").strip():
            raise ValidationError({"manuel_neden": "Manuel kur girişinde neden zorunludur."})

    def __str__(self):
        return (
            f"{self.para_birimi} {self.kur_tipi} {self.kur} "
            f"({self.zaman:%d.%m.%Y %H:%M})"
        )
