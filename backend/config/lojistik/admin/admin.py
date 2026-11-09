from django.contrib import admin

from lojistik.models import ProofOfDelivery, ReturnLine, ReturnRequest, Shipment


class _ImmutableAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Shipment)
class ShipmentAdmin(_ImmutableAdmin):
    """Salt okunur; yazım shipment_servisi."""

    list_display = (
        "id",
        "order",
        "durum",
        "takip_no",
        "olusturma_tarihi",
    )
    list_filter = ("durum",)
    list_select_related = ("order",)
    readonly_fields = (
        "order",
        "durum",
        "takip_no",
        "notlar",
        "olusturan",
        "olusturma_tarihi",
        "guncelleme_tarihi",
    )


@admin.register(ProofOfDelivery)
class ProofOfDeliveryAdmin(_ImmutableAdmin):
    list_display = ("id", "shipment", "teslim_alan", "olusturma_tarihi")
    list_select_related = ("shipment",)
    readonly_fields = [f.name for f in ProofOfDelivery._meta.fields]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(_ImmutableAdmin):
    """Salt okunur; yazım return_servisi (F6-030)."""

    list_display = (
        "id",
        "order",
        "shipment",
        "durum",
        "stok_iade_yapildi",
        "finans_mahsup_yapildi",
        "olusturma_tarihi",
    )
    list_filter = ("durum", "stok_iade_yapildi", "finans_mahsup_yapildi")
    list_select_related = ("order", "shipment")
    readonly_fields = [f.name for f in ReturnRequest._meta.fields]


@admin.register(ReturnLine)
class ReturnLineAdmin(_ImmutableAdmin):
    list_display = ("id", "return_request", "order_line", "miktar", "birim")
    list_select_related = ("return_request", "order_line")
    readonly_fields = [f.name for f in ReturnLine._meta.fields]
