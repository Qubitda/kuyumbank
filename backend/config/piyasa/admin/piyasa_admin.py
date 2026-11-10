from decimal import Decimal, InvalidOperation

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.urls import path, reverse

from firmalar.services.yetki_servisi import has_perm
from piyasa.models import (
    DarphaneIscilik,
    PiyasaKarPolitikasi,
    PiyasaMarjPolitikasi,
    PiyasaUrun,
)
from piyasa.services import kar_yardimcisi, piyasa_fiyat_servisi

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
    change_list_template = "admin/piyasa/piyasaurun_changelist.html"
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

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "kar-yardimcisi/",
                self.admin_site.admin_view(self.kar_yardimcisi_view),
                name="piyasa_kar_yardimcisi",
            ),
        ]
        return custom + urls

    def kar_yardimcisi_view(self, request):
        if not _piyasa_perm(request.user):
            messages.error(request, "Piyasa yetkisi yok.")
            from django.shortcuts import redirect

            return redirect("admin:index")

        pol = kar_yardimcisi.get_kar_politikasi()
        g = request.GET
        ctx = {
            "title": "Kar hesaplama yardımcısı",
            "giris": g.get("giris", "PANO"),
            "urun_kod": g.get("urun_kod", ""),
            "metal_kod": g.get("metal_kod", ""),
            "ayar_kodu": g.get("ayar_kodu", ""),
            "taraf": g.get("taraf", "SATIS"),
            "agirlik_gr": g.get("agirlik_gr", "1"),
            "kar_pct": g.get("kar_pct", "0"),
            "iscilik_tl": g.get("iscilik_tl", "0"),
            "hedef_toplam": g.get("hedef_toplam", ""),
            "banka_tipi": g.get("banka_tipi", pol.banka_tipi),
            "banka_degeri": g.get("banka_degeri", str(pol.banka_degeri)),
            "isletme_tipi": g.get("isletme_tipi", pol.isletme_tipi),
            "isletme_degeri": g.get("isletme_degeri", str(pol.isletme_degeri)),
            "gv_tipi": g.get("gv_tipi", pol.gelir_vergisi_tipi),
            "gv_degeri": g.get("gv_degeri", str(pol.gelir_vergisi_degeri)),
            "diger_tipi": g.get("diger_tipi", pol.diger_tipi),
            "diger_degeri": g.get("diger_degeri", str(pol.diger_degeri)),
            "sonuc": None,
            "hata": "",
            "opts": self.model._meta,
            "marj_modu": piyasa_fiyat_servisi.get_marj_modu(),
        }
        hesapla = bool(g.get("urun_kod") or g.get("metal_kod"))
        if hesapla:
            try:
                hedef = ctx["hedef_toplam"].strip() or None
                kes = dict(
                    banka={
                        "tip": ctx["banka_tipi"],
                        "deger": Decimal(ctx["banka_degeri"] or "0"),
                    },
                    isletme={
                        "tip": ctx["isletme_tipi"],
                        "deger": Decimal(ctx["isletme_degeri"] or "0"),
                    },
                    gelir_vergisi={
                        "tip": ctx["gv_tipi"],
                        "deger": Decimal(ctx["gv_degeri"] or "0"),
                    },
                    diger={
                        "tip": ctx["diger_tipi"],
                        "deger": Decimal(ctx["diger_degeri"] or "0"),
                    },
                )
                ortak = dict(
                    taraf=ctx["taraf"],
                    agirlik_gr=Decimal(ctx["agirlik_gr"] or "1"),
                    kar_pct=Decimal(ctx["kar_pct"] or "0"),
                    iscilik_tl=Decimal(ctx["iscilik_tl"] or "0"),
                    hedef_toplam=Decimal(hedef) if hedef else None,
                    **kes,
                )
                if ctx["giris"] == "METAL_AYAR" or (
                    not ctx["urun_kod"] and ctx["metal_kod"]
                ):
                    ctx["sonuc"] = kar_yardimcisi.simule_metal_ayar(
                        metal_kod=ctx["metal_kod"],
                        ayar_kodu=ctx["ayar_kodu"] or None,
                        **ortak,
                    )
                else:
                    ctx["sonuc"] = kar_yardimcisi.simule_pano_urun(
                        urun_kod=ctx["urun_kod"], **ortak
                    )
            except (
                ValidationError,
                ValueError,
                InvalidOperation,
                PiyasaUrun.DoesNotExist,
            ) as exc:
                ctx["hata"] = str(exc)
        return render(request, "admin/piyasa/kar_yardimcisi.html", ctx)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["kar_yardimcisi_url"] = reverse("admin:piyasa_kar_yardimcisi")
        extra_context["marj_modu"] = piyasa_fiyat_servisi.get_marj_modu()
        return super().changelist_view(request, extra_context=extra_context)
