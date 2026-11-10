from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class PiyasaUrun(models.Model):
    """Pano kalemi — metal/ayar **Tanımlar**dan FK (yeni metal/ayar burada açılmaz).

    Marj modu globaldir (`PiyasaMarjPolitikasi`); satırda yalnız alış/satış değeri.
    Ham = MetalKuru.saf_birim_fiyat × milyem(ayar|1) × gram; sonra marj + yuvarlama.
    """

    class Grup(models.TextChoices):
        HAS = "HAS", "Has altın & ons"
        GUMUS = "GUMUS", "Gümüş"
        SARRAFIYE = "SARRAFIYE", "Sarrafiye"
        AYAR_GRAM = "AYAR_GRAM", "Ayar / gram"
        DIGER = "DIGER", "Diğer"

    class VaryantEtiket(models.TextChoices):
        YENI = "YENI", "Yeni"
        ESKI = "ESKI", "Eski"

    class Yuvarlama(models.TextChoices):
        YAKIN = "YAKIN", "En yakın"
        YUKARI = "YUKARI", "Yukarı"
        ASAGI = "ASAGI", "Aşağı"

    class Olcek(models.TextChoices):
        GRAM = "GRAM", "Gram"
        ONS = "ONS", "Ons (troy)"
        KG = "KG", "Kilogram"

    class CiktiPb(models.TextChoices):
        TRY = "TRY", "TRY"
        USD = "USD", "USD"

    kod = models.SlugField("Kod", max_length=24, unique=True)
    ad = models.CharField("Ad", max_length=80)
    grup = models.CharField(
        "Grup",
        max_length=16,
        choices=Grup.choices,
        default=Grup.AYAR_GRAM,
        db_index=True,
    )
    varyant_etiket = models.CharField(
        "Varyant",
        max_length=8,
        choices=VaryantEtiket.choices,
        blank=True,
        default="",
        help_text="Sarrafiye yeni/eski; boş = yok.",
    )
    metal = models.ForeignKey(
        "tanimlar.KiymetliMetal",
        verbose_name="Metal (Tanımlar)",
        on_delete=models.PROTECT,
        related_name="piyasa_urunleri",
        help_text="Tanımlar → Kıymetli metaller. Burada yeni metal tanımlanmaz.",
    )
    ayar = models.ForeignKey(
        "tanimlar.AyarMilyem",
        verbose_name="Ayar / milyem (Tanımlar)",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="piyasa_urunleri",
        help_text="Tanımlar → Milyem tablosu. Boş = has (milyem 1). Seçilirse metal ayardan gelir.",
    )
    olcek = models.CharField(
        "Ölçek",
        max_length=8,
        choices=Olcek.choices,
        default=Olcek.GRAM,
        help_text="GRAM / ONS / KG — ham fiyat ölçeği (ADR-0025).",
    )
    cikti_pb = models.CharField(
        "Çıktı PB",
        max_length=3,
        choices=CiktiPb.choices,
        default=CiktiPb.TRY,
        help_text="TRY veya USD (USD için DovizKuru USDTRY gerekir).",
    )
    gram = models.DecimalField(
        "Miktar çarpanı",
        max_digits=12,
        decimal_places=4,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="1 = birim ölçek (1 gr / 1 oz / 1 kg); çeyrek vb. için sabit gram.",
    )
    alis_marj = models.DecimalField(
        "Alış marjı",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="≥0. Mod global politikadan: TL → baz−marj; % → baz×(1−marj/100).",
    )
    satis_marj = models.DecimalField(
        "Satış marjı",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="≥0. Mod global politikadan: TL → baz+marj; % → baz×(1+marj/100).",
    )
    yuvarlama_adimi = models.DecimalField(
        "Yuvarlama adımı (TL)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="0 = yok. Örn. 10 → 6670.",
    )
    yuvarlama_yontemi = models.CharField(
        "Yuvarlama yöntemi",
        max_length=6,
        choices=Yuvarlama.choices,
        default=Yuvarlama.YAKIN,
    )
    sira = models.PositiveIntegerField("Sıra", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    olusturma = models.DateTimeField(auto_now_add=True)
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Piyasa ürünü"
        verbose_name_plural = "Piyasa ürünleri"
        ordering = ["grup", "sira", "kod"]
        permissions = [
            ("manage_piyasa", "Piyasa panosu yönetebilir"),
        ]

    def __str__(self):
        return f"{self.kod} — {self.ad}"

    def clean(self):
        super().clean()
        if self.ayar_id and self.ayar.metal_id and (
            not self.metal_id or self.metal_id != self.ayar.metal_id
        ):
            self.metal_id = self.ayar.metal_id
        if self.alis_marj is not None and self.alis_marj < 0:
            raise ValidationError({"alis_marj": "Alış marjı negatif olamaz."})
        if self.satis_marj is not None and self.satis_marj < 0:
            raise ValidationError({"satis_marj": "Satış marjı negatif olamaz."})

    def save(self, *args, **kwargs):
        if self.ayar_id and self.ayar.metal_id:
            self.metal_id = self.ayar.metal_id
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def etkin_milyem(self) -> Decimal:
        if self.ayar_id:
            return self.ayar.milyem
        return Decimal("1")
