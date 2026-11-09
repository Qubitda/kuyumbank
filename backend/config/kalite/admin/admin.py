from django.contrib import admin

from kalite.models import QualityInspection


@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    """Salt okunur liste; yazım inspection_servisi."""

    list_display = (
        "id",
        "order",
        "order_line",
        "durum",
        "shipment_blok",
        "olusturma_tarihi",
    )
    list_filter = ("durum", "shipment_blok")
    list_select_related = ("order", "order_line")
    readonly_fields = (
        "order",
        "order_line",
        "durum",
        "shipment_blok",
        "notlar",
        "olusturan",
        "olusturma_tarihi",
        "guncelleme_tarihi",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
