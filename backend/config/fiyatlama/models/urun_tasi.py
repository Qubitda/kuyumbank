from django.db import models
from decimal import Decimal


class UrunTasi(models.Model):
    """Teklife bağlı taş satırı. Pırlanta / renkli / süs taşı ortak + özel alanlar."""

    class TasGrubu(models.TextChoices):
        PIRLANTA = "PIRLANTA", "Pırlanta"
        RENKLI = "RENKLI", "Renkli taş"
        SUS_TASI = "SUS_TASI", "Süs taşı"

    teklif = models.ForeignKey(
        "fiyatlama.TedarikciTeklif",
        on_delete=models.CASCADE,
        related_name="taslar",
    )
    tas_grubu = models.CharField(max_length=16, choices=TasGrubu.choices)
    adet = models.PositiveIntegerField(default=1)
    toplam_karat = models.DecimalField(max_digits=10, decimal_places=4)
    toplu_mu = models.BooleanField(default=False)
    bedel = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    para_birimi = models.CharField(max_length=3, default="TRY")

    # Pırlanta alanları (sadece PIRLANTA için)
    renk_derecesi = models.CharField(max_length=8, blank=True)
    berraklik = models.CharField(max_length=8, blank=True)
    kesim = models.CharField(max_length=16, blank=True)
    sertifika_kurumu = models.CharField(max_length=32, blank=True)
    sertifika_no = models.CharField(max_length=64, blank=True)

    # Renkli taş alanları (sadece RENKLI için)
    tas_turu = models.CharField(max_length=64, blank=True)
    mense = models.CharField(max_length=64, blank=True)
    islem = models.CharField(max_length=64, blank=True)

    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ürün Taşı"
        verbose_name_plural = "Ürün Taşları"
        ordering = ["teklif", "id"]

    def __str__(self) -> str:
        return f"{self.get_tas_grubu_display()} — {self.toplam_karat}ct"