"""Cart/Order tenant scope — alıcı kendi; view_all / QC / lojistik ops; başkası DoesNotExist."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from siparis.models import Cart, Order


class CartNotFound(ObjectDoesNotExist):
    """404 semantiği — varlık / çapraz tenant sızdırılmaz."""


class OrderNotFound(ObjectDoesNotExist):
    """404 semantiği — varlık / çapraz tenant sızdırılmaz."""


def can_ops_read_orders(user) -> bool:
    """Y1: view_all veya QC/lojistik manage/view — genel view_all genişletmesi değil."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if can_view_all_tenants(user):
        return True
    return (
        has_perm(user, P["manage_qc"])
        or has_perm(user, P["view_qc"])
        or has_perm(user, P["manage_shipment"])
    )


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
        Cart.objects.select_related("alici_firma").prefetch_related("lines"),
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


def scope_order_queryset(qs, user):
    """Alıcı: kendi. view_all / QC / lojistik: tümü (rol-kapılı). Tedarikçi: boş."""
    if can_ops_read_orders(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(alici_firma_id=firma_id)
    return qs.none()


def get_order_for_actor(user, order_id: int) -> Order:
    if user is None or not getattr(user, "is_authenticated", False):
        raise OrderNotFound("Sipariş bulunamadı.")
    qs = scope_order_queryset(
        Order.objects.select_related("alici_firma").prefetch_related("lines"),
        user,
    )
    try:
        return qs.get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise OrderNotFound("Sipariş bulunamadı.") from exc
