from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from firmalar.models import Firma
from firmalar.services.yetki_servisi import can_view_all_tenants
from urunler.selectors.katalog_tenant import (
    scope_urun_queryset,
    scope_urun_related_queryset,
    user_may_see_tedarikci_identity,
)

from ..models import Urun, UrunKanal, UrunTasi, Varyant
from ..services import onay_servisi as servisler


class TopluRedForm(forms.Form):
    # MultipleHiddenInput listesi CharField ile bozulur; MultipleChoiceField kullan.
    _selected_action = forms.MultipleChoiceField(
        widget=forms.MultipleHiddenInput,
        required=False,
    )
    red_nedeni = forms.CharField(
        label="Red Nedeni",
        widget=forms.Textarea(attrs={"rows": 3, "cols": 40}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seçilen pk'ler choices olarak tanımlanmalı (yoksa validasyon düşer)
        raw = []
        if self.is_bound:
            raw = self.data.getlist("_selected_action")
        else:
            initial = self.initial.get("_selected_action") or []
            raw = list(initial) if not isinstance(initial, str) else [initial]
        self.fields["_selected_action"].choices = [(str(x), str(x)) for x in raw]


class TenantScopedInlineMixin:
    """Inline satırları üst ürünün tenant scope'una bağlıdır."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return scope_urun_related_queryset(qs, request.user, urun_field="urun")

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj is not None and not can_view_all_tenants(request.user):
            urun = getattr(obj, "urun", obj)
            if getattr(urun, "onay_durumu", None) == "onay_bekliyor":
                return False
        return True


class VaryantInline(TenantScopedInlineMixin, admin.TabularInline):
    model = Varyant
    extra = 1
    fields = (
        "sku", "tedarikci_sku", "renk", "beden", "gram", "sabit_fiyat", "ek_bedel",
        "stok", "benzersiz_parca", "aktif",
    )
    readonly_fields = ("sku",)
    autocomplete_fields = ("renk", "beden")


class UrunTasiInline(TenantScopedInlineMixin, admin.TabularInline):
    model = UrunTasi
    extra = 0
    autocomplete_fields = (
        "tas_tipi", "kesim", "mihlama_tipi", "mensei", "berraklik",
        "renk_derecesi", "kesim_kalitesi", "sertifika_kurumu",
    )


class UrunKanalInline(TenantScopedInlineMixin, admin.TabularInline):
    model = UrunKanal
    extra = 0
    autocomplete_fields = ("kanal",)
    can_delete = False


class UrunTenantAdminMixin:
    """Urun / ilişkili modeller için ortak tenant scope."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.model is Urun:
            return scope_urun_queryset(qs, request.user)
        return scope_urun_related_queryset(qs, request.user, urun_field="urun")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "urun":
            kwargs["queryset"] = scope_urun_queryset(Urun.objects.all(), request.user)
        if db_field.name == "olusturan_firma":
            if user_may_see_tedarikci_identity(request.user):
                kwargs["queryset"] = Firma.objects.all()
            else:
                firma_id = getattr(request.user, "firma_id", None)
                kwargs["queryset"] = (
                    Firma.objects.filter(pk=firma_id) if firma_id else Firma.objects.none()
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_autocomplete_fields(self, request):
        fields = list(super().get_autocomplete_fields(request))
        if not user_may_see_tedarikci_identity(request.user) and "olusturan_firma" in fields:
            fields.remove("olusturan_firma")
        return fields


@admin.register(Urun)
class UrunAdmin(UrunTenantAdminMixin, admin.ModelAdmin):
    list_display = (
        "platform_kodu", "ad", "olusturan_firma", "kategori", "ayar", "fiyat_tipi",
        "onay_durumu", "yayin_durumu",
    )
    list_filter = (
        "onay_durumu", "yayin_durumu", "fiyat_tipi", "temin_tipi", "kategori",
        "kimlik_sinifi", "olusturan_firma",
    )
    search_fields = ("platform_kodu", "ad", "kimlik_anahtari", "slug")
    list_select_related = ("olusturan_firma", "kategori", "ayar", "ayar__metal")
    autocomplete_fields = (
        "olusturan_firma", "kategori", "ayar", "koleksiyon", "yas_grubu",
        "zincir_tipi", "kopca_tipi",
    )
    list_per_page = 50

    readonly_fields = (
        "platform_kodu", "onay_durumu", "red_nedeni", "yayin_durumu",
        "olusturan_kullanici", "onaylayan_kullanici", "onay_zamani",
        "olusturma_zamani", "guncelleme_zamani",
    )
    filter_horizontal = ("teknikler", "stiller", "ozel_gunler")
    inlines = [VaryantInline, UrunTasiInline, UrunKanalInline]
    actions = [
        "onaya_gonder",
        "geri_cek",
        "onayla",
        "reddet",
        "taslaga_al",
        "yayina_al",
        "yakinda_yayina_al",
        "pasife_al",
    ]

    fieldsets = (
        ("Temel", {
            "fields": (
                "platform_kodu", "olusturan_firma", "kimlik_sinifi", "kimlik_anahtari",
                "ad", "aciklama", "kategori",
            )
        }),
        ("Fiyat ve temin", {"fields": ("ayar", "fiyat_tipi", "temin_tipi", "termin_gun")}),
        ("Varyant eksenleri", {"fields": ("renk_ekseni", "olcu_tipi")}),
        ("Vitrin nitelikleri", {
            "classes": ("collapse",),
            "fields": (
                "koleksiyon", "hedef_kitle", "yas_grubu", "yuzey", "zincir_tipi", "kopca_tipi",
                "teknikler", "stiller", "ozel_gunler",
            ),
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("slug", "meta_baslik", "meta_aciklama", "canonical_url", "gorsel_alt_metni"),
        }),
        ("Onay ve yayın", {
            "fields": (
                "onay_durumu", "red_nedeni", "yayin_durumu",
                "olusturan_kullanici", "onaylayan_kullanici", "onay_zamani",
                "olusturma_zamani", "guncelleme_zamani",
            ),
        }),
    )

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if not user_may_see_tedarikci_identity(request.user) and "olusturan_firma" in display:
            display.remove("olusturan_firma")
        return display

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        if not user_may_see_tedarikci_identity(request.user) and "olusturan_firma" in filters:
            filters.remove("olusturan_firma")
        return filters

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if user_may_see_tedarikci_identity(request.user):
            return fieldsets
        result = []
        for name, opts in fieldsets:
            fields = tuple(
                f for f in opts.get("fields", ())
                if f not in ("olusturan_firma",)
            )
            new_opts = dict(opts)
            new_opts["fields"] = fields
            result.append((name, new_opts))
        return result

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        # O1: tedarikçi onay_bekliyor ürünü düzenleyemez (geri_cek action kullanır)
        if obj is not None and not can_view_all_tenants(request.user):
            if getattr(obj, "onay_durumu", None) == "onay_bekliyor":
                return False
        return True

    def save_model(self, request, obj, form, change):
        if not change:
            obj.olusturan_kullanici = request.user
            if not user_may_see_tedarikci_identity(request.user) and request.user.firma_id:
                obj.olusturan_firma_id = request.user.firma_id
        if change:
            servisler.assert_onayli_kritik_kilit(obj)
        super().save_model(request, obj, form, change)

    def _toplu(self, request, queryset, islem, sonuc, **kwargs):
        from django.db import IntegrityError

        queryset = scope_urun_queryset(queryset, request.user)
        basarili, hatalar = 0, []
        for urun in queryset:
            try:
                islem(urun, request.user, **kwargs)
                basarili += 1
            except (ValidationError, PermissionDenied) as e:
                msg = "; ".join(e.messages) if hasattr(e, "messages") else str(e)
                hatalar.append(f"{urun.platform_kodu}: {msg}")
            except IntegrityError as e:
                hatalar.append(f"{urun.platform_kodu}: veritabanı kısıtı ihlali ({e}).")
        if basarili:
            self.message_user(request, f"{basarili} ürün {sonuc}.")
        for h in hatalar:
            self.message_user(request, h, messages.WARNING)

    @admin.action(description="Onaya gönder")
    def onaya_gonder(self, request, queryset):
        self._toplu(request, queryset, servisler.onaya_gonder, "onaya gönderildi")

    @admin.action(description="Onaydan geri çek (taslak)")
    def geri_cek(self, request, queryset):
        self._toplu(request, queryset, servisler.geri_cek, "taslağa çekildi")

    @admin.action(description="Onayla")
    def onayla(self, request, queryset):
        self._toplu(request, queryset, servisler.onayla, "onaylandı")

    @admin.action(description="Taslağa al (yeniden onay)")
    def taslaga_al(self, request, queryset):
        self._toplu(request, queryset, servisler.taslaga_al, "taslağa alındı")

    @admin.action(description="Reddet (Seçilen ürünler için gerekçe girin)")
    def reddet(self, request, queryset):
        changelist_url = reverse("admin:urunler_urun_changelist")
        queryset = scope_urun_queryset(queryset, request.user)

        if "apply" in request.POST:
            form = TopluRedForm(request.POST)
            if form.is_valid():
                red_nedeni = form.cleaned_data["red_nedeni"]
                id_listesi = form.cleaned_data.get("_selected_action") or []
                hedef = scope_urun_queryset(
                    Urun.objects.filter(pk__in=id_listesi), request.user
                ) if id_listesi else queryset
                self._toplu(request, hedef, servisler.reddet, "reddedildi", neden=red_nedeni)
                return HttpResponseRedirect(changelist_url)
        else:
            form = TopluRedForm(
                initial={"_selected_action": request.POST.getlist(admin.ACTION_CHECKBOX_NAME)}
            )

        return render(request, "admin/toplu_red_onay.html", context={
            "items": queryset,
            "form": form,
            "title": "Toplu Red Nedeni Girin",
            "opts": self.model._meta,
            "action_checkbox_name": admin.ACTION_CHECKBOX_NAME,
        })

    @admin.action(description="Yayına al (aktif)")
    def yayina_al(self, request, queryset):
        self._toplu(request, queryset, servisler.yayina_al, "yayına alındı", durum="aktif")

    @admin.action(description="Yayına al (yakında)")
    def yakinda_yayina_al(self, request, queryset):
        self._toplu(request, queryset, servisler.yayina_al, "yakında olarak işaretlendi", durum="yakinda")

    @admin.action(description="Pasife al")
    def pasife_al(self, request, queryset):
        self._toplu(request, queryset, servisler.pasife_al, "pasife alındı")


@admin.register(Varyant)
class VaryantAdmin(UrunTenantAdminMixin, admin.ModelAdmin):
    list_display = (
        "sku", "urun", "renk", "beden", "gram", "sabit_fiyat", "ek_bedel",
        "stok", "benzersiz_parca", "aktif",
    )
    list_editable = ("gram", "sabit_fiyat", "ek_bedel", "stok", "aktif")
    list_filter = ("aktif", "benzersiz_parca", "renk")
    search_fields = ("sku", "tedarikci_sku", "urun__ad", "urun__platform_kodu")
    list_select_related = ("urun", "renk", "beden")
    autocomplete_fields = ("urun", "renk", "beden")
    readonly_fields = ("sku",)
    list_per_page = 50


@admin.register(UrunTasi)
class UrunTasiAdmin(UrunTenantAdminMixin, admin.ModelAdmin):
    list_display = ("urun", "tas_tipi", "adet", "karat", "bedel", "sertifika_kurumu", "sertifika_no")
    list_filter = ("tas_tipi", "mensei", "sertifika_kurumu")
    search_fields = ("urun__ad", "urun__platform_kodu", "sertifika_no")
    list_select_related = ("urun", "tas_tipi", "sertifika_kurumu")
    autocomplete_fields = (
        "urun", "tas_tipi", "kesim", "mihlama_tipi", "mensei", "berraklik",
        "renk_derecesi", "kesim_kalitesi", "sertifika_kurumu",
    )
    list_per_page = 50


@admin.register(UrunKanal)
class UrunKanalAdmin(UrunTenantAdminMixin, admin.ModelAdmin):
    list_display = ("urun", "kanal", "aktif")
    list_editable = ("aktif",)
    list_filter = ("aktif", "kanal")
    search_fields = ("urun__ad", "urun__platform_kodu", "kanal__ad")
    list_select_related = ("urun", "kanal")
    autocomplete_fields = ("urun", "kanal")
    list_per_page = 50

    def has_delete_permission(self, request, obj=None):
        return False
