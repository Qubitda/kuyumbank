from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from tanimlar.models import DovizKuru, KurPolitikasi, KurSaglayici, MetalKuru
from tanimlar.services import kur_servisi

User = get_user_model()


class KurAdminTaban(admin.ModelAdmin):
    """Kur gözlemleri tarihçedir: değiştirilmez / silinmez."""

    readonly_fields = (
        "giren_kullanici",
        "girilme_zamani",
        "onaylayan_kullanici",
        "onay_zamani",
        "alinma_zamani",
        "saglayici",
    )
    date_hierarchy = "zaman"

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ManuelMetalKuruForm(forms.ModelForm):
    onaylayan = forms.ModelChoiceField(
        label="Onaylayan (dört göz)",
        queryset=User.objects.filter(is_active=True, is_staff=True),
        required=True,
    )

    class Meta:
        model = MetalKuru
        fields = ("metal", "kur_tipi", "zaman", "saf_birim_fiyat", "manuel_neden")


class ManuelDovizKuruForm(forms.ModelForm):
    onaylayan = forms.ModelChoiceField(
        label="Onaylayan (dört göz)",
        queryset=User.objects.filter(is_active=True, is_staff=True),
        required=True,
    )

    class Meta:
        model = DovizKuru
        fields = ("para_birimi", "kur_tipi", "zaman", "kur", "manuel_neden")


@admin.register(MetalKuru)
class MetalKuruAdmin(KurAdminTaban):
    form = ManuelMetalKuruForm
    list_display = (
        "metal",
        "kur_tipi",
        "saf_birim_fiyat",
        "zaman",
        "saglayici",
        "kaynak",
        "giren_kullanici",
    )
    list_filter = ("metal", "kur_tipi", "kaynak", "saglayici")
    search_fields = ("metal__ad", "metal__kod")
    list_select_related = ("metal", "giren_kullanici", "saglayici")
    autocomplete_fields = ("metal",)

    def save_model(self, request, obj, form, change):
        if change:
            return
        try:
            saved = kur_servisi.manuel_metal_kuru_gir(
                request.user,
                form.cleaned_data["onaylayan"],
                metal=form.cleaned_data["metal"],
                saf_birim_fiyat=form.cleaned_data["saf_birim_fiyat"],
                kur_tipi=form.cleaned_data["kur_tipi"],
                zaman=form.cleaned_data.get("zaman"),
                neden=form.cleaned_data.get("manuel_neden") or "",
            )
        except (PermissionDenied, ValidationError, kur_servisi.KurYokError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            raise
        obj.pk = saved.pk


@admin.register(DovizKuru)
class DovizKuruAdmin(KurAdminTaban):
    form = ManuelDovizKuruForm
    list_display = (
        "para_birimi",
        "kur_tipi",
        "kur",
        "zaman",
        "saglayici",
        "kaynak",
        "giren_kullanici",
    )
    list_filter = ("para_birimi", "kur_tipi", "kaynak", "saglayici")
    search_fields = ("para_birimi",)
    list_select_related = ("giren_kullanici", "saglayici")

    def save_model(self, request, obj, form, change):
        if change:
            return
        try:
            saved = kur_servisi.manuel_doviz_kuru_gir(
                request.user,
                form.cleaned_data["onaylayan"],
                para_birimi=form.cleaned_data["para_birimi"],
                kur=form.cleaned_data["kur"],
                kur_tipi=form.cleaned_data["kur_tipi"],
                zaman=form.cleaned_data.get("zaman"),
                neden=form.cleaned_data.get("manuel_neden") or "",
            )
        except (PermissionDenied, ValidationError, kur_servisi.KurYokError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            raise
        obj.pk = saved.pk


@admin.register(KurSaglayici)
class KurSaglayiciAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "aktif", "max_gecikme_saniye")
    list_filter = ("aktif",)
    search_fields = ("kod", "ad")
    readonly_fields = ("olusturma", "guncelleme")
    actions = ("aksiyon_aktif_yap",)

    @admin.action(description="Seçilen sağlayıcıyı aktif yap (tek aktif)")
    def aksiyon_aktif_yap(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request, "Tam olarak bir sağlayıcı seçin.", level=messages.ERROR
            )
            return
        hedef = queryset.get()
        try:
            kur_servisi.aktif_saglayici_ayarla(request.user, hedef.pk)
        except (PermissionDenied, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return
        self.message_user(request, f"{hedef.kod} aktif yapıldı.")


@admin.register(KurPolitikasi)
class KurPolitikasiAdmin(admin.ModelAdmin):
    list_display = ("anahtar", "alici_kur_tipi", "tedarikci_kur_tipi", "guncelleme")
    readonly_fields = ("anahtar", "guncelleme")

    def has_add_permission(self, request):
        return not KurPolitikasi.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        try:
            kur_servisi.politikayi_guncelle(
                request.user,
                alici_kur_tipi=obj.alici_kur_tipi,
                tedarikci_kur_tipi=obj.tedarikci_kur_tipi,
            )
        except (PermissionDenied, ValidationError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            raise
        obj.pk = kur_servisi.get_or_create_politikasi().pk
