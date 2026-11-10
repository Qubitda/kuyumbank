"""ADR-0018 CP-10 — negatif marj / min_marj guardrail."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from tanimlar.fiyat_kaynagi import TRY_QUANT
from tanimlar.services.kur_servisi import get_or_create_politikasi

_Q = Decimal(TRY_QUANT)


@dataclass(frozen=True)
class GuardrailSonuc:
    ok: bool
    toplam: Decimal
    maliyet: Decimal
    marj_pct: Decimal | None
    neden: str = ""


def assert_marj_guardrail(
    *,
    toplam_vergisiz: Decimal,
    maliyet_referans: Decimal | None,
    min_marj_pct: Decimal | None = None,
) -> GuardrailSonuc:
    """Maliyet altında veya min_marj altı → BLOKE (quote yok)."""
    toplam = Decimal(str(toplam_vergisiz)).quantize(_Q, rounding=ROUND_HALF_UP)
    if toplam <= 0:
        raise ValidationError("toplam_vergisiz pozitif olmalı; 0 fiyat yok.")
    if maliyet_referans is None:
        return GuardrailSonuc(
            ok=True, toplam=toplam, maliyet=Decimal("0"), marj_pct=None
        )
    maliyet = Decimal(str(maliyet_referans)).quantize(_Q, rounding=ROUND_HALF_UP)
    if maliyet < 0:
        raise ValidationError("maliyet_referans negatif olamaz.")
    pol = get_or_create_politikasi()
    min_m = Decimal(
        str(min_marj_pct if min_marj_pct is not None else pol.min_marj_pct)
    )
    if toplam < maliyet:
        return GuardrailSonuc(
            ok=False,
            toplam=toplam,
            maliyet=maliyet,
            marj_pct=None,
            neden="toplam_vergisiz maliyetin altında (guardrail).",
        )
    if maliyet > 0:
        marj = ((toplam - maliyet) / maliyet * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if marj < min_m:
            return GuardrailSonuc(
                ok=False,
                toplam=toplam,
                maliyet=maliyet,
                marj_pct=marj,
                neden=f"Marj %{marj} < min %{min_m}.",
            )
        return GuardrailSonuc(
            ok=True, toplam=toplam, maliyet=maliyet, marj_pct=marj
        )
    return GuardrailSonuc(
        ok=True, toplam=toplam, maliyet=maliyet, marj_pct=None
    )
