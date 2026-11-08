from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from .kiymetli_metal import KiymetliMetal

class AyarMilyem(models.Model):
    metal = models.ForeignKey(
        KiymetliMetal,
        verbose_name="Metal",
        related_name="ayarlar",
        on_delete=models.PROTECT,
    )
    # Örn: 14, 18, 22, 925 (Sayısal filtrelemeler ve sıralamalar için)
    ayar_degeri = models.PositiveIntegerField(
        "Ayar / Karat Değeri",
        help_text="Altın için karat (14, 22), Gümüş için saflık derecesi (925) giriniz."
    )
    # Örn: "14K", "22K", "925 Ayar" (Müşteriye ve faturaya basılacak etiket)
    ayar_kodu = models.CharField(
        "Ayar Kodu (Etiket)",
        max_length=15
    )
    # Finansal/Matematiksel işlemlerde doğrudan çarpan olarak kullanılacak alan
    milyem = models.DecimalField(
        "Milyem Karşılığı (Saflık Oranı)",
        max_digits=4,
        decimal_places=3,
        validators=[
            MinValueValidator(0.000),
            MaxValueValidator(1.000)
        ],
        help_text="Has metal oranını ondalık girin. Örn: 14K Altın için 0.585, 925 Gümüş için 0.925"
    )

    class Meta:
        verbose_name = "Ayar / milyem"
        verbose_name_plural = "Milyem tablosu"
        ordering = ["metal", "milyem"]
        constraints = [
            # 1. Hata Önleme: Aynı metal türünde aynı kod iki kez açılamaz
            models.UniqueConstraint(
                fields=["metal", "ayar_kodu"], name="benzersiz_metal_ayar_kodu"
            ),
            # 2. Hata Önleme: Aynı metal türünde aynı saflık oranı (milyem) iki kez tanımlanamaz
            models.UniqueConstraint(
                fields=["metal", "milyem"], name="benzersiz_metal_milyem_orani"
            ),
        ]

    def __str__(self):
        return f"{self.metal.ad} - {self.ayar_kodu} ({self.milyem})"
