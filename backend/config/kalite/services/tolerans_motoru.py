"""F6-011 / ADR-0013 F6-K3 — gram tolerans motoru (Decimal; float yok).

İzin verilen sapma = max(beklenen × pct/100, abs_taban).
ADET sayımı: dönüşüm yok; tam eşitlik (izin=0).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from siparis.birim_constants import SepetBirimi

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")
_Q6 = Decimal("0.000001")


def _q6(value: Decimal) -> Decimal:
    return _d(value).quantize(_Q6, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class ToleransSonuc:
    beklenen: Decimal
    olculen: Decimal
    sapma_abs: Decimal
    izin_verilen: Decimal
    tolerans_pct: Decimal
    tolerans_abs: Decimal
    uygun: bool


def _d(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def izin_verilen_sapma(
    *,
    beklenen: Decimal,
    birim: str,
    tolerans_pct: Decimal,
    tolerans_abs: Decimal,
) -> Decimal:
    """Bağıl ±% + isteğe bağlı mutlak taban (F6-K3). ADET → 0."""
    beklenen = _d(beklenen)
    if beklenen <= 0:
        raise ValidationError({"beklenen": "Beklenen değer pozitif olmalı."})
    if birim == SepetBirimi.ADET:
        return _ZERO
    pct = _d(tolerans_pct)
    abs_t = _d(tolerans_abs)
    if pct < 0 or abs_t < 0:
        raise ValidationError("Tolerans negatif olamaz.")
    bagil = beklenen * pct / _HUNDRED
    return _q6(max(bagil, abs_t))


def degerlendir(
    *,
    beklenen: Decimal,
    olculen: Decimal,
    birim: str,
    tolerans_pct: Decimal,
    tolerans_abs: Decimal,
) -> ToleransSonuc:
    beklenen = _q6(_d(beklenen))
    olculen = _q6(_d(olculen))
    if olculen < 0:
        raise ValidationError({"olculen": "Ölçülen değer negatif olamaz."})
    izin = izin_verilen_sapma(
        beklenen=beklenen,
        birim=birim,
        tolerans_pct=tolerans_pct,
        tolerans_abs=tolerans_abs,
    )
    sapma = _q6(abs(olculen - beklenen))
    return ToleransSonuc(
        beklenen=beklenen,
        olculen=olculen,
        sapma_abs=sapma,
        izin_verilen=izin,
        tolerans_pct=_d(tolerans_pct),
        tolerans_abs=_d(tolerans_abs),
        uygun=sapma <= izin,
    )
