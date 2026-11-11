from django.contrib import admin

from firmalar.services.yetki_servisi import has_perm
from piyasa.models import (
    DarphaneIscilik,
    PiyasaKarPolitikasi,
    PiyasaMarjPolitikasi,
    PiyasaUrun,
)
from piyasa.services import piyasa_fiyat_servisi

P_MANAGE = "piyasa.manage_piyasa"


def _piyasa_perm(user) -> bool:
    return (
        has_perm(user, P_MANAGE)
        or user.has_perm(P_MANAGE)
        or user.is_superuser
    )


class _PiyasaPermMixin:
    def has_module_permission(self, request):
        return _piyasa_perm(request.user) or super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return _piyasa_perm(request.user) or super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return _piyasa_perm(request.user) or super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return _piyasa_perm(request.user) or super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return _piyasa_perm(request.user) or super().has_delete_permission(
            request, obj
        )


@admin.register(PiyasaMarjPolitikasi)
class PiyasaMarjPolitikasiAdmin(_PiyasaPermMixin, admin.ModelAdmin):
    list_display = ("anahtar", "marj_modu", "guncelleme")
    fields = ("anahtar", "marj_modu", "guncelleme")
    readonly_fields = ("guncelleme",)


@admin.register(PiyasaKarPolitikasi)
class PiyasaKarPolitikasiAdmin(_PiyasaPermMixin, admin.ModelAdmin):
    list_display = (
        "anahtar",
        "banka_tipi",
        "banka_degeri",
        "isletme_tipi",
        "isletme_degeri",
        "gelir_vergisi_tipi",
        "gelir_vergisi_degeri",
        "diger_tipi",
        "diger_degeri",
    )
    readonly_fields = ("guncelleme",)


@admin.register(DarphaneIscilik)
class DarphaneIscilikAdmin(_PiyasaPermMixin, admin.ModelAdmin):
    list_display = ("urun", "kanal", "iscilik_tl", "aktif", "sira")
    list_filter = ("kanal", "aktif")
    list_editable = ("iscilik_tl", "aktif", "sira")
    autocomplete_fields = ("urun",)
    ordering = ("sira", "urun__kod", "kanal")


@admin.register(PiyasaUrun)
class PiyasaUrunAdmin(_PiyasaPermMixin, admin.ModelAdmin):
    """Ürün + alış/satış marj değerleri. Marj modu global politikadan."""

    list_display = (
        "kod",
        "ad",
        "grup",
        "olcek",
        "cikti_pb",
        "varyant_etiket",
        "metal",
        "ayar",
        "alis_marj",
        "satis_marj",
        "yuvarlama_adimi",
        "aktif",
        "sira",
        "baz_alis",
        "baz_satis",
        "feed",
    )
    list_filter = ("aktif", "grup", "olcek", "cikti_pb", "metal", "varyant_etiket")
    search_fields = ("kod", "ad", "metal__kod", "ayar__ayar_kodu")
    list_editable = ("sira", "aktif", "alis_marj", "satis_marj", "grup")
    autocomplete_fields = ("metal", "ayar")
    readonly_fields = ("olusturma", "guncelleme")
    ordering = ("grup", "sira", "kod")
    fieldsets = (
        (None, {"fields": ("kod", "ad", "aktif", "sira", "grup", "varyant_etiket")}),
        (
            "Tanımlar (mevcut tablolar — burada yeni metal/ayar açılmaz)",
            {
                "fields": ("metal", "ayar", "olcek", "cikti_pb", "gram"),
                "description": (
                    "Metal → Tanımlar / Kıymetli metaller. "
                    "Ayar → Tanımlar / Milyem tablosu. "
                    "Ölçek GRAM|ONS|KG; çıktı TRY|USD (ADR-0025)."
                ),
            },
        ),
        (
            "Marj değerleri (mod: Piyasa marj politikası — global TL|%)",
            {
                "fields": ("alis_marj", "satis_marj"),
                "description": (
                    "Alış marjı düşülür, satış marjı eklenir. "
                    "Birim (TL/%) tek yerden: Piyasa marj politikası."
                ),
            },
        ),
        ("Yuvarlama", {"fields": ("yuvarlama_adimi", "yuvarlama_yontemi")}),
        ("Kayıt", {"fields": ("olusturma", "guncelleme")}),
    )

    @admin.display(description="Baz alış")
    def baz_alis(self, obj):
        ozet = piyasa_fiyat_servisi.hesapla_urun(obj)
        return ozet["alis"] if ozet["ok"] else "—"

    @admin.display(description="Baz satış")
    def baz_satis(self, obj):
        ozet = piyasa_fiyat_servisi.hesapla_urun(obj)
        return ozet["satis"] if ozet["ok"] else "—"

    @admin.display(description="Feed")
    def feed(self, obj):
        ozet = piyasa_fiyat_servisi.hesapla_urun(obj)
        if not ozet["ok"]:
            return ozet["hata"][:48]
        return ozet["feed_health"] or "—"

