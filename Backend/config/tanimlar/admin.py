from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import AyarMilyem, DovizKuru, FiyatGrubu, KiymetliMetal, MetalKuru, SatisKanali


class AyarMilyemInline(admin.TabularInline):
    model = AyarMilyem
    extra = 0


@admin.register(KiymetliMetal)
class KiymetliMetalAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "gram_bazli")
    inlines = [AyarMilyemInline]


@admin.register(AyarMilyem)
class AyarMilyemAdmin(ImportExportModelAdmin):
    list_display = ("metal", "ayar_kodu", "milyem")
    list_filter = ("metal",)
    search_fields = ("ayar_kodu",)
    list_select_related = ("metal",)


class KurAdminTaban(admin.ModelAdmin):
    """
    Kur kayıtları tarihçedir: eklenir, ama değiştirilmez ve silinmez.
    Hatalı kur, yeni bir kayıtla düzeltilir. Giren kullanıcı otomatik atanır.
    """

    readonly_fields = ("giren_kullanici", "girilme_zamani")
    date_hierarchy = "zaman"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.giren_kullanici = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MetalKuru)
class MetalKuruAdmin(KurAdminTaban):
    list_display = ("metal", "saf_birim_fiyat", "zaman", "kaynak", "giren_kullanici")
    list_filter = ("metal", "kaynak")
    list_select_related = ("metal", "giren_kullanici")


@admin.register(DovizKuru)
class DovizKuruAdmin(KurAdminTaban):
    list_display = ("para_birimi", "kur", "zaman", "kaynak", "giren_kullanici")
    list_filter = ("para_birimi", "kaynak")
    list_select_related = ("giren_kullanici",)


@admin.register(SatisKanali)
class SatisKanaliAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "aktif")
    list_filter = ("aktif",)


@admin.register(FiyatGrubu)
class FiyatGrubuAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "aktif")
    list_filter = ("aktif",)
