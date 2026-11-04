from django.core.exceptions import ValidationError
from django.db import models


class Kategori(models.Model):
    """Kategori ağacı: Kolye > Tek Taş Kolye gibi. En fazla 3 seviye."""

    MAKS_DERINLIK = 3

    kod = models.CharField("Kod", max_length=30, unique=True)
    ad = models.CharField("Ad", max_length=80)
    ust = models.ForeignKey(
        "self", verbose_name="Üst kategori", related_name="alt_kategoriler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    fiyat_grubu = models.ForeignKey(
        "tanimlar.FiyatGrubu", verbose_name="Fiyat grubu", related_name="kategoriler",
        null=True, blank=True, on_delete=models.PROTECT,
        help_text="Ana kategoride zorunlu. Alt kategoride boşsa üst kategorininki geçerlidir.",
    )
    sira = models.PositiveIntegerField("Sıra", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    dahili = models.BooleanField(
        "Dahili", default=False,
        help_text="İşaretliyse kategori müşteriye, vitrine ve API'ye çıkmaz (yalnızca platform içi kullanım).",
    )

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ["sira", "ad"]

    def derinlik(self):
        seviye, k = 1, self
        while k.ust_id:
            k = k.ust
            seviye += 1
        return seviye

    def etkin_fiyat_grubu(self):
        k = self
        while k is not None:
            if k.fiyat_grubu_id:
                return k.fiyat_grubu
            k = k.ust
        return None

    def clean(self):
        super().clean()
        errors = {}
        if self.ust_id:
            if self.pk:
                k = self.ust
                while k is not None:
                    if k.pk == self.pk:
                        errors["ust"] = "Bir kategori kendisinin ya da alt kategorisinin altına konamaz."
                        break
                    k = k.ust
            if "ust" not in errors and self.derinlik() > self.MAKS_DERINLIK:
                errors["ust"] = f"Kategori ağacı en fazla {self.MAKS_DERINLIK} seviye olabilir."
        elif not self.fiyat_grubu_id:
            errors["fiyat_grubu"] = "Ana kategori için fiyat grubu seçilmelidir."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        yol, k = [self.ad], self
        while k.ust_id:
            k = k.ust
            yol.append(k.ad)
        return " > ".join(reversed(yol))
