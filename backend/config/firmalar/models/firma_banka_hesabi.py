from django.db import models



class FirmaBankaHesabi(models.Model):
    firma = models.ForeignKey("firmalar.Firma", related_name="banka_hesaplari", on_delete=models.CASCADE)
    banka_adi = models.CharField("Banka", max_length=80)
    iban = models.CharField("IBAN", max_length=34)
    swift_bic = models.CharField(
        "SWIFT / BIC",
        max_length=11,
        blank=True,
        default="",
        help_text="Uluslararası transfer için banka SWIFT/BIC kodu (8 veya 11 karakter).",
    )
    para_birimi = models.CharField("Para birimi", max_length=10, default="TRY")
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Banka hesabı"
        verbose_name_plural = "Banka hesapları"

    def __str__(self):
        return f"{self.firma.ad} - {self.banka_adi}"