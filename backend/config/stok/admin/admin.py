from django.contrib import admin

from stok.models import StockBalance, StockMovement, StockReservation, Warehouse
from stok.selectors.tenant import scope_warehouse_queryset


class _StokReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Warehouse)
class WarehouseAdmin(_StokReadOnlyAdmin):
    """Depo — salt okunur; yazım `warehouse_servisi` üzerinden."""

    list_display = (
        "id",
        "kod",
        "ad",
        "sahip_firma",
        "sahip_tipi",
        "aktif",
        "olusturma_tarihi",
    )
    list_filter = ("sahip_tipi", "aktif")
    search_fields = ("kod", "ad", "sahip_firma__ad")
    list_select_related = ("sahip_firma",)
    readonly_fields = (
        "kod",
        "ad",
        "sahip_firma",
        "sahip_tipi",
        "aktif",
        "olusturma_tarihi",
        "guncelleme_tarihi",
    )

    def get_queryset(self, request):
        return scope_warehouse_queryset(
            super().get_queryset(request), request.user
        )


@admin.register(StockMovement)
class StockMovementAdmin(_StokReadOnlyAdmin):
    list_display = (
        "id",
        "tip",
        "miktar",
        "birim",
        "warehouse",
        "teklif",
        "olusturma_tarihi",
    )
    list_filter = ("tip", "birim")
    list_select_related = ("warehouse", "teklif", "varyant")
    readonly_fields = [f.name for f in StockMovement._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        wh_ids = scope_warehouse_queryset(
            Warehouse.objects.all(), request.user
        ).values_list("pk", flat=True)
        return qs.filter(warehouse_id__in=wh_ids)


@admin.register(StockBalance)
class StockBalanceAdmin(_StokReadOnlyAdmin):
    list_display = (
        "id",
        "warehouse",
        "teklif",
        "birim",
        "on_hand",
        "reserved",
        "blocked",
    )
    list_filter = ("birim",)
    list_select_related = ("warehouse", "teklif", "varyant")
    readonly_fields = [f.name for f in StockBalance._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        wh_ids = scope_warehouse_queryset(
            Warehouse.objects.all(), request.user
        ).values_list("pk", flat=True)
        return qs.filter(warehouse_id__in=wh_ids)


@admin.register(StockReservation)
class StockReservationAdmin(_StokReadOnlyAdmin):
    list_display = (
        "id",
        "durum",
        "miktar",
        "birim",
        "warehouse",
        "teklif",
        "alici_firma",
        "gecerlilik_sonu",
    )
    list_filter = ("durum", "birim")
    list_select_related = ("warehouse", "teklif", "alici_firma", "varyant")
    readonly_fields = [f.name for f in StockReservation._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        wh_ids = scope_warehouse_queryset(
            Warehouse.objects.all(), request.user
        ).values_list("pk", flat=True)
        return qs.filter(warehouse_id__in=wh_ids)
