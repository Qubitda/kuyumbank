"""Stok birimi — U-002 / ADR-0011 F4-A12.

Karar: birim = teklif `fiyat_modeli` birincil birimi.
Farklı birimler birbirine dönüştürülmez / toplanmaz (sessiz varsayım yok).
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

from fiyatlama.models import TedarikciTeklif
from stok.birim_constants import StokBirimi

_FIYAT_MODELI_BIRIM = {
    TedarikciTeklif.FiyatModeli.SABIT_PARCA: StokBirimi.ADET,
    TedarikciTeklif.FiyatModeli.METAL_BAZLI: StokBirimi.GRAM,
    TedarikciTeklif.FiyatModeli.GRAM_BIRIM: StokBirimi.GRAM,
}


def birim_from_fiyat_modeli(fiyat_modeli: str) -> str:
    """Teklif fiyat modelinden stok birimi. Bilinmeyen model → hata (tahmin yok)."""
    try:
        return _FIYAT_MODELI_BIRIM[fiyat_modeli]
    except KeyError as exc:
        raise ValidationError(
            {
                "fiyat_modeli": (
                    f"Stok birimi eşlemesi yok: {fiyat_modeli!r}. "
                    "Birimler arası dönüşüm Faz 4'te yok (U-002)."
                )
            }
        ) from exc


def birim_from_teklif(teklif: TedarikciTeklif) -> str:
    return birim_from_fiyat_modeli(teklif.fiyat_modeli)


def assert_ayni_birim(a: str, b: str, *, context: str = "") -> None:
    """Farklı birimlerin karıştırılmasını reddeder; dönüşüm yapmaz."""
    if a != b:
        suffix = f" ({context})" if context else ""
        raise ValidationError(
            f"Stok birimleri uyuşmuyor: {a} ≠ {b}{suffix}. "
            "Dönüşüm yok — ayrı balance satırı gerekir (U-002)."
        )
