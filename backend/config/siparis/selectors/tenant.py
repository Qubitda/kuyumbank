"""Cart tenant scope — alıcı kendi sepeti; başkası DoesNotExist (F4-A7)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import Cart


class CartNotFound(ObjectDoesNotExist):
    """404 semantiği — varlık / çapraz tenant sızdırılmaz."""


def scope_cart_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(alici_firma_id=firma_id)
    return qs.none()


def get_cart_for_actor(user, cart_id: int | None = None) -> Cart:
    """Actor’un görebileceği sepet. Yok/kapsam dışı → CartNotFound."""
    if user is None or not getattr(user, "is_authenticated", False):
        raise CartNotFound("Sepet bulunamadı.")
    qs = scope_cart_queryset(
        Cart.objects.select_related("alici_firma"),
        user,
    )
    try:
        if cart_id is not None:
            return qs.get(pk=cart_id)
        firma_id = getattr(user, "firma_id", None)
        if can_view_all_tenants(user):
            raise CartNotFound("Sepet bulunamadı.")
        return qs.get(alici_firma_id=firma_id)
    except Cart.DoesNotExist as exc:
        raise CartNotFound("Sepet bulunamadı.") from exc
