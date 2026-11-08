from django.db import models



class FirmaAdresi(models.Model):
    TIP = [("merkez", "Merkez"), ("depo", "Depo"), ("sevk", "Sevk"), ("fatura", "Fatura")]

    firma = models.ForeignKey("firmalar.Firma", related_name="adresler", on_delete=models.CASCADE)
    tip = models.CharField("Adres tipi", max_length=10, choices=TIP, default="merkez")
    il = models.CharField("İl", max_length=50)
    ilce = models.CharField("İlçe", max_length=50, blank=True)
    adres = models.TextField("Açık adres")
    varsayilan = models.BooleanField("Varsayılan", default=False)

    class Meta:
        verbose_name = "Firma adresi"
        verbose_name_plural = "Firma adresleri"

    def __str__(self):
        return f"{self.firma.ad} - {self.get_tip_display()}"