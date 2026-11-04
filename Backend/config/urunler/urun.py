from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .olcu import OlcuDegeri


class Urun(models.Model):
    """Müşterinin vitrinde gördüğü model (ör. "Tek taş yüzük").

    Gram, stok ve fiyat Varyant'tadır. Metal ve ayar üründe tutulur: farklı ayar
    farklı üründür, böylece bir ürünün tüm varyantları aynı sözleşme kalemiyle
    fiyatlanır. Metal, ayardan türetilir (ayrı alan yok, çelişme olmaz).
    """

    ONAY = [
        ("taslak", "Taslak"),
        ("onay_bekliyor", "Onay bekliyor"),
        ("onayli", "Onaylı"),
        ("reddedildi", "Reddedildi"),
    ]
    YAYIN = [("pasif", "Pasif"), ("aktif", "Aktif"), ("yakinda", "Yakında")]
    FIYAT_TIPI = [("gram", "Gram bazlı"), ("sabit", "Sabit fiyat")]
    TEMIN_TIPI = [("hazir", "Hazır ürün"), ("siparis_ozel", "Siparişe özel")]
    HEDEF_KITLE = [("kadin", "Kadın"), ("erkek", "Erkek"), ("cocuk", "Çocuk"), ("unisex", "Unisex")]
    YUZEY = [("mat", "Mat"), ("parlak", "Parlak")]

    platform_kodu = models.CharField(
        "Platform ürün kodu", max_length=20, unique=True, blank=True, editable=False,
        help_text="Otomatik üretilir. Müşteriye ve API'ye bu kod gider.",
    )
    tedarikci = models.ForeignKey(
        "firmalar.Firma", verbose_name="Tedarikçi", related_name="urunler",
        on_delete=models.PROTECT, limit_choices_to={"tedarikci_mi": True},
        help_text="Müşteriye hiçbir ekranda gösterilmez.",
    )
    tedarikci_urun_kodu = models.CharField("Tedarikçi ürün kodu", max_length=50, blank=True)

    ad = models.CharField("Ürün adı", max_length=150)
    aciklama = models.TextField("Açıklama", blank=True)

    kategori = models.ForeignKey(
        "urunler.Kategori", verbose_name="Kategori", related_name="urunler",
        on_delete=models.PROTECT, limit_choices_to={"aktif": True},
    )
    ayar = models.ForeignKey(
        "tanimlar.AyarMilyem", verbose_name="Ayar", related_name="urunler",
        on_delete=models.PROTECT, help_text="Metal buradan belirlenir. Çelik için Ayarsız seçilir.",
    )
    fiyat_tipi = models.CharField("Fiyat tipi", max_length=10, choices=FIYAT_TIPI, default="gram")
    temin_tipi = models.CharField("Temin tipi", max_length=15, choices=TEMIN_TIPI, default="hazir")
    termin_gun = models.PositiveIntegerField("Termin (gün)", null=True, blank=True)

    # --- varyant eksenleri (Medusa'daki ProductOption karşılığı) ---
    renk_ekseni = models.BooleanField(
        "Renk seçenekli", default=False,
        help_text="İşaretliyse her varyantın rengi zorunlu (sarı/beyaz/rose gibi).",
    )
    olcu_tipi = models.CharField(
        "Ölçü tipi", max_length=15, choices=OlcuDegeri.TIP, blank=True,
        help_text="Boşsa ürün bedensizdir. Doluysa her varyantın bu tipte bir ölçüsü olmalı.",
    )

    # --- vitrin nitelikleri (hepsi opsiyonel, filtrede kullanılır) ---
    koleksiyon = models.ForeignKey(
        "urunler.Koleksiyon", verbose_name="Koleksiyon", related_name="urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    hedef_kitle = models.CharField("Hedef kitle", max_length=10, choices=HEDEF_KITLE, blank=True)
    yas_grubu = models.ForeignKey(
        "urunler.YasGrubu", verbose_name="Yaş grubu", related_name="urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    yuzey = models.CharField("Yüzey", max_length=10, choices=YUZEY, blank=True)
    zincir_tipi = models.ForeignKey(
        "urunler.ZincirTipi", verbose_name="Zincir tipi", related_name="urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    kopca_tipi = models.ForeignKey(
        "urunler.KopcaTipi", verbose_name="Kopça tipi", related_name="urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    teknikler = models.ManyToManyField("urunler.Teknik", verbose_name="Teknikler", related_name="urunler", blank=True)
    stiller = models.ManyToManyField("urunler.Stil", verbose_name="Stiller", related_name="urunler", blank=True)
    ozel_gunler = models.ManyToManyField("urunler.OzelGun", verbose_name="Özel günler", related_name="urunler", blank=True)

    # --- onay ve yayın ---
    onay_durumu = models.CharField("Onay durumu", max_length=15, choices=ONAY, default="taslak")
    red_nedeni = models.TextField("Red nedeni", blank=True)
    yayin_durumu = models.CharField("Yayın durumu", max_length=10, choices=YAYIN, default="pasif")

    olusturan_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Oluşturan", related_name="olusturdugu_urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    onaylayan_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Onaylayan", related_name="onayladigi_urunler",
        null=True, blank=True, on_delete=models.PROTECT,
    )
    onay_zamani = models.DateTimeField("Onay zamanı", null=True, blank=True)
    olusturma_zamani = models.DateTimeField(auto_now_add=True)
    guncelleme_zamani = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ["-olusturma_zamani"]
        indexes = [
            models.Index(fields=["tedarikci", "onay_durumu"]),
            models.Index(fields=["yayin_durumu", "kategori"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(yayin_durumu__in=["aktif", "yakinda"]) | models.Q(onay_durumu="onayli"),
                name="urun_yayin_icin_onay",
            ),
            models.CheckConstraint(
                condition=~models.Q(onay_durumu="onayli") | models.Q(onaylayan_kullanici__isnull=False),
                name="urun_onayli_icin_onaylayan",
            ),
        ]

    @property
    def metal(self):
        return self.ayar.metal

    def clean(self):
        super().clean()
        errors = {}
        if self.ayar_id and not self.ayar.metal.gram_bazli and self.fiyat_tipi != "sabit":
            errors["fiyat_tipi"] = f"{self.ayar.metal.ad} gram bazlı değildir; fiyat tipi 'Sabit fiyat' olmalı."
        if self.temin_tipi == "siparis_ozel" and not self.termin_gun:
            errors["termin_gun"] = "Siparişe özel üründe termin süresi (gün) zorunludur."
        if self.onay_durumu == "reddedildi" and not self.red_nedeni.strip():
            errors["red_nedeni"] = "Reddedilen ürün için red nedeni yazılmalıdır."
        if self.yayin_durumu in ("aktif", "yakinda") and self.onay_durumu != "onayli":
            errors["yayin_durumu"] = "Yalnızca onaylı ürün yayına alınabilir."
        if self.kategori_id and self.kategori.etkin_fiyat_grubu() is None:
            errors["kategori"] = "Bu kategorinin (ve üst kategorilerinin) fiyat grubu tanımlı değil."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        yeni = self.pk is None
        super().save(*args, **kwargs)
        if yeni and not self.platform_kodu:
            self.platform_kodu = f"URN-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(platform_kodu=self.platform_kodu)

    def __str__(self):
        return f"{self.platform_kodu or 'yeni'} — {self.ad}"
