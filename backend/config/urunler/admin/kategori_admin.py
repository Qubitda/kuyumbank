from django.contrib import admin

from ..models import Kategori, OlcuDegeri

@admin.register(OlcuDegeri)
class OlcuDegeriAdmin(admin.ModelAdmin):
    list_display = ("tip", "deger", "sayisal_deger", "sira", "aktif")
    list_editable = ("sayisal_deger", "sira", "aktif")
    list_filter = ("tip", "aktif")
    search_fields = ("deger", "sayisal_deger", "entegrasyon_kodu")
    list_per_page = 50


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("__str__", "kod", "fiyat_grubu", "derinlik_goster", "sira", "aktif", "dahili", "one_cikan")
    list_editable = ("sira", "aktif", "one_cikan")
    list_filter = ("aktif", "dahili", "one_cikan", "fiyat_grubu")
    search_fields = ("ad", "kod", "slug")
    prepopulated_fields = {"slug": ("ad",)}
    autocomplete_fields = ("ust", "fiyat_grubu")
    readonly_fields = ("derinlik_goster", "etkin_fiyat_grubu_goster")
    list_select_related = ("ust", "ust__ust", "fiyat_grubu")
    list_per_page = 50

    fieldsets = (
        ("Temel", {
            "fields": ("kod", "ad", "slug", "ust", "fiyat_grubu", "sira", "aktif", "dahili", "one_cikan")
        }),
        ("Görsel / Menü", {
            "classes": ("collapse",),
            "fields": ("gorsel", "ikon"),
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("seo_baslik", "seo_aciklama"),
        }),
        ("Pazaryeri", {
            "classes": ("collapse",),
            "fields": ("pazaryeri_kategorisi",),
        }),
        ("Hesaplanan", {
            "classes": ("collapse",),
            "fields": ("derinlik_goster", "etkin_fiyat_grubu_goster"),
        }),
    )

    @admin.display(description="Derinlik")
    def derinlik_goster(self, obj):
        if not obj.pk:
            return "-"
        return obj.derinlik()

    @admin.display(description="Etkin fiyat grubu")
    def etkin_fiyat_grubu_goster(self, obj):
        if not obj.pk:
            return "-"
        grup = obj.etkin_fiyat_grubu()
        return grup if grup else "— (tanımsız)"


