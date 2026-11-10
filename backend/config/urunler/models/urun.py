from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Urun(models.Model):
    """Müşterinin vitrinde gördüğü model (ör. "Tek taş yüzük").

    Tasarım notları:
    - `onay_durumu` ve `yayin_durumu` yalnızca `urunler.servisler` üzerinden
      değiştirilmelidir. `save()` bu iki alanı eski değerle karşılaştırır ve
      servis dışından doğrudan değişimi reddeder. (Acil durumlar için
      `Urun.objects.filter(pk=...).update(...)` her zaman kullanılabilir; bu
      kısıt yalnızca model `save()` çağrısına uygulanır.)
    - SEO alanları boş bırakılırsa `save()` içinde otomatik üretilir.
    - `full_clean()` çağrısı `save()`'te bilinçli olarak yapılmaz; form/servis
      katmanı sorumludur. Bu sayede veri migration'ları engellenmez.
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
    KIMLIK_SINIFI = [
        ("A", "Seri / sertifikalı"),
        ("B", "Markalı / model kodlu"),
        ("C", "Jenerik kalıp"),
    ]

    platform_kodu = models.CharField(
        "Platform ürün kodu", max_length=20, unique=True, blank=True,
        help_text="Otomatik üretilir. Müşteriye ve API'ye bu kod gider.",
    )

    olusturan_firma = models.ForeignKey(
        "firmalar.Firma",
        verbose_name="Oluşturan firma",
        related_name="olusturdugu_katalog_urunleri",
        on_delete=models.PROTECT,
        help_text="Denetim alanı. Alıcıya hiçbir yüzeyde gösterilmez (ADR-0005 K6).",
    )
    kimlik_sinifi = models.CharField(
        "Kimlik sınıfı", max_length=1, choices=KIMLIK_SINIFI, default="C",
    )
    kimlik_anahtari = models.CharField(
        "Kimlik anahtarı",
        max_length=255,
        blank=True,
        default="",
        help_text="A/B: sertifika/parça veya marka+model(+GTIN). C: platform spec anahtarı.",
    )

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
    fiyat_kaynagi = models.CharField(
        "Fiyat kaynağı",
        max_length=16,
        choices=[
            ("CANLI_PIYASA", "Canlı piyasa"),
            ("MANUEL_GIRIS", "Manuel giriş"),
            ("MIRAS", "Miras (ayar→politika)"),
        ],
        default="MIRAS",
        help_text="ADR-0018 CP-1: ürün → ayar → politika.",
    )
    temin_tipi = models.CharField("Temin tipi", max_length=15, choices=TEMIN_TIPI, default="hazir")
    termin_gun = models.PositiveIntegerField("Termin (gün)", null=True, blank=True)

    renk_ekseni = models.BooleanField(
        "Renk seçenekli", default=False,
        help_text="İşaretliyse her varyantın rengi zorunlu (sarı/beyaz/rose gibi).",
    )

    olcu_tipi = models.CharField(
        "Ölçü tipi", max_length=15, blank=True,
        choices=[
            ("yuzuk_no", "Yüzük numarası"),
            ("bilezik_boyu", "Bilezik boyu (cm)"),
            ("zincir_uzunlugu", "Zincir / kolye uzunluğu (cm)"),
            ("bileklik_boyu", "Bileklik boyu (cm)"),
        ],
        help_text="Boşsa ürün bedensizdir. Doluysa her varyantın bu tipte bir ölçüsü olmalı.",
    )

    # --- vitrin nitelikleri ---
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
    teknikler = models.ManyToManyField(
        "urunler.Teknik", verbose_name="Teknikler", related_name="urunler", blank=True,
    )
    stiller = models.ManyToManyField(
        "urunler.Stil", verbose_name="Stiller", related_name="urunler", blank=True,
    )
    ozel_gunler = models.ManyToManyField(
        "urunler.OzelGun", verbose_name="Özel günler", related_name="urunler", blank=True,
    )

    # --- SEO ---
    slug = models.SlugField(
        "URL Adresi (Slug)", max_length=160, unique=True, blank=True,
        help_text="Küçük harf, tireli ve Türkçe karaktersiz benzersiz sayfa adresi. Boş bırakılırsa otomatik üretilir.",
    )
    meta_baslik = models.CharField(
        "Meta Başlık (SEO)", max_length=70, blank=True,
        help_text="Google arama sonuçlarındaki mavi başlık. Boş bırakılırsa otomatik oluşturulur.",
    )
    meta_aciklama = models.TextField(
        "Meta Açıklama (SEO)", max_length=160, blank=True,
        help_text="Google sonuçlarındaki özet metin. En fazla 160 karakter olmalıdır.",
    )
    canonical_url = models.URLField(
        "Canonical URL", blank=True, null=True,
        help_text="Kopya içerik algoritmasını önlemek için asıl ürünün tam internet adresi.",
    )
    gorsel_alt_metni = models.TextField(
        "Görsel Alt Metni (SEO)", blank=True,
        help_text="Görsellerin arama motorları tarafından indekslenmesi için açıklama metinleri.",
    )

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
        permissions = [
            ("submit_urun", "Ürünü onaya gönderebilir"),
            ("approve_urun", "Ürünü onaylayabilir / reddedebilir"),
            ("publish_urun", "Ürünü yayına alabilir"),
        ]
        indexes = [
            models.Index(fields=["olusturan_firma", "onay_durumu"]),
            models.Index(fields=["yayin_durumu", "kategori"]),
            models.Index(fields=["kimlik_sinifi", "kimlik_anahtari"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(yayin_durumu__in=["aktif", "yakinda"]) | models.Q(onay_durumu="onayli"),
                name="urun_yayin_icin_onay",
            ),
            models.CheckConstraint(
                condition=~models.Q(onay_durumu="onayli") | (
                    models.Q(onaylayan_kullanici__isnull=False) & models.Q(onay_zamani__isnull=False)
                ),
                name="urun_onayli_icin_onaylayan_ve_zaman",
            ),
            models.UniqueConstraint(
                fields=["kimlik_sinifi", "kimlik_anahtari"],
                condition=(
                    models.Q(kimlik_sinifi__in=["A", "B"])
                    & ~models.Q(kimlik_anahtari="")
                    & ~models.Q(onay_durumu="reddedildi")
                ),
                name="urun_kimlik_ab_anahtar_uniq",
            ),
        ]

    # ------------------------------------------------------------------ #
    # Yardımcılar
    # ------------------------------------------------------------------ #
    @property
    def metal(self):
        return self.ayar.metal

    def _eski_deger(self, alan_adi):
        """DB'deki mevcut değeri döner (yeni kayıtta None)."""
        if self.pk is None:
            return None
        return (
            type(self)
            .objects
            .filter(pk=self.pk)
            .values_list(alan_adi, flat=True)
            .first()
        )

    # ------------------------------------------------------------------ #
    # Validasyon
    # ------------------------------------------------------------------ #
    def clean(self):
        super().clean()
        errors = {}

        # 1) Metal gram bazlı değilse fiyat tipi sabit olmalı
        if self.ayar_id and hasattr(self.ayar, "metal") and not getattr(
            self.ayar.metal, "gram_bazli", True
        ) and self.fiyat_tipi != "sabit":
            errors["fiyat_tipi"] = (
                f"{self.ayar.metal.ad} gram bazlı değildir; fiyat tipi 'Sabit fiyat' olmalı."
            )

        # 2) Siparişe özel termin
        if self.temin_tipi == "siparis_ozel" and not self.termin_gun:
            errors["termin_gun"] = "Siparişe özel üründe termin süresi (gün) zorunludur."

        # 3) Reddedilen ürün için neden zorunlu
        if self.onay_durumu == "reddedildi" and not (self.red_nedeni or "").strip():
            errors["red_nedeni"] = "Reddedilen ürün için red nedeni yazılmalıdır."

        # 4) Yayın için onay zorunlu
        if self.yayin_durumu in ("aktif", "yakinda") and self.onay_durumu != "onayli":
            errors["yayin_durumu"] = "Yalnızca onaylı ürün yayına alınabilir."

        # 5) Kategori fiyat grubu tanımlı olmalı
        if self.kategori_id and hasattr(self.kategori, "etkin_fiyat_grubu"):
            if self.kategori.etkin_fiyat_grubu() is None:
                errors["kategori"] = "Bu kategorinin (ve üst kategorilerinin) fiyat grubu tanımlı değil."

        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------ #
    # Kayıt
    # ------------------------------------------------------------------ #
    def save(self, *args, **kwargs):
        # 1) Onay/yayın alanlarının doğrudan değiştirilmesini engelle.
        #    Sadece servisler.py üzerinden değişmeli. `QuerySet.update` her zaman
        #    çalışır (bilinçli kaçış kapısı); bu kısıt yalnızca model.save() içindir.
        if self.pk is not None:
            eski_onay = self._eski_deger("onay_durumu")
            eski_yayin = self._eski_deger("yayin_durumu")
            if eski_onay is not None and eski_onay != self.onay_durumu:
                raise ValidationError(
                    {"onay_durumu": "Onay durumu yalnızca servisler.onayla/reddet/onaya_gonder ile değiştirilebilir."}
                )
            if eski_yayin is not None and eski_yayin != self.yayin_durumu:
                raise ValidationError(
                    {"yayin_durumu": "Yayın durumu yalnızca servisler.yayina_al/pasife_al ile değiştirilebilir."}
                )

        # 2) SEO teknik fallback (K-015) — pazarlama metni üretilmez
        from urunler.services.seo_servisi import teknik_aciklama_kirp, teknik_baslik

        if not self.slug and self.ad:
            self.slug = slugify(self.ad)

        if not self.meta_baslik and self.ad:
            self.meta_baslik = teknik_baslik(self.ad, max_len=70)

        if not self.meta_aciklama:
            self.meta_aciklama = teknik_aciklama_kirp(self.aciklama, max_len=160)

        # 3) Kaydet
        yeni = self.pk is None
        super().save(*args, **kwargs)

        # 4) platform_kodu üret
        if yeni and not self.platform_kodu:
            self.platform_kodu = f"URN-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(platform_kodu=self.platform_kodu)

    def __str__(self):
        return f"{self.platform_kodu or 'yeni'} — {self.ad}"