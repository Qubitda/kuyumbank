"""Alıcı/ops API sunum DTO — kör havuz (tedarikçi/maliyet yok)."""

from __future__ import annotations

from siparis.models import Order, OrderLine
from siparis.services.cart_servisi import present_cart_line


def present_order_line(line: OrderLine) -> dict:
    return {
        "id": line.pk,
        "varyant_id": line.varyant_id,
        "miktar": str(line.miktar),
        "birim": line.birim,
        "snapshot_birim_fiyat_vergisiz": str(line.snapshot_birim_fiyat_vergisiz),
        "snapshot_satir_tutari_vergisiz": str(line.snapshot_satir_tutari_vergisiz),
        "para_birimi": line.para_birimi,
    }


def present_order(order: Order, *, include_lines: bool = True) -> dict:
    data = {
        "id": order.pk,
        "durum": order.durum,
        "alici_firma_id": order.alici_firma_id,
        "idempotency_key": order.idempotency_key,
        "olusturma_tarihi": order.olusturma_tarihi.isoformat()
        if order.olusturma_tarihi
        else None,
        "line_count": order.lines.count(),
    }
    if include_lines:
        data["lines"] = [
            present_order_line(ln) for ln in order.lines.all().order_by("pk")
        ]
    return data


def present_cart(cart, *, include_lines: bool = True) -> dict:
    data = {
        "id": cart.pk,
        "alici_firma_id": cart.alici_firma_id,
        "line_count": cart.lines.count(),
    }
    if include_lines:
        data["lines"] = [
            present_cart_line(ln) for ln in cart.lines.select_related("price_quote")
        ]
    return data
