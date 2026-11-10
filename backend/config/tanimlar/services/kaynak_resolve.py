"""ADR-0018 CP-1 — ürün → ayar → politika fiyat kaynağı precedence."""

from __future__ import annotations

from tanimlar.fiyat_kaynagi import FiyatKaynagi
from tanimlar.services.kur_servisi import get_or_create_politikasi


def etkin_kaynak(*, urun) -> str:
    """CANLI_PIYASA | MANUEL_GIRIS — MIRAS çözülür; soft uydurma yok."""
    u = (getattr(urun, "fiyat_kaynagi", None) or FiyatKaynagi.MIRAS).strip()
    if u in {FiyatKaynagi.CANLI_PIYASA, FiyatKaynagi.MANUEL_GIRIS}:
        return u
    ayar = getattr(urun, "ayar", None)
    a = (getattr(ayar, "fiyat_kaynagi", None) or FiyatKaynagi.MIRAS).strip()
    if a in {FiyatKaynagi.CANLI_PIYASA, FiyatKaynagi.MANUEL_GIRIS}:
        return a
    pol = get_or_create_politikasi()
    p = (pol.fiyat_kaynagi or FiyatKaynagi.CANLI_PIYASA).strip()
    if p not in {FiyatKaynagi.CANLI_PIYASA, FiyatKaynagi.MANUEL_GIRIS}:
        return FiyatKaynagi.CANLI_PIYASA
    return p
