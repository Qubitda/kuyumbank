from django.contrib import admin

from ..models import DovizKuru, MetalKuru


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
    search_fields = ("metal__ad", "metal__kod")
    list_select_related = ("metal", "giren_kullanici")
    autocomplete_fields = ("metal",)


@admin.register(DovizKuru)
class DovizKuruAdmin(KurAdminTaban):
    list_display = ("para_birimi", "kur", "zaman", "kaynak", "giren_kullanici")
    list_filter = ("para_birimi", "kaynak")
    search_fields = ("para_birimi",)
    list_select_related = ("giren_kullanici",)


