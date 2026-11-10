"""ADR-0018 CP-12 — XAUUSDT×USDTTRY implied vs TCMB USDTRY."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from tanimlar.fiyat_kaynagi import ARA_QUANT
from tanimlar.services.kur_servisi import get_or_create_politikasi

_Q = Decimal(ARA_QUANT)


def _q(v: Decimal) -> Decimal:
    return Decimal(v).quantize(_Q, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CaprazSonuc:
    ok: bool
    implied_usdtry: Decimal | None
    tcmb_usdtry: Decimal | None
    makas_yuzde: Decimal | None
    esik_yuzde: Decimal
    neden: str = ""


def capraz_makas_kontrol(
    *,
    xauusdt: Decimal,
    usdttry: Decimal,
    tcmb_usdtry: Decimal,
    esik_yuzde: Decimal | None = None,
) -> CaprazSonuc:
    """Aşımda ok=False — yeni anlık aktif olmaz; LKG korunur."""
    pol = get_or_create_politikasi()
    esik = Decimal(str(esik_yuzde if esik_yuzde is not None else pol.capraz_makas_esigi_yuzde))
    x = Decimal(str(xauusdt))
    u = Decimal(str(usdttry))
    t = Decimal(str(tcmb_usdtry))
    if x <= 0 or u <= 0 or t <= 0:
        return CaprazSonuc(
            ok=False,
            implied_usdtry=None,
            tcmb_usdtry=t if t > 0 else None,
            makas_yuzde=None,
            esik_yuzde=esik,
            neden="Sıfır/negatif kur; çapraz red.",
        )
    # implied USDTRY ≈ USDTTRY (XAUUSDT metal; çapraz FX = USDTTRY vs TCMB)
    implied = _q(u)
    tcmb_q = _q(t)
    makas = _q(abs(implied - tcmb_q) / tcmb_q * Decimal("100"))
    if makas > esik:
        return CaprazSonuc(
            ok=False,
            implied_usdtry=implied,
            tcmb_usdtry=tcmb_q,
            makas_yuzde=makas,
            esik_yuzde=esik,
            neden=f"Çapraz makas %{makas} > eşik %{esik}.",
        )
    return CaprazSonuc(
        ok=True,
        implied_usdtry=implied,
        tcmb_usdtry=tcmb_q,
        makas_yuzde=makas,
        esik_yuzde=esik,
    )
