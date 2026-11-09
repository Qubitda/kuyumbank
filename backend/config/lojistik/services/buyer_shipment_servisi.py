"""F6-023 — Alıcı sevkiyat yüzeyi (maskeli; tedarikçi/maliyet yok)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from firmalar.services.yetki_servisi import can_view_all_tenants
from lojistik.models import Shipment
from siparis.models import Order


class ShipmentNotFound(LookupError):
    pass


def _assert_buyer_or_ops(actor) -> None:
    if can_view_all_tenants(actor):
        return
    firma = getattr(actor, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied("Sevkiyat yalnız alıcı veya platform ops içindir.")


def scope_shipment_queryset(qs, actor):
    """Tenant: alıcı kendi sipariş sevkiyatı; ops tümü. Client firma_id yok."""
    if can_view_all_tenants(actor):
        return qs
    firma = getattr(actor, "firma", None)
    if firma is None:
        return qs.none()
    return qs.filter(order__alici_firma_id=firma.pk)


def get_shipment_for_actor(actor, *, shipment_id: int) -> Shipment:
    _assert_buyer_or_ops(actor)
    qs = Shipment.objects.select_related("order").filter(pk=shipment_id)
    qs = scope_shipment_queryset(qs, actor)
    ship = qs.first()
    if ship is None:
        raise ShipmentNotFound()
    return ship


def list_for_order(actor, *, order: Order) -> list[Shipment]:
    _assert_buyer_or_ops(actor)
    if not can_view_all_tenants(actor):
        firma = getattr(actor, "firma", None)
        if firma is None or order.alici_firma_id != firma.pk:
            raise ShipmentNotFound()
    return list(
        Shipment.objects.filter(order=order).order_by("-olusturma_tarihi", "-pk")
    )


def present_shipment(ship: Shipment) -> dict:
    """Kör havuz: tedarikçi/warehouse/maliyet yok."""
    from lojistik.models import ProofOfDelivery

    pod = ProofOfDelivery.objects.filter(shipment_id=ship.pk).first()
    data = {
        "id": ship.pk,
        "order_id": ship.order_id,
        "durum": ship.durum,
        "takip_no": ship.takip_no,
        "olusturma_tarihi": ship.olusturma_tarihi.isoformat()
        if ship.olusturma_tarihi
        else None,
        "pod": None,
    }
    if pod is not None:
        data["pod"] = {
            "teslim_alan": pod.teslim_alan,
            "olusturma_tarihi": pod.olusturma_tarihi.isoformat()
            if pod.olusturma_tarihi
            else None,
            "belgeler_ref": pod.belgeler_ref or "",
        }
    return data
