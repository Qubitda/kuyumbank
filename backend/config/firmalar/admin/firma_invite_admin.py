"""FirmaInvite admin — oluşturma servis/API üzerinden (ADR-0028)."""

from django.contrib import admin

from firmalar.models import FirmaInvite
from firmalar.selectors.tenant import scope_queryset
from firmalar.services.yetki_servisi import can_manage_all_users


@admin.register(FirmaInvite)
class FirmaInviteAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "firma",
        "rol",
        "expires_at",
        "kabul_edildi_at",
        "olusturma_tarihi",
    )
    list_filter = ("rol", "firma")
    search_fields = ("email", "firma__ad", "token")
    readonly_fields = (
        "token",
        "olusturan",
        "kabul_eden",
        "kabul_edildi_at",
        "olusturma_tarihi",
    )
    ordering = ("-olusturma_tarihi", "-pk")

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if can_manage_all_users(request.user):
            return qs
        return scope_queryset(qs, request.user, firma_field="firma_id")
