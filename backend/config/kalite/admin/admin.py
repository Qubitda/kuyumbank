from django.contrib import admin

from kalite.models import QualityInspection, QualityMeasurement


class _ImmutableAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(QualityInspection)
class QualityInspectionAdmin(_ImmutableAdmin):
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


@admin.register(QualityMeasurement)
class QualityMeasurementAdmin(_ImmutableAdmin):
    """Salt okunur; yazım olcum_servisi (F6-011)."""

    list_display = (
        "id",
        "inspection",
        "order_line",
        "birim",
        "beklenen",
        "olculen",
        "sonuc",
        "override_uygulandi",
        "olusturma_tarihi",
    )
    list_filter = ("sonuc", "birim", "override_uygulandi")
    list_select_related = ("inspection", "order_line")
    readonly_fields = [f.name for f in QualityMeasurement._meta.fields]
