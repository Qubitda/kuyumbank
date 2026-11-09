from django.contrib import admin

from finans.models import (
    CariHesap,
    HedgeEntry,
    LedgerEntry,
    PaymentIntent,
    PaymentWebhookEvent,
)


class _ImmutableAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(_ImmutableAdmin):
    list_display = (
        "id",
        "firma",
        "yon",
        "tutar",
        "para_birimi",
        "hareket_tipi",
        "olusturma_tarihi",
    )
    list_filter = ("yon", "hareket_tipi", "para_birimi")
    search_fields = ("idempotency_key", "referans_id", "aciklama")
    readonly_fields = [f.name for f in LedgerEntry._meta.fields]
    ordering = ("-olusturma_tarihi", "-pk")


@admin.register(HedgeEntry)
class HedgeEntryAdmin(_ImmutableAdmin):
    list_display = ("id", "grams", "metal_kodu", "idempotency_key", "olusturma_tarihi")
    search_fields = ("idempotency_key", "aciklama", "metal_kodu")
    readonly_fields = [f.name for f in HedgeEntry._meta.fields]
    ordering = ("-olusturma_tarihi", "-pk")


@admin.register(CariHesap)
class CariHesapAdmin(_ImmutableAdmin):
    list_display = (
        "id",
        "firma",
        "karsi_firma",
        "para_birimi",
        "bakiye",
        "kredi_limiti",
        "guncelleme_tarihi",
    )
    list_filter = ("para_birimi",)
    search_fields = ("firma__ad",)
    readonly_fields = [f.name for f in CariHesap._meta.fields]


@admin.register(PaymentIntent)
class PaymentIntentAdmin(_ImmutableAdmin):
    list_display = (
        "id",
        "order",
        "alici_firma",
        "tutar",
        "para_birimi",
        "durum",
        "olusturma_tarihi",
    )
    list_filter = ("durum", "para_birimi")
    search_fields = ("idempotency_key",)
    readonly_fields = [f.name for f in PaymentIntent._meta.fields]


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(_ImmutableAdmin):
    list_display = (
        "id",
        "provider",
        "event_id",
        "event_type",
        "sonuc",
        "payment_intent",
        "olusturma_tarihi",
    )
    list_filter = ("provider", "sonuc", "event_type")
    search_fields = ("event_id",)
    readonly_fields = [f.name for f in PaymentWebhookEvent._meta.fields]

