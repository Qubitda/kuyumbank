from django.contrib import admin

from firmalar.models import (
    HarcamaLimiti,
    OnayTalebi,
    OrgBirimi,
    OrgUyeligi,
)
from firmalar.selectors.org import scope_org_queryset


@admin.register(OrgBirimi)
class OrgBirimiAdmin(admin.ModelAdmin):
    list_display = ("id", "firma", "kod", "ad", "parent", "aktif")
    list_filter = ("aktif",)
    search_fields = ("kod", "ad", "firma__ad")
    list_select_related = ("firma", "parent")
    autocomplete_fields = ("firma", "parent")

    def get_queryset(self, request):
        return scope_org_queryset(super().get_queryset(request), request.user)


@admin.register(OrgUyeligi)
class OrgUyeligiAdmin(admin.ModelAdmin):
    list_display = ("id", "kullanici", "org_birimi", "olusturma_tarihi")
    list_select_related = ("kullanici", "org_birimi", "org_birimi__firma")
    autocomplete_fields = ("kullanici", "org_birimi")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from firmalar.services.yetki_servisi import can_view_all_tenants

        if can_view_all_tenants(request.user):
            return qs
        firma = getattr(request.user, "firma", None)
        if firma is None:
            return qs.none()
        return qs.filter(org_birimi__firma_id=firma.pk)


@admin.register(HarcamaLimiti)
class HarcamaLimitiAdmin(admin.ModelAdmin):
    """F10-012/014 — salt okunur admin (portal UI F9)."""

    list_display = (
        "id",
        "firma",
        "org_birimi",
        "donem",
        "tutar",
        "para_birimi",
        "aktif",
    )
    list_filter = ("aktif", "donem")
    list_select_related = ("firma", "org_birimi")
    readonly_fields = (
        "firma",
        "org_birimi",
        "donem",
        "tutar",
        "para_birimi",
        "aktif",
        "olusturma_tarihi",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OnayTalebi)
class OnayTalebiAdmin(admin.ModelAdmin):
    """F10-013/014 — salt okunur onay kuyruğu stub."""

    list_display = (
        "id",
        "firma",
        "durum",
        "tutar",
        "para_birimi",
        "order",
        "olusturma_tarihi",
    )
    list_filter = ("durum",)
    list_select_related = ("firma", "org_birimi", "order")
    readonly_fields = (
        "firma",
        "org_birimi",
        "order",
        "durum",
        "tutar",
        "para_birimi",
        "gerekce",
        "olusturan",
        "karar_veren",
        "olusturma_tarihi",
        "guncelleme_tarihi",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
