from django.db import models

from .firma import Firma


class FirmaBankaHesabi(models.Model):
    firma = models.ForeignKey(Firma, related_name="banka_hesaplari", on_delete=models.CASCADE)
    banka_adi = models.CharField("Banka", max_length=80)
    iban = models.CharField("IBAN", max_length=34)
    para_birimi = models.CharField("Para birimi", max_length=10, default="TRY")
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Banka hesabı"
        verbose_name_plural = "Banka hesapları"

    def __str__(self):
        return f"{self.firma.ad} - {self.banka_adi}"