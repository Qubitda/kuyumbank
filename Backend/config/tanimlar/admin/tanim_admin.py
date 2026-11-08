from django.contrib import admin

from ..models import FiyatGrubu, SatisKanali


@admin.register(SatisKanali)
class SatisKanaliAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "sira", "aktif", "quote_ttl_saniye")
    list_editable = ("sira", "aktif", "quote_ttl_saniye")
    list_filter = ("aktif",)
    search_fields = ("kod", "ad")


@admin.register(FiyatGrubu)
class FiyatGrubuAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "sira", "aktif")
    list_editable = ("sira", "aktif")
    list_filter = ("aktif",)
    search_fields = ("kod", "ad")
