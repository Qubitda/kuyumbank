from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

from .models import Firma, FirmaAdresi, FirmaBankaHesabi, Kullanici

# Rol gruplarının izinleri admin ekranından değiştirilemesin.
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


@admin.register(Firma)
class FirmaAdmin(admin.ModelAdmin):
    list_display = ("ad", "vergi_no", "alici_mi", "tedarikci_mi", "platform_mu", "onay_durumu", "aktif")
    list_filter = ("alici_mi", "tedarikci_mi", "onay_durumu", "aktif")
    search_fields = ("ad", "unvan", "vergi_no")
    inlines = [FirmaAdresiInline, FirmaBankaHesabiInline]


@admin.register(Kullanici)
class KullaniciAdmin(UserAdmin):
    # Groups ve doğrudan user_permissions alanları admin formundan çıkarıldı.
    # İş rolü tek kaynak; ilgili rol grubu otomatik senkronlanır.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Kişisel bilgiler", {"fields": ("first_name", "last_name", "email")}),
        ("Firma ve iş rolü", {"fields": ("firma", "rol")}),
        ("Durum", {"fields": ("is_active",)}),
        ("Önemli tarihler", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "firma", "rol"),
        }),
    )
    readonly_fields = ("is_staff", "is_superuser", "user_permissions")
    filter_horizontal = ()
    list_display = ("username", "firma", "rol", "is_active", "is_staff", "is_superuser")
    list_filter = ("rol", "is_active", "is_staff", "is_superuser", "firma__aktif")
    search_fields = ("username", "first_name", "last_name", "email", "firma__ad")
    ordering = ("username",)
