"""F11-010 / F11-021 — Ticari + alıcı davranış raporları (NOTE-F11-001 RM-1…6).

Canlı ORM aggregate; CQRS yok; kör havuz; client firma_id yok.
Zorunlu tarih aralığı (varsayılan son 90 gün, max 366) — tam tablo tarama yok.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import record_audit_durable
from firmalar.services.yetki_servisi import can_view_all_tenants, require_perm
from fiyatlama.models import PriceQuote
from siparis.models import Order, OrderLine

DEFAULT_RANGE_DAYS = 90
MAX_RANGE_DAYS = 366


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


def _parse_day(raw, *, field: str) -> date | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError as exc:
        raise ValidationError({field: "ISO tarih beklenir (YYYY-MM-DD)."}) from exc


def resolve_date_range(
    *,
    date_from=None,
    date_to=None,
    default_days: int = DEFAULT_RANGE_DAYS,
    max_days: int = MAX_RANGE_DAYS,
) -> tuple[date, date]:
    """Kapalı aralık [from, to]; boşsa son default_days; max_days aşımı → 400."""
    today = timezone.localdate()
    d_to = _parse_day(date_to, field="date_to") or today
    d_from = _parse_day(date_from, field="date_from") or (
        d_to - timedelta(days=default_days - 1)
    )
    if d_from > d_to:
        raise ValidationError({"date_from": "date_from ≤ date_to olmalı."})
    span = (d_to - d_from).days + 1
    if span > max_days:
        raise ValidationError(
            {
                "date_to": (
                    f"Tarih aralığı en fazla {max_days} gün "
                    f"(istenilen: {span})."
                )
            }
        )
    return d_from, d_to


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
    date_from=None,
    date_to=None,
) -> dict:
    """F11-010 — sipariş adet + ciro (satır snapshot); çapraz tenant yok."""
    scope_id = _resolve_alici_scope(actor, alici_firma_id)
    d_from, d_to = resolve_date_range(date_from=date_from, date_to=date_to)
    orders = Order.objects.filter(
        olusturma_tarihi__date__gte=d_from,
        olusturma_tarihi__date__lte=d_to,
    )
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
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
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
    date_from=None,
    date_to=None,
) -> dict:
    """F11-021 — alıcı firma kesitli sipariş + quote özeti (kör)."""
    scope_id = _resolve_alici_scope(actor, alici_firma_id)
    if scope_id is None:
        raise ValidationError(
            {"alici_firma_id": "Alıcı davranış özeti için firma kesiti zorunlu."}
        )
    d_from, d_to = resolve_date_range(date_from=date_from, date_to=date_to)
    orders = Order.objects.filter(
        alici_firma_id=scope_id,
        olusturma_tarihi__date__gte=d_from,
        olusturma_tarihi__date__lte=d_to,
    )
    o_agg = orders.aggregate(siparis_adet=Count("pk"))
    lines = OrderLine.objects.filter(order__in=orders)
    l_agg = lines.aggregate(
        ciro=Coalesce(Sum("snapshot_satir_tutari_vergisiz"), Decimal("0")),
        satir_adet=Count("pk"),
    )
    quotes = PriceQuote.objects.filter(
        alici_firma_id=scope_id,
        olusturma_tarihi__date__gte=d_from,
        olusturma_tarihi__date__lte=d_to,
    )
    q_agg = quotes.aggregate(
        quote_adet=Count("pk"),
        quote_sum=Coalesce(Sum("toplam_vergisiz"), Decimal("0")),
    )
    return {
        "scope": "buyer_behavior",
        "alici_firma_id": scope_id,
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "siparis_adet": int(o_agg["siparis_adet"] or 0),
        "satir_adet": int(l_agg["satir_adet"] or 0),
        "ciro_vergisiz": str(l_agg["ciro"] or Decimal("0")),
        "quote_adet": int(q_agg["quote_adet"] or 0),
        "quote_toplam_sum": str(q_agg["quote_sum"] or Decimal("0")),
        "read_model": "live_orm",
    }
