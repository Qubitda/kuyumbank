from django.core.exceptions import ValidationError
from django.db import models


class UrunTasi(models.Model):
    """Ürüne ait bir taş satırı. Birden fazla taş varsa birden fazla satır girilir.

    4C ve sertifika alanları şimdilik açıklayıcıdır, fiyatı etkilemez; taş bedelini
    tedarikçi girer (`bedel`).
    """

    urun = models.ForeignKey("urunler.Urun", verbose_name="Ürün", related_name="taslar", on_delete=models.CASCADE)
    tas_tipi = models.ForeignKey("urunler.TasTipi", verbose_name="Taş tipi", on_delete=models.PROTECT)
    adet = models.PositiveIntegerField("Adet", default=1)
    karat = models.DecimalField("Toplam karat", max_digits=7, decimal_places=3, null=True, blank=True)
    bedel = models.DecimalField("Taş bedeli (TL)", max_digits=14, decimal_places=2, default=0)

    kesim = models.ForeignKey("urunler.TasKesimi", verbose_name="Kesim", null=True, blank=True, on_delete=models.PROTECT)
    mihlama_tipi = models.ForeignKey(
        "urunler.MihlamaTipi", verbose_name="Mıhlama tipi", null=True, blank=True, on_delete=models.PROTECT,
    )
    mensei = models.ForeignKey("urunler.TasMensei", verbose_name="Menşei", null=True, blank=True, on_delete=models.PROTECT)
    berraklik = models.ForeignKey("urunler.Berraklik", verbose_name="Berraklık", null=True, blank=True, on_delete=models.PROTECT)
    renk_derecesi = models.ForeignKey(
        "urunler.RenkDerecesi", verbose_name="Renk derecesi", null=True, blank=True, on_delete=models.PROTECT,
    )
    kesim_kalitesi = models.ForeignKey(
        "urunler.KesimKalitesi", verbose_name="Kesim kalitesi", null=True, blank=True, on_delete=models.PROTECT,
    )
    sertifika_kurumu = models.ForeignKey(
        "urunler.SertifikaKurumu", verbose_name="Sertifika kurumu", null=True, blank=True, on_delete=models.PROTECT,
    )
    sertifika_no = models.CharField("Sertifika no", max_length=50, blank=True)

    class Meta:
        verbose_name = "Ürün taşı"
        verbose_name_plural = "Ürün taşları"
        constraints = [
            models.CheckConstraint(condition=models.Q(adet__gte=1), name="urun_tasi_adet_pozitif"),
            models.CheckConstraint(condition=models.Q(bedel__gte=0), name="urun_tasi_bedel_negatif_degil"),
        ]

    def clean(self):
        super().clean()
        if self.sertifika_no and not self.sertifika_kurumu_id:
            raise ValidationError({"sertifika_kurumu": "Sertifika numarası girildiyse kurum da seçilmelidir."})

    def __str__(self):
        return f"{self.adet} × {self.tas_tipi}"
