from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models


class Varyant(models.Model):
    """Sepete eklenen, stoku ve ağırlığı olan satış birimi (SKU).

    Varyant = ürünün tanımladığı eksenlerin (renk, ölçü) bir kombinasyonu.
    Beden değişince gram, gram değişince fiyat değişir; bu yüzden gram burada.
    Tekil (eksensiz) ürün de tek bir varyantla temsil edilir.
    """

    urun = models.ForeignKey(
        "urunler.Urun", verbose_name="Ürün", related_name="varyantlar", on_delete=models.CASCADE,
    )
    sku = models.CharField("Platform SKU", max_length=20, unique=True, blank=True, editable=False)
    tedarikci_sku = models.CharField("Tedarikçi SKU", max_length=50, blank=True)

    renk = models.ForeignKey(
        "urunler.Renk", verbose_name="Renk", related_name="varyantlar",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    beden = models.ForeignKey(
        "urunler.OlcuDegeri", verbose_name="Beden / ölçü", related_name="varyantlar",
        null=True, blank=True, on_delete=models.PROTECT,
    )

    gram = models.DecimalField("Gram", max_digits=10, decimal_places=3, null=True, blank=True)
    sabit_fiyat = models.DecimalField(
        "Sabit fiyat (TL)", max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Yalnızca fiyat tipi 'Sabit fiyat' olan ürünlerde.",
    )
    ek_bedel = models.DecimalField(
        "Ek bedel (TL)", max_digits=14, decimal_places=2, default=0,
        help_text="Kutu, sertifika, gravür gibi kalemlerin toplamı.",
    )

    stok = models.PositiveIntegerField("Stok", default=1)
    benzersiz_parca = models.BooleanField(
        "Benzersiz parça", default=False, help_text="Tek adet, tekrar üretilmeyen parça (ör. sertifikalı tek taş).",
    )
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Varyant"
        verbose_name_plural = "Varyantlar"
        ordering = ["urun", "renk", "beden"]
        constraints = [
            # Aynı ürün içinde aynı eksen kombinasyonu iki kez olamaz. NULL'lar
            # PostgreSQL'de birbirinden farklı sayıldığı için dört durum ayrı yazılır.
            models.UniqueConstraint(fields=["urun", "renk", "beden"], name="benzersiz_varyant_renk_beden"),
            models.UniqueConstraint(
                fields=["urun", "beden"], condition=models.Q(renk__isnull=True),
                name="benzersiz_varyant_beden_renksiz",
            ),
            models.UniqueConstraint(
                fields=["urun", "renk"], condition=models.Q(beden__isnull=True),
                name="benzersiz_varyant_renk_bedensiz",
            ),
            models.UniqueConstraint(
                fields=["urun"], condition=models.Q(renk__isnull=True, beden__isnull=True),
                name="benzersiz_varyant_eksensiz",
            ),
            models.CheckConstraint(
                condition=models.Q(gram__isnull=True) | models.Q(gram__gt=0), name="varyant_gram_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(sabit_fiyat__isnull=True) | models.Q(sabit_fiyat__gt=0),
                name="varyant_sabit_fiyat_pozitif",
            ),
            models.CheckConstraint(condition=models.Q(ek_bedel__gte=0), name="varyant_ek_bedel_negatif_degil"),
            models.CheckConstraint(
                condition=~models.Q(benzersiz_parca=True) | models.Q(stok__lte=1),
                name="varyant_benzersiz_parca_stok",
            ),
        ]

    def _urun_veya_none(self):
        try:
            return self.urun
        except ObjectDoesNotExist:
            return None

    def clean(self):
        super().clean()
        urun = self._urun_veya_none()
        if urun is None:
            return
        errors = {}

        # fiyat tipi kuralları
        if urun.fiyat_tipi == "gram":
            if not self.gram:
                errors["gram"] = "Gram bazlı üründe gram zorunludur."
            if self.sabit_fiyat is not None:
                errors["sabit_fiyat"] = "Gram bazlı üründe sabit fiyat girilmez."
        elif urun.fiyat_tipi == "sabit" and not self.sabit_fiyat:
            errors["sabit_fiyat"] = "Sabit fiyatlı üründe sabit fiyat zorunludur."

        # eksen kuralları: ürünün tanımladığı eksenler eksiksiz doldurulmalı
        if urun.renk_ekseni:
            if not self.renk_id:
                errors["renk"] = "Bu ürün renk seçenekli; renk zorunludur."
        elif self.renk_id:
            errors["renk"] = "Bu ürün renk seçenekli değil; renk girilmez."

        if urun.olcu_tipi:
            if not self.beden_id:
                errors["beden"] = f"Bu ürün için '{urun.get_olcu_tipi_display()}' seçilmelidir."
            elif self.beden.tip != urun.olcu_tipi:
                errors["beden"] = f"Bu ürün için '{urun.get_olcu_tipi_display()}' tipinde bir değer seçilmelidir."
        elif self.beden_id:
            errors["beden"] = "Bu ürün bedensiz tanımlı; ölçü girilmez."

        if errors:
            raise ValidationError(errors)

    def tas_bedeli_toplam(self):
        """Ürünün taş satırlarındaki bedellerin toplamı (fiyat motoru kullanır)."""
        return sum((t.bedel for t in self.urun.taslar.all()), Decimal("0"))

    def ek_bedel_toplam(self):
        return self.ek_bedel

    def save(self, *args, **kwargs):
        yeni = self.pk is None
        super().save(*args, **kwargs)
        if yeni and not self.sku:
            self.sku = f"SKU-{self.pk:07d}"
            type(self).objects.filter(pk=self.pk).update(sku=self.sku)

    def __str__(self):
        parca = []
        if self.renk_id:
            parca.append(self.renk.ad)
        if self.beden_id:
            parca.append(self.beden.deger)
        return f"{self.sku or 'yeni'} — {self.urun.ad}" + (f" ({', '.join(parca)})" if parca else "")
