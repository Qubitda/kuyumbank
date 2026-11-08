from django.contrib import admin
from django.core.exceptions import PermissionDenied

from firmalar.models import Firma
from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.models import (
    FiyatSozlesmesi,
    FiyatSozlesmesiKalemi,
    PriceCalculationLog,
    TedarikciTeklif,
    UrunTasi,
)
from fiyatlama.selectors.tenant import (
    scope_fiyat_sozlesmesi_kalemi_queryset,
    scope_fiyat_sozlesmesi_queryset,
    scope_price_log_queryset,
    scope_teklif_queryset,
    scope_teklif_uruntasi_queryset,
    scope_teklif_varyant_queryset,
    user_may_see_fiyat_maliyet,
)
from urunler.models import Varyant


class FiyatSozlesmesiKalemiInline(admin.TabularInline):
    model = FiyatSozlesmesiKalemi
    extra = 0
    fields = (
        "metal",
        "ayar",
        "marj_tipi",
        "marj_degeri",
        "iscilik",
        "islcilik_dahil_mi",
        "sira",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return scope_fiyat_sozlesmesi_kalemi_queryset(qs, request.user)


@admin.register(FiyatSozlesmesi)
class FiyatSozlesmesiAdmin(admin.ModelAdmin):
    list_display = (
        "firma",
        "kontrat_tipi",
        "satis_kanali",
        "versiyon",
        "gecerlilik_baslangic",
        "gecerlilik_bitis",
        "durum",
    )
    list_filter = ("kontrat_tipi", "durum", "satis_kanali")
    search_fields = ("firma__ad",)
    inlines = [FiyatSozlesmesiKalemiInline]
    readonly_fields = ("olusturma_tarihi", "guncelleme_tarihi")

    def get_queryset(self, request):
        return scope_fiyat_sozlesmesi_queryset(super().get_queryset(request), request.user)

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if not user_may_see_fiyat_maliyet(request.user):
            # Alıcı/tedarikçi: sözleşme varlığını görebilir (kendi firması) ama
            # marj/maliyet odaklı alanlar kalem inline'da ayrıca kısıtlanır.
            pass
        return display


class UrunTasiInline(admin.TabularInline):
    model = UrunTasi
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return scope_teklif_uruntasi_queryset(qs, request.user)


@admin.register(TedarikciTeklif)
class TedarikciTeklifAdmin(admin.ModelAdmin):
    list_display = (
        "tedarikci",
        "varyant",
        "fiyat_modeli",
        "gram",
        "birim_fiyat",
        "para_birimi",
        "temin_tipi",
        "stok_adet",
        "durum",
    )
    list_filter = ("fiyat_modeli", "temin_tipi", "durum")
    search_fields = ("tedarikci__ad", "varyant__sku", "tedarikci_kodu")
    inlines = [UrunTasiInline]
    _maliyet_fields = ("birim_fiyat", "iscilik_override")
    # Durum / eşleştirme yalnız servis (ADR-0006 B1)
    _servis_alanlari = (
        "durum",
        "onaylayan",
        "onay_zamani",
        "eslestirme_durumu",
        "eslestirme_guveni",
        "eslestiren_kullanici",
        "eslestirme_kaniti",
        "hedef_urun",
        "esdegerlik_seviyesi",
    )

    def get_queryset(self, request):
        return scope_teklif_queryset(super().get_queryset(request), request.user)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        for f in self._servis_alanlari:
            if f not in ro:
                ro.append(f)
        if not can_view_all_tenants(request.user) and "tedarikci" not in ro:
            ro.append("tedarikci")
        return ro

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "varyant":
            kwargs["queryset"] = scope_teklif_varyant_queryset(
                Varyant.objects.all(), request.user
            )
        if db_field.name == "tedarikci":
            if can_view_all_tenants(request.user):
                kwargs["queryset"] = Firma.objects.filter(tedarikci_mi=True)
            else:
                firma_id = getattr(request.user, "firma_id", None)
                kwargs["queryset"] = (
                    Firma.objects.filter(pk=firma_id)
                    if firma_id
                    else Firma.objects.none()
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Tedarikçi kimliği formdan değil; sunucu atar (IDOR engeli).
        if not can_view_all_tenants(request.user):
            firma = getattr(request.user, "firma", None)
            if firma is None or not getattr(firma, "tedarikci_mi", False):
                raise PermissionDenied("Teklif yalnız tedarikçi firması kullanıcısıyla kaydedilir.")
            obj.tedarikci = firma
        super().save_model(request, obj, form, change)

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if not user_may_see_fiyat_maliyet(request.user):
            for f in self._maliyet_fields:
                if f in display:
                    display.remove(f)
            firma = getattr(request.user, "firma", None)
            # Alıcı (tedarikçi değil): tedarikçi kimliğini gösterme
            if (
                firma
                and getattr(firma, "alici_mi", False)
                and not getattr(firma, "tedarikci_mi", False)
                and "tedarikci" in display
            ):
                display.remove("tedarikci")
        return display

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not user_may_see_fiyat_maliyet(request.user):
            fields = [f for f in fields if f not in self._maliyet_fields]
        # Eşleştirme güveni tedarikçiye gösterilmez (ADR-0006 B3)
        if not can_view_all_tenants(request.user):
            fields = [f for f in fields if f != "eslestirme_guveni"]
        return fields


@admin.register(PriceCalculationLog)
class PriceCalculationLogAdmin(admin.ModelAdmin):
    list_display = (
        "hesap_zamani",
        "sozlesme",
        "varyant",
        "kaynak",
        "toplam",
        "kilit_bitis",
    )
    list_filter = ("kaynak",)
    readonly_fields = [f.name for f in PriceCalculationLog._meta.fields]

    def get_queryset(self, request):
        return scope_price_log_queryset(super().get_queryset(request), request.user)

    def has_module_permission(self, request):
        return user_may_see_fiyat_maliyet(request.user)

    def has_view_permission(self, request, obj=None):
        return user_may_see_fiyat_maliyet(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FiyatSozlesmesiKalemi)
class FiyatSozlesmesiKalemiAdmin(admin.ModelAdmin):
    list_display = (
        "sozlesme",
        "metal",
        "ayar",
        "marj_tipi",
        "marj_degeri",
        "iscilik",
        "islcilik_dahil_mi",
        "sira",
    )
    list_filter = ("marj_tipi", "sozlesme__kontrat_tipi", "sozlesme__durum")
    search_fields = ("sozlesme__firma__ad",)
    list_select_related = ("sozlesme", "metal", "ayar")
    autocomplete_fields = ("sozlesme", "metal", "ayar")
    _maliyet_fields = ("marj_degeri", "iscilik", "marj_tipi")

    def get_queryset(self, request):
        return scope_fiyat_sozlesmesi_kalemi_queryset(
            super().get_queryset(request), request.user
        )

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if not user_may_see_fiyat_maliyet(request.user):
            for f in self._maliyet_fields:
                if f in display:
                    display.remove(f)
        return display


@admin.register(UrunTasi)
class FiyatlamaUrunTasiAdmin(admin.ModelAdmin):
    list_display = ("teklif", "tas_grubu", "adet", "toplam_karat", "bedel", "para_birimi")
    list_filter = ("tas_grubu", "para_birimi")
    search_fields = ("teklif__tedarikci__ad", "teklif__varyant__sku")
    list_select_related = ("teklif", "teklif__tedarikci", "teklif__varyant")
    _maliyet_fields = ("bedel",)

    def get_queryset(self, request):
        return scope_teklif_uruntasi_queryset(super().get_queryset(request), request.user)

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if not user_may_see_fiyat_maliyet(request.user):
            for f in self._maliyet_fields:
                if f in display:
                    display.remove(f)
        return display
