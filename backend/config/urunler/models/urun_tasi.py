from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class UrunTasi(models.Model):
    """Ürüne ait bir taş satırı. Birden fazla taş varsa birden fazla satır girilir.

    4C ve sertifika alanları şimdilik açıklayıcıdır, fiyatı etkilemez; taş bedelini
    tedarikçi girer (`bedel`).

    Tasarım notları:
    - Değerli taş tespiti artık `TasTipi.degerli` alanından okunur; string eşleşmesi
      kaldırıldı. Böylece yeni taş tipleri, çoklu dil ve yazım farklılıkları sorun
      çıkarmaz.
    - `self.tas_tipi` FK'sine yalnızca gerçekten ihtiyaç duyulduğunda dokunulur;
      `tas_tipi_id` üzerinden tek kolon sorgusu yapılır.
    - Sertifika kuralları çift yönlü kontrol edilir (no ↔ kurum).
    """

    urun = models.ForeignKey(
        "urunler.Urun", verbose_name="Ürün", related_name="taslar", on_delete=models.CASCADE,
    )
    tas_tipi = models.ForeignKey(
        "urunler.TasTipi", verbose_name="Taş tipi", on_delete=models.PROTECT,
    )
    adet = models.PositiveIntegerField("Adet", default=1)
    karat = models.DecimalField(
        "Toplam karat", max_digits=7, decimal_places=3, null=True, blank=True,
        help_text="Toplam taş ağırlığı",
    )
    bedel = models.DecimalField("Taş bedeli (TL)", max_digits=14, decimal_places=2, default=0)

    kesim = models.ForeignKey(
        "urunler.TasKesimi", verbose_name="Kesim", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    mihlama_tipi = models.ForeignKey(
        "urunler.MihlamaTipi", verbose_name="Mıhlama tipi", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    mensei = models.ForeignKey(
        "urunler.TasMensei", verbose_name="Menşei", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    berraklik = models.ForeignKey(
        "urunler.Berraklik", verbose_name="Berraklık", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    renk_derecesi = models.ForeignKey(
        "urunler.RenkDerecesi", verbose_name="Renk derecesi", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    kesim_kalitesi = models.ForeignKey(
        "urunler.KesimKalitesi", verbose_name="Kesim kalitesi", null=True, blank=True,
        on_delete=models.PROTECT,
    )
    sertifika_kurumu = models.ForeignKey(
        "urunler.SertifikaKurumu", verbose_name="Sertifika kurumu", null=True, blank=True,
        on_delete=models.PROTECT,
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
        errors = {}

        # 1) Sertifika çift yönlü kontrol: no ↔ kurum
        if self.sertifika_no and not self.sertifika_kurumu_id:
            errors["sertifika_kurumu"] = "Sertifika numarası girildiyse kurum da seçilmelidir."
        if self.sertifika_kurumu_id and not (self.sertifika_no or "").strip():
            errors["sertifika_no"] = "Sertifika kurumu seçildiyse sertifika numarası boş bırakılamaz."

        # 2) Değerli taşlarda karat zorunluluğu — artık tek alan kontrolü.
        if self.tas_tipi_id:
            degerli = (
                type(self.tas_tipi)
                .objects
                .filter(pk=self.tas_tipi_id)
                .values_list("degerli", flat=True)
                .first()
            )
            if degerli and (self.karat is None or self.karat <= 0):
                errors["karat"] = (
                    "Değerli taşlarda toplam karat değeri sıfırdan büyük olmalıdır."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        tas_adi = getattr(self.tas_tipi, "ad", "Taş")
        karat_str = f" ({self.karat} Ct)" if self.karat else ""
        return f"{self.adet} × {tas_adi}{karat_str}"