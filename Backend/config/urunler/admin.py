from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from . import servisler
from .models import (
    Berraklik, Kategori, KesimKalitesi, Koleksiyon, KopcaTipi, MihlamaTipi, OlcuDegeri, OzelGun,
    Renk, RenkDerecesi, SertifikaKurumu, Stil, TasKesimi, TasMensei, TasTipi, Teknik, Urun,
    UrunKanal, UrunTasi, Varyant, YasGrubu, ZincirTipi,
)

# --- basit seçim listeleri -------------------------------------------------
BASIT_LISTELER = [
    Koleksiyon, Renk, YasGrubu, Teknik, Stil, OzelGun, ZincirTipi, KopcaTipi, TasTipi,
    TasKesimi, MihlamaTipi, TasMensei, SertifikaKurumu, Berraklik, RenkDerecesi, KesimKalitesi,
]


class BasitListeAdmin(admin.ModelAdmin):
    list_display = ("ad", "kod", "sira", "aktif")
    list_editable = ("sira", "aktif")
    list_filter = ("aktif",)
    search_fields = ("ad", "kod")


for _model in BASIT_LISTELER:
    admin.site.register(_model, BasitListeAdmin)


@admin.register(OlcuDegeri)
class OlcuDegeriAdmin(admin.ModelAdmin):
    list_display = ("tip", "deger", "sira", "aktif")
    list_editable = ("sira", "aktif")
    list_filter = ("tip", "aktif")
    search_fields = ("deger",)


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("__str__", "kod", "fiyat_grubu", "sira", "aktif", "dahili")
    list_filter = ("aktif", "dahili", "fiyat_grubu")
    search_fields = ("ad", "kod")
    list_select_related = ("ust", "ust__ust", "fiyat_grubu")


# --- ürün ------------------------------------------------------------------
class VaryantInline(admin.TabularInline):
    model = Varyant
    extra = 1
    fields = ("sku", "tedarikci_sku", "renk", "beden", "gram", "sabit_fiyat", "ek_bedel", "stok", "benzersiz_parca", "aktif")
    readonly_fields = ("sku",)


class UrunTasiInline(admin.TabularInline):
    model = UrunTasi
    extra = 0


class UrunKanalInline(admin.TabularInline):
    model = UrunKanal
    extra = 0


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ("platform_kodu", "ad", "tedarikci", "kategori", "ayar", "fiyat_tipi", "onay_durumu", "yayin_durumu")
    list_filter = ("onay_durumu", "yayin_durumu", "fiyat_tipi", "temin_tipi", "kategori", "tedarikci")
    search_fields = ("platform_kodu", "ad", "tedarikci_urun_kodu")
    list_select_related = ("tedarikci", "kategori", "ayar", "ayar__metal")
    # Durum alanları yalnızca aşağıdaki işlemlerle (servisler.py) değişir.
    readonly_fields = (
        "platform_kodu", "onay_durumu", "yayin_durumu",
        "olusturan_kullanici", "onaylayan_kullanici", "onay_zamani",
    )
    filter_horizontal = ("teknikler", "stiller", "ozel_gunler")
    inlines = [VaryantInline, UrunTasiInline, UrunKanalInline]
    actions = ["onaya_gonder", "onayla", "reddet", "yayina_al", "pasife_al"]
    fieldsets = (
        ("Temel", {"fields": ("platform_kodu", "tedarikci", "tedarikci_urun_kodu", "ad", "aciklama", "kategori")}),
        ("Fiyat ve temin", {"fields": ("ayar", "fiyat_tipi", "temin_tipi", "termin_gun")}),
        ("Varyant eksenleri", {"fields": ("renk_ekseni", "olcu_tipi")}),
        ("Vitrin nitelikleri", {
            "classes": ("collapse",),
            "fields": ("koleksiyon", "hedef_kitle", "yas_grubu", "yuzey", "zincir_tipi", "kopca_tipi",
                       "teknikler", "stiller", "ozel_gunler"),
        }),
        ("Onay ve yayın", {"fields": ("onay_durumu", "red_nedeni", "yayin_durumu",
                                      "olusturan_kullanici", "onaylayan_kullanici", "onay_zamani")}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.olusturan_kullanici = request.user
        super().save_model(request, obj, form, change)

    def _toplu(self, request, queryset, islem, sonuc, **kwargs):
        basarili, hatalar = 0, []
        for urun in queryset:
            try:
                islem(urun, request.user, **kwargs)
                basarili += 1
            except ValidationError as e:
                hatalar.append(f"{urun.platform_kodu}: {'; '.join(e.messages)}")
        if basarili:
            self.message_user(request, f"{basarili} ürün {sonuc}.")
        for h in hatalar:
            self.message_user(request, h, messages.WARNING)

    @admin.action(description="Onaya gönder")
    def onaya_gonder(self, request, queryset):
        self._toplu(request, queryset, servisler.onaya_gonder, "onaya gönderildi")

    @admin.action(description="Onayla")
    def onayla(self, request, queryset):
        self._toplu(request, queryset, servisler.onayla, "onaylandı")

    @admin.action(description="Reddet (red nedeni ürün ekranında önceden yazılmış olmalı)")
    def reddet(self, request, queryset):
        basarili, hatalar = 0, []
        for urun in queryset:
            try:
                servisler.reddet(urun, request.user, urun.red_nedeni)
                basarili += 1
            except ValidationError as e:
                hatalar.append(f"{urun.platform_kodu}: {'; '.join(e.messages)}")
        if basarili:
            self.message_user(request, f"{basarili} ürün reddedildi.")
        for h in hatalar:
            self.message_user(request, h, messages.WARNING)

    @admin.action(description="Yayına al (aktif)")
    def yayina_al(self, request, queryset):
        self._toplu(request, queryset, servisler.yayina_al, "yayına alındı")

    @admin.action(description="Pasife al")
    def pasife_al(self, request, queryset):
        self._toplu(request, queryset, servisler.pasife_al, "pasife alındı")


@admin.register(Varyant)
class VaryantAdmin(admin.ModelAdmin):
    list_display = ("sku", "urun", "renk", "beden", "gram", "sabit_fiyat", "stok", "aktif")
    list_filter = ("aktif", "benzersiz_parca", "renk")
    search_fields = ("sku", "tedarikci_sku", "urun__ad", "urun__platform_kodu")
    list_select_related = ("urun", "renk", "beden")
    readonly_fields = ("sku",)
