from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from ..models import AyarMilyem, KiymetliMetal


class AyarMilyemInline(admin.TabularInline):
    model = AyarMilyem
    extra = 0
    fields = ("ayar_degeri", "ayar_kodu", "milyem")


@admin.register(KiymetliMetal)
class KiymetliMetalAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "gram_bazli")
    list_filter = ("gram_bazli",)
    search_fields = ("kod", "ad")
    inlines = [AyarMilyemInline]


@admin.register(AyarMilyem)
class AyarMilyemAdmin(ImportExportModelAdmin):
    list_display = ("metal", "ayar_kodu", "ayar_degeri", "milyem")
    list_filter = ("metal",)
    search_fields = ("ayar_kodu", "metal__ad", "metal__kod")
    list_select_related = ("metal",)
    autocomplete_fields = ("metal",)
