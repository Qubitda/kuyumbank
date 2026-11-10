"""F9-010 — Alıcı dashboard özeti (tenant context; kör havuz)."""

from __future__ import annotations

from api.masking import assert_masked
from siparis.models import Order, RFQ
from siparis.selectors.rfq import scope_rfq_queryset
from siparis.selectors.tenant import scope_order_queryset
from siparis.services import cart_servisi


def ozet_for_actor(*, actor) -> dict:
    """Auth + firma/rol context + sayaçlar. Tedarikçi/maliyet yok."""
    firma = getattr(actor, "firma", None)
    cart = cart_servisi.al_veya_olustur_sepet(actor=actor)
    order_qs = scope_order_queryset(Order.objects.all(), actor)
    rfq_qs = scope_rfq_queryset(RFQ.objects.all(), actor)
    data = {
        "username": getattr(actor, "username", "") or "",
        "rol": getattr(actor, "rol", "") or "",
        "firma_id": getattr(actor, "firma_id", None),
        "firma_ad": getattr(firma, "ad", "") if firma is not None else "",
        "firma_kodu": getattr(firma, "firma_kodu", "") if firma is not None else "",
        "cart_id": cart.pk,
        "cart_line_count": cart.lines.count(),
        "order_count": order_qs.count(),
        "rfq_count": rfq_qs.count(),
        "rfq_ozel_count": rfq_qs.filter(talep_tipi=RFQ.TalepTipi.OZEL_URETIM).count(),
    }
    assert_masked(data)
    return data
