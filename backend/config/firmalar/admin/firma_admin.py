from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.selectors.tenant import scope_queryset
from firmalar.services.firma_onay_servisi import onayla_firma
from firmalar.services.yetki_servisi import can_view_all_tenants

from ..models import Firma, FirmaAdresi, FirmaBankaHesabi

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class FirmaAdresiInline(admin.TabularInline):
    model = FirmaAdresi
    extra = 0


class FirmaBankaHesabiInline(admin.TabularInline):
    model = FirmaBankaHesabi
    extra = 0
    fields = ("banka_adi", "iban", "swift_bic", "para_birimi", "aktif")


@admin.register(Firma)
class FirmaAdmin(admin.ModelAdmin):
    list_display = (
        "ad", "firma_kodu", "vergi_no", "alici_mi", "tedarikci_mi",
        "platform_mu", "onay_durumu", "aktif",
    )
    list_filter = ("alici_mi", "tedarikci_mi", "platform_mu", "onay_durumu", "aktif")
    search_fields = ("ad", "unvan", "vergi_no", "firma_kodu")
    inlines = [FirmaAdresiInline, FirmaBankaHesabiInline]
    actions = ("action_onayla",)

    @admin.action(description="Seçili firmaları onayla (firma.approved outbox)")
    def action_onayla(self, request, queryset):
        ok = 0
        for firma in queryset:
            try:
                onayla_firma(actor=request.user, firma=firma)
                ok += 1
            except (PermissionDenied, ValidationError) as exc:
                self.message_user(request, f"{firma}: {exc}", level=messages.ERROR)
        if ok:
            self.message_user(request, f"{ok} firma onaylandı.", level=messages.SUCCESS)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if can_view_all_tenants(request.user):
            return qs
        if getattr(request.user, "firma_id", None):
            return qs.filter(pk=request.user.firma_id)
        return qs.none()


@admin.register(FirmaAdresi)
class FirmaAdresiAdmin(admin.ModelAdmin):
    list_display = ("firma", "tip", "il", "ilce", "varsayilan")
    list_filter = ("tip", "varsayilan")
    search_fields = ("firma__ad", "il", "ilce")
    list_select_related = ("firma",)
    autocomplete_fields = ("firma",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return scope_queryset(qs, request.user, firma_field="firma_id")


@admin.register(FirmaBankaHesabi)
class FirmaBankaHesabiAdmin(admin.ModelAdmin):
    list_display = ("firma", "banka_adi", "iban", "swift_bic", "para_birimi", "aktif")
    list_filter = ("para_birimi", "aktif")
    search_fields = ("firma__ad", "banka_adi", "iban", "swift_bic")
    list_select_related = ("firma",)
    autocomplete_fields = ("firma",)
    fields = ("firma", "banka_adi", "iban", "swift_bic", "para_birimi", "aktif")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return scope_queryset(qs, request.user, firma_field="firma_id")
