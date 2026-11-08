"""Tenant scope okuma yardımcıları (ADR-0003, ADR-0004 selectors)."""

from django.core.exceptions import PermissionDenied
from django.http import Http404

from ..services.yetki_servisi import can_view_all_tenants


def object_firma_id(obj, *, firma_field: str = "firma_id"):
    if hasattr(obj, firma_field):
        return getattr(obj, firma_field)
    if firma_field.endswith("_id"):
        rel = firma_field[:-3]
        related = getattr(obj, rel, None)
        return getattr(related, "pk", None) if related is not None else None
    return None


def scope_queryset(qs, user, *, firma_field: str = "firma_id"):
    """Çapraz tenant yetkisi yoksa queryset'i kullanıcının firmasına indirger."""
    if can_view_all_tenants(user):
        return qs
    if not getattr(user, "firma_id", None):
        return qs.none()
    return qs.filter(**{firma_field: user.firma_id})


def assert_same_firma(user, obj_or_firma_id, *, hide: bool = True):
    """Nesne başka firmaya aitse 404 (hide) veya PermissionDenied."""
    if can_view_all_tenants(user):
        return
    target = obj_or_firma_id
    if not isinstance(target, int) and target is not None:
        target = (
            object_firma_id(target)
            or object_firma_id(target, firma_field="olusturan_firma_id")
            or object_firma_id(target, firma_field="tedarikci_id")
        )
    if target != getattr(user, "firma_id", None):
        if hide:
            raise Http404()
        raise PermissionDenied("Bu kayda erişim yetkiniz yok.")
