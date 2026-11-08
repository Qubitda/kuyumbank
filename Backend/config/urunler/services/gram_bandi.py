"""Varyant gram bandı hesabı (ADR-0005 K3, ADR-0006 B4a)."""

from decimal import Decimal

from django.conf import settings


def varyant_gram_bandi(varyant) -> tuple[Decimal | None, Decimal | None]:
    """(min, max) — override alanları veya gram ± oran; gramsızda (None, None)."""
    if varyant.gram_bandi_min is not None and varyant.gram_bandi_max is not None:
        return Decimal(varyant.gram_bandi_min), Decimal(varyant.gram_bandi_max)
    if varyant.gram is None:
        return None, None
    oran = Decimal(str(getattr(settings, "VARYANT_GRAM_BANDI_ORAN", "0.05")))
    g = Decimal(varyant.gram)
    return g * (Decimal("1") - oran), g * (Decimal("1") + oran)


def teklif_gram_band_uygun_mu(teklif, varyant=None) -> bool:
    """Teklif gramı hedef varyant bandındaysa True; gramsız teklif/varyant → True (atlanır)."""
    varyant = varyant or teklif.varyant
    if teklif.gram is None:
        return True
    lo, hi = varyant_gram_bandi(varyant)
    if lo is None or hi is None:
        return True
    g = Decimal(teklif.gram)
    return lo <= g <= hi
