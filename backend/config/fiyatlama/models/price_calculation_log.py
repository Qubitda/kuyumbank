from decimal import Decimal

from django.db import models


class PriceCalculationLog(models.Model):
    """
    Her hesap ve kilit buraya yazılır. Kırılım SADECE burada durur;
    alıcı/tedarikçi serializer'larına sızdırılmaz (v3 §6).
    """

    class Kaynak(models.TextChoices):
        HESAP = "HESAP", "Normal hesap"
        KILIT = "KILIT", "Fiyat kilidi"
        KONTROL_DUZELTME = "KONTROL_DUZELTME", "Kontrol düzeltmesi"

    sozlesme = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesi",
        on_delete=models.PROTECT,
        related_name="hesap_loglari",
    )
    kalem = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesiKalemi",
        on_delete=models.PROTECT,
        related_name="hesap_loglari",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",          # ← DÜZELTİLDİ: UrunVaryant → Varyant
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="hesap_loglari",
    )

    # Girdiler
    gram = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    milyem = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    saf_birim_fiyat = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    para_birimi = models.CharField(max_length=3, default="TRY")
    kur_tipi = models.CharField(max_length=32, blank=True)
    kur_degeri = models.DecimalField(
        max_digits=14, decimal_places=6, null=True, blank=True
    )
    tas_bedeli = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    # Çıktı (yuvarlanmamış ara değerler)
    metal_bedeli = models.DecimalField(max_digits=18, decimal_places=6)
    iscilik = models.DecimalField(max_digits=14, decimal_places=2)
    marj = models.DecimalField(max_digits=18, decimal_places=6)
    toplam = models.DecimalField(max_digits=18, decimal_places=6)

    kaynak = models.CharField(
        max_length=16, choices=Kaynak.choices, default=Kaynak.HESAP
    )
    kilit_bitis = models.DateTimeField(null=True, blank=True)
    notlar = models.TextField(blank=True)
    hesap_zamani = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fiyat Hesap Logu"
        verbose_name_plural = "Fiyat Hesap Logları"
        ordering = ["-hesap_zamani"]
        indexes = [
            models.Index(fields=["sozlesme", "-hesap_zamani"]),
            models.Index(fields=["varyant", "-hesap_zamani"]),
        ]

    def __str__(self) -> str:
        return f"{self.sozlesme} @ {self.hesap_zamani:%Y-%m-%d %H:%M}"