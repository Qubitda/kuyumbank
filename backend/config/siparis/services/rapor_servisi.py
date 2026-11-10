"""F11-010 / F11-021 — Ticari + alıcı davranış raporları (NOTE-F11-001 RM-1…6).

Canlı ORM aggregate; CQRS yok; kör havuz; client firma_id yok.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import record_audit_durable
from firmalar.services.yetki_servisi import can_view_all_tenants, require_perm
from fiyatlama.models import PriceQuote
from siparis.models import Order, OrderLine


def _deny(actor, *, action: str, reason: str):
    record_audit_durable(
        actor=actor,
        action=action,
        entity_type="Rapor",
        entity_id="",
        success=False,
        reason=reason,
    )
    raise PermissionDenied(reason)


def _resolve_alici_scope(actor, alici_firma_id: int | None) -> int | None:
    """Platform: opsiyonel filtre; alıcı: yalnız kendi firma (zorunlu)."""
    firma = getattr(actor, "firma", None)
    if can_view_all_tenants(actor) and firma and getattr(firma, "platform_mu", False):
        try:
            require_perm(
                actor, P["manage_sozlesme"], message="Ticari rapor yetkisi yok."
            )
        except PermissionDenied:
            _deny(actor, action="siparis.rapor.denied", reason="yetki_yok")
        return int(alici_firma_id) if alici_firma_id is not None else None
    if firma is None or not getattr(firma, "alici_mi", False):
        _deny(
            actor,
            action="siparis.rapor.denied",
            reason="Rapor yalnız alıcı veya platform finans.",
        )
    # Alıcı — client firma_id yok sayılır
    return int(firma.pk)


def ticari_siparis_ozet(
    *,
    actor,
    alici_firma_id: int | None = None,
) -> dict:
    """F11-010 — sipariş adet + ciro (satır snapshot); çapraz tenant yok."""
    scope_id = _resolve_alici_scope(actor, alici_firma_id)
    orders = Order.objects.all()
    if scope_id is not None:
        orders = orders.filter(alici_firma_id=scope_id)
    o_agg = orders.aggregate(
        siparis_adet=Count("pk"),
        olusturuldu=Count(
            "pk", filter=Q(durum=Order.Durum.OLUSTURULDU)
        ),
        iptal=Count("pk", filter=Q(durum=Order.Durum.IPTAL)),
    )
    lines = OrderLine.objects.filter(order__in=orders)
    l_agg = lines.aggregate(
        ciro=Coalesce(Sum("snapshot_satir_tutari_vergisiz"), Decimal("0")),
        satir_adet=Count("pk"),
    )
    return {
        "scope": "Order+OrderLine",
        "alici_firma_id": scope_id,
        "siparis_adet": int(o_agg["siparis_adet"] or 0),
        "siparis_olusturuldu": int(o_agg["olusturuldu"] or 0),
        "siparis_iptal": int(o_agg["iptal"] or 0),
        "satir_adet": int(l_agg["satir_adet"] or 0),
        "ciro_vergisiz": str(l_agg["ciro"] or Decimal("0")),
        "read_model": "live_orm",
    }


def alici_davranis_ozet(
    *,
    actor,
    alici_firma_id: int | None = None,
) -> dict:
    """F11-021 — alıcı firma kesitli sipariş + quote özeti (kör)."""
    scope_id = _resolve_alici_scope(actor, alici_firma_id)
    if scope_id is None:
        raise ValidationError(
            {"alici_firma_id": "Alıcı davranış özeti için firma kesiti zorunlu."}
        )
    orders = Order.objects.filter(alici_firma_id=scope_id)
    o_agg = orders.aggregate(siparis_adet=Count("pk"))
    lines = OrderLine.objects.filter(order__alici_firma_id=scope_id)
    l_agg = lines.aggregate(
        ciro=Coalesce(Sum("snapshot_satir_tutari_vergisiz"), Decimal("0")),
        satir_adet=Count("pk"),
    )
    quotes = PriceQuote.objects.filter(alici_firma_id=scope_id)
    q_agg = quotes.aggregate(
        quote_adet=Count("pk"),
        quote_sum=Coalesce(Sum("toplam_vergisiz"), Decimal("0")),
    )
    return {
        "scope": "buyer_behavior",
        "alici_firma_id": scope_id,
        "siparis_adet": int(o_agg["siparis_adet"] or 0),
        "satir_adet": int(l_agg["satir_adet"] or 0),
        "ciro_vergisiz": str(l_agg["ciro"] or Decimal("0")),
        "quote_adet": int(q_agg["quote_adet"] or 0),
        "quote_toplam_sum": str(q_agg["quote_sum"] or Decimal("0")),
        "read_model": "live_orm",
    }
