from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from firmalar import roles
from firmalar.models import Firma
from firmalar.selectors.tenant import scope_queryset
from firmalar.services.rol_servisi import assign_user_role, sync_user_role_groups
from firmalar.services.yetki_servisi import can_manage_all_users, can_view_all_tenants

from ..models import Kullanici


def _rol_choices_for(user):
    if can_view_all_tenants(user) or can_manage_all_users(user):
        return list(roles.ROLE_CHOICES)
    firma = getattr(user, "firma", None)
    if firma is None:
        return []
    if getattr(firma, "tedarikci_mi", False):
        allowed = roles.TEDARIKCI_ROLLERI
    elif getattr(firma, "alici_mi", False):
        allowed = roles.ALICI_ROLLERI
    else:
        allowed = frozenset()
    return [(c, lab) for c, lab in roles.ROLE_CHOICES if c in allowed]


@admin.register(Kullanici)
class KullaniciAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Kişisel bilgiler", {"fields": ("first_name", "last_name", "email")}),
        ("Firma ve iş rolü", {"fields": ("firma", "rol")}),
        ("Durum", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Önemli tarihler", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "firma", "rol"),
        }),
    )
    readonly_fields = ("user_permissions",)
    filter_horizontal = ()
    list_display = ("username", "firma", "rol", "is_active", "is_staff", "is_superuser")
    list_filter = ("rol", "is_active", "is_staff", "is_superuser", "firma__aktif")
    search_fields = ("username", "first_name", "last_name", "email", "firma__ad")
    ordering = ("username",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if can_view_all_tenants(request.user) or can_manage_all_users(request.user):
            return qs
        return scope_queryset(qs, request.user, firma_field="firma_id")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "firma":
            if can_view_all_tenants(request.user) or can_manage_all_users(request.user):
                kwargs["queryset"] = Firma.objects.all()
            else:
                firma_id = getattr(request.user, "firma_id", None)
                kwargs["queryset"] = (
                    Firma.objects.filter(pk=firma_id) if firma_id else Firma.objects.none()
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "rol":
            kwargs["choices"] = _rol_choices_for(request.user)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Firma/rol ataması assign_user_role ile senkron kalır (ADR-0003/0006)."""
        raw_password = None
        if form and form.cleaned_data.get("password1"):
            raw_password = form.cleaned_data["password1"]

        if raw_password:
            obj.set_password(raw_password)

        assign_user_role(
            actor=request.user,
            user=obj,
            firma=obj.firma,
            rol=obj.rol,
        )
        # assign_user_role save eder; ek alanlar (staff vb.) formdan obj üzerindedir
        super(UserAdmin, self).save_model(request, obj, form, change)
        sync_user_role_groups(obj)
