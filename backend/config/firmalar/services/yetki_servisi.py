"""Permission tabanlı yetki kontrolleri — rol string switch yok (ADR-0003).

Not: Django `User.has_perm` is_superuser için her zaman True döner.
İş kurallarında bu kısa yol kullanılmaz; tenant/permission sessizce aşılmaz.
"""

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied

from .. import roles
from ..role_permissions import P


def has_perm(user, perm: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", False):
        return False
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "aktif", True) is False:
        return False
    if not perm or "." not in perm:
        return False
    app_label, codename = perm.split(".", 1)
    if user.user_permissions.filter(
        content_type__app_label=app_label, codename=codename
    ).exists():
        return True
    return Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
        group__user=user,
    ).exists()


def require_perm(user, perm: str, *, message: str | None = None):
    if not has_perm(user, perm):
        raise PermissionDenied(message or f"Yetki gerekli: {perm}")


def is_platform_firm_user(user) -> bool:
    firma = getattr(user, "firma", None)
    return bool(
        getattr(user, "firma_id", None)
        and firma is not None
        and firma.platform_mu
        and user.rol in roles.PLATFORM_ROLLERI
    )


def can_view_all_tenants(user) -> bool:
    if not is_platform_firm_user(user):
        return False
    return has_perm(user, P["view_all_tenants"])


def can_manage_all_users(user) -> bool:
    return is_platform_firm_user(user) and has_perm(user, P["manage_all_users"])
