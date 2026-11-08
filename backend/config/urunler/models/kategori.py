from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Kategori(models.Model):
    """
    E-ticaret Kategori Ağacı Modeli.
    UX, SEO, Görsel Desteği ve Öne Çıkarma (Popüler) kriterlerini tam olarak karşılar.

    Tasarım notları:
    - Ağaç gezinmesi her yerde `ust_id` + tek sorgu ile yapılır (N+1 yok).
    - Döngü koruması tek bir yardımcıda (`_ata_zinciri`) toplanmıştır; `clean`,
      `derinlik` ve `__str__` aynı mantığı kullanır.
    - `save()` artık `full_clean()` çağırmaz. Validasyon `clean()`'e ve servis/
      form katmanına bırakılmıştır; böylece `bulk_create`, `QuerySet.update`
      ve veri migration'ları engellenmez.
    """

    MAKS_DERINLIK = 3

    # --- Temel Yapı ---
    kod = models.CharField("Kategori Kodu", max_length=30, unique=True)
    ad = models.CharField("Kategori Adı", max_length=80)
    slug = models.SlugField(
        "URL Slug", max_length=100, unique=True, null=True, blank=True,
        help_text="Boş bırakılırsa isimden otomatik üretilir. SEO dostu URL'ler için zorunludur.",
    )

    ust = models.ForeignKey(
        "self", verbose_name="Üst Kategori", related_name="alt_kategoriler",
        null=True, blank=True, on_delete=models.PROTECT,
        help_text="Eğer boşsa bu bir ana kategoridir.",
    )
    fiyat_grubu = models.ForeignKey(
        "tanimlar.FiyatGrubu", verbose_name="Fiyat Grubu", related_name="kategoriler",
        null=True, blank=True, on_delete=models.PROTECT,
        help_text="Ana kategoride zorunlu. Alt kategoride boş bırakılırsa üst kategorinin grubu miras alınır.",
    )
    sira = models.PositiveIntegerField(
        "Görüntüleme Sırası", default=0,
        help_text="Menüde küçük olan sayı önce listelenir.",
    )
    aktif = models.BooleanField("Aktif mi?", default=True)
    dahili = models.BooleanField(
        "Dahili mi?", default=False,
        help_text="İşaretliyse kategori vitrine ve API'ye çıkmaz, sadece platform içi muhasebe/raporlamada kullanılır.",
    )

    # --- UX ve Tasarım Geliştirmeleri ---
    one_cikan = models.BooleanField(
        "Öne Çıkan / Popüler Kategori", default=False,
        help_text="Menünün en üstünde veya ana sayfada popüler başlıklar olarak vurgulanır.",
    )
    gorsel = models.ImageField(
        "Kategori Görseli", upload_to="kategoriler/resimler/", null=True, blank=True,
        help_text="Kategori sayfalarının tepesinde veya mega menülerde gösterilecek yüksek çözünürlüklü resim.",
    )
    ikon = models.CharField(
        "Menü İkon Kodu", max_length=50, null=True, blank=True,
        help_text="Mobil menülerde kategori adının yanında çıkacak ikon kodu (Örn: fa-gem, fas fa-tshirt).",
    )

    # --- SEO ve Rehberlik İçerikleri ---
    seo_baslik = models.CharField(
        "SEO Başlığı (Meta Title)", max_length=150, null=True, blank=True,
        help_text="Tarayıcı sekmesinde görünecek başlık. Boşsa kategori adı kullanılır.",
    )
    seo_aciklama = models.TextField(
        "SEO / Kategori Alt Açıklama Metni", blank=True, null=True,
        help_text="Kategori sayfasının en altında listelenecek, arama motorlarını besleyen rehber yazı.",
    )

    # --- Pazaryeri Entegrasyonları ---
    pazaryeri_kategorisi = models.CharField(
        "Pazaryeri Kategorisi (Trendyol/Hepsiburada)", max_length=255, blank=True, null=True,
        help_text="Pazaryeri kategori ağacıyla birebir eşleştirme için (Örn: Takı & Mücevher > Kolye).",
    )

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ["sira", "ad"]

    # ------------------------------------------------------------------ #
    # Ağaç yardımcıları
    # ------------------------------------------------------------------ #
    def _ata_zinciri(self, baslangic_ust_id=None):
        """
        `self`'ten köke kadar üst kategorileri tek sorguda döner.

        `baslangic_ust_id` verilirse (form'da `ust` henüz DB'ye yazılmamışken),
        zincir o üst üzerinden yürür. Aksi halde `self.ust_id` kullanılır.

        Döngü korumalıdır: döngüye girilirse zincir orada kesilir ve elde edilen
        kısmi zincir döner. Her eleman `(pk, ad)` çiftidir.
        """
        zincir = []
        # Sonsuz döngüyü önlemek için ziyaret edilen pk'lar (self.pk dahil değil —
        # döngü tespitinde self.pk zincirde görünebilmeli)
        ziyaret = set()

        mevcut_ust_id = baslangic_ust_id if baslangic_ust_id is not None else self.ust_id

        while mevcut_ust_id is not None and mevcut_ust_id not in ziyaret:
            ziyaret.add(mevcut_ust_id)
            kayit = (
                Kategori.objects
                .filter(pk=mevcut_ust_id)
                .values("pk", "ad", "ust_id")
                .first()
            )
            if kayit is None:
                break
            zincir.append((kayit["pk"], kayit["ad"]))
            mevcut_ust_id = kayit["ust_id"]

        return zincir

    def derinlik(self, baslangic_ust_id=None):
        """Kategorinin ağaçtaki derinliği (kendisi dahil). Döngü korumalıdır."""
        return 1 + len(self._ata_zinciri(baslangic_ust_id))

    def alt_agac_yuksekligi(self) -> int:
        """Bu düğüm dahil alt ağaç yüksekliği (yaprak = 1). K-016."""
        if not self.pk:
            return 1
        from collections import deque

        max_h = 1
        kuyruk = deque([(self.pk, 1)])
        while kuyruk:
            pk, h = kuyruk.popleft()
            max_h = max(max_h, h)
            for child_id in (
                Kategori.objects.filter(ust_id=pk).values_list("pk", flat=True)
            ):
                kuyruk.append((child_id, h + 1))
        return max_h

    def etkin_fiyat_grubu(self):
        """Mevcut kategoride yoksa üst kategorilerin fiyat grubunu miras alır."""
        # Önce kendi fiyat grubu
        if self.fiyat_grubu_id:
            return self.fiyat_grubu

        # Üstlerin fiyat grubunu tek sorguda çek (kendi pk'si hariç)
        ziyaret = {self.pk} if self.pk else set()
        mevcut_ust_id = self.ust_id
        while mevcut_ust_id is not None and mevcut_ust_id not in ziyaret:
            ziyaret.add(mevcut_ust_id)
            kayit = (
                Kategori.objects
                .filter(pk=mevcut_ust_id)
                .values("fiyat_grubu_id", "ust_id")
                .first()
            )
            if kayit is None:
                return None
            if kayit["fiyat_grubu_id"]:
                # Grubu döndürmek için FK objesine ihtiyacımız var
                return self.__class__.fiyat_grubu.field.related_model.objects.get(pk=kayit["fiyat_grubu_id"])
            mevcut_ust_id = kayit["ust_id"]
        return None

    # ------------------------------------------------------------------ #
    # Validasyon
    # ------------------------------------------------------------------ #
    def clean(self):
        super().clean()
        errors = {}

        # 1) URL için otomatik slug üretimi
        if not self.slug and self.ad:
            self.slug = slugify(self.ad)

        # 2) SEO teknik fallback (K-015) — pazarlama metni üretilmez
        from urunler.services.seo_servisi import teknik_baslik

        if not self.seo_baslik and self.ad:
            self.seo_baslik = teknik_baslik(self.ad, max_len=150)

        # 3) Üst kategori varsa döngü ve derinlik kontrolü
        if self.ust_id:
            # 3a) Kendisini üst yapamaz
            if self.pk and self.ust_id == self.pk:
                errors["ust"] = "Bir kategori kendisinin altına konamaz."

            # 3b) Ataları arasında kendisi var mı? (döngü)
            # `ust_id` üzerinden yürü; `self.ust`'a dokunma (form'da yeni değer taşınmamış olabilir)
            elif self.pk:
                atalar = self._ata_zinciri(baslangic_ust_id=self.ust_id)
                ata_pk_listesi = [pk for pk, _ in atalar]
                if self.pk in ata_pk_listesi:
                    errors["ust"] = (
                        "Bir kategori, alt kategorisinin altına taşınarak döngüsel ilişki oluşturamaz."
                    )

            # 3c) Maksimum seviye — alt ağaç yüksekliği dahil (K-016)
            if "ust" not in errors:
                yeni_derinlik = self.derinlik(baslangic_ust_id=self.ust_id)
                yukseklik = self.alt_agac_yuksekligi() if self.pk else 1
                if yeni_derinlik + yukseklik - 1 > self.MAKS_DERINLIK:
                    errors["ust"] = (
                        f"Kategori ağacı (alt dallar dahil) en fazla {self.MAKS_DERINLIK} "
                        f"seviye olabilir (Örn: Ana > Alt > En Alt)."
                    )

        # 4) İş kuralı: Ana kategoride fiyat grubu zorunlu
        elif not self.fiyat_grubu_id:
            errors["fiyat_grubu"] = "Ana kategoriler için fiyat grubu seçilmesi zorunludur."

        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------ #
    # Kayıt
    # ------------------------------------------------------------------ #
    def save(self, *args, **kwargs):
        from urunler.services.seo_servisi import teknik_baslik

        if not self.slug and self.ad:
            self.slug = slugify(self.ad)

        if not self.seo_baslik and self.ad:
            self.seo_baslik = teknik_baslik(self.ad, max_len=150)

        # DİKKAT: `full_clean()` burada BİLİNÇLİ olarak çağrılmıyor.
        # Validasyon `clean()`'e ve form/servis katmanına bırakıldı.
        # Böylece `bulk_create`, `QuerySet.update` ve veri migration'ları çalışır.
        super().save(*args, **kwargs)

    def __str__(self):
        # Hiyerarşik isim: kökten kendine doğru
        parcalar = [self.ad]
        parcalar.extend(ad for _, ad in self._ata_zinciri())
        return " > ".join(reversed(parcalar))