"""FX / HAS açık pozisyon (ADR-0012 F5-K6) — stateless hesap."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db.models import Sum

from fiyatlama.models import PriceLock


Q4 = Decimal("0.0001")


@dataclass(frozen=True)
class HasPosition:
    locked_customer: Decimal
    unpaid_supplier: Decimal
    hedge: Decimal
    open_has: Decimal
    limit: Decimal
    over_limit: bool
    approval_required: bool


def _q4(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Q4, rounding=ROUND_HALF_UP)


def locked_customer_has() -> Decimal:
    """Interim (F5-K6): AKTİF PriceLock → quote.gram toplamı."""
    total = (
        PriceLock.objects.filter(durum=PriceLock.Durum.AKTIF)
        .aggregate(s=Sum("quote__gram"))
        .get("s")
    )
    return _q4(total if total is not None else Decimal("0"))


def unpaid_supplier_has() -> Decimal:
    """Cari/hak ediş yokken 0 (F5-K6)."""
    return Decimal("0.0000")


def open_has_position(*, limit: Decimal | None = None) -> HasPosition:
    from finans.services.hedge_servisi import hedge_has_total

    locked = locked_customer_has()
    unpaid = unpaid_supplier_has()
    hedge = _q4(hedge_has_total())
    open_has = _q4(locked - unpaid - hedge)
    if limit is None:
        raw = getattr(settings, "HAS_POSITION_LIMIT", Decimal("0"))
        limit = _q4(Decimal(str(raw)))
    else:
        limit = _q4(limit)
    over = open_has > limit if limit > 0 else False
    return HasPosition(
        locked_customer=locked,
        unpaid_supplier=unpaid,
        hedge=hedge,
        open_has=open_has,
        limit=limit,
        over_limit=over,
        approval_required=over,
    )
