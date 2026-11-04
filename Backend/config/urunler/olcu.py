from django.db import models


class OlcuDegeri(models.Model):
    """Varyant ekseni olarak beden/ölçü değerleri (Medusa'daki ProductOptionValue karşılığı).

    Serbest metin yerine tablo: "2" ile "14" doğru sıralanır, vitrinde filtrelenir,
    "14" ile "14 " ayrı değer olarak girilemez.
    """

    TIP = [
        ("yuzuk_no", "Yüzük numarası"),
        ("bilezik_boyu", "Bilezik boyu (cm)"),
        ("zincir_uzunlugu", "Zincir / kolye uzunluğu (cm)"),
    ]

    tip = models.CharField("Ölçü tipi", max_length=15, choices=TIP)
    deger = models.CharField("Değer", max_length=20, help_text="Örn: 14, 19 cm, 45 cm")
    sira = models.PositiveIntegerField("Sıra", default=0)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Ölçü değeri"
        verbose_name_plural = "Ölçü değerleri"
        ordering = ["tip", "sira", "deger"]
        constraints = [
            models.UniqueConstraint(fields=["tip", "deger"], name="benzersiz_olcu_tip_deger"),
        ]

    def __str__(self):
        return f"{self.get_tip_display()}: {self.deger}"
