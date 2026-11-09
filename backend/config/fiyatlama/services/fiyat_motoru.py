"""Dilim 3.4 — üç model hesap + PB dönüşüm yardımcıları.

Orkestrasyon: `pricing_service.quote` (Dilim 3.5) bu modülü tüketir.
Girdiler zaten çözülmüş Decimal’lar veya teklif PB’sinden hedef PB’ye çevrilmiş tutarlar.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tanimlar.models import KurTaraf
from tanimlar.services.currency_conversion import ConversionResult, convert

from fiyatlama.services import fiyat_hesaplama


def cevir_tutari(
    amount,
    *,
    kaynak_pb: str,
    hedef_pb: str,
    taraf: str = KurTaraf.ALICI,
    gozlem=None,
    gozlem_hedef=None,
    now=None,
) -> ConversionResult:
    """K-012: tüm PB dönüşümleri currency_conversion üzerinden."""
    return convert(
        amount,
        kaynak_pb=kaynak_pb,
        hedef_pb=hedef_pb,
        taraf=taraf,
        gozlem=gozlem,
        gozlem_hedef=gozlem_hedef,
        now=now,
    )


def hesapla_teklif_kalemleri(
    *,
    fiyat_modeli: str,
    hedef_para_birimi: str = "TRY",
    # METAL
    gram: Decimal | None = None,
    milyem: Decimal | None = None,
    saf_birim_fiyat: Decimal | None = None,
    iscilik: Decimal = Decimal("0"),
    islcilik_dahil_mi: bool = False,
    # GRAM / SABIT
    birim_fiyat: Decimal | None = None,
    birim_fiyat_pb: str | None = None,
    # ortak
    marj_tipi: str,
    marj_degeri: Decimal,
    tas_bedeli: Decimal = Decimal("0"),
    ek_bedel: Decimal = Decimal("0"),
    taraf: str = KurTaraf.ALICI,
    doviz_gozlem=None,
    now=None,
) -> dict[str, Any]:
    """
    Model hesabı; birim_fiyat kaynak PB ≠ hedef ise dönüştürülür.
    metal saf_birim_fiyat ve ek_bedel/tas_bedeli hedef PB’de beklenir
    (metal kuru zaten TRY/gr — hedef TRY dışı ise çağıran dönüştürmüş olmalı).
    """
    bf = birim_fiyat
    donusum_meta: dict[str, Any] = {}
    if fiyat_modeli in ("GRAM_BIRIM", "SABIT_PARCA") and bf is not None:
        src = (birim_fiyat_pb or hedef_para_birimi).upper()
        if src != hedef_para_birimi.upper():
            conv = cevir_tutari(
                bf,
                kaynak_pb=src,
                hedef_pb=hedef_para_birimi,
                taraf=taraf,
                gozlem=doviz_gozlem,
                now=now,
            )
            bf = conv.tutar
            donusum_meta = {
                "birim_fiyat_kaynak_pb": conv.kaynak_pb,
                "birim_fiyat_hedef_pb": conv.hedef_pb,
                "birim_fiyat_efektif_carpan": conv.efektif_carpan,
                "birim_fiyat_gozlem_idler": conv.gozlem_idler,
            }

    kwargs: dict[str, Any] = {
        "marj_tipi": marj_tipi,
        "marj_degeri": marj_degeri,
        "tas_bedeli": tas_bedeli,
        "ek_bedel": ek_bedel,
        "para_birimi": hedef_para_birimi,
    }
    if fiyat_modeli == "METAL_BAZLI":
        sonuc = fiyat_hesaplama.hesapla_metal_bazli(
            gram=gram,
            milyem=milyem,
            saf_birim_fiyat=saf_birim_fiyat,
            iscilik=iscilik,
            islcilik_dahil_mi=islcilik_dahil_mi,
            **kwargs,
        )
    elif fiyat_modeli == "GRAM_BIRIM":
        sonuc = fiyat_hesaplama.hesapla_gram_birim(
            gram=gram,
            birim_fiyat=bf,
            **kwargs,
        )
    elif fiyat_modeli == "SABIT_PARCA":
        sonuc = fiyat_hesaplama.hesapla_sabit_parca(
            birim_fiyat=bf,
            gram=gram,
            **kwargs,
        )
    elif fiyat_modeli == "HEDEF_TOPLAM":
        # KS-6: birim_fiyat = hedef_toplam (çağıran doldurur)
        if bf is None:
            raise ValueError("HEDEF_TOPLAM için birim_fiyat (hedef_toplam) zorunlu.")
        sonuc = fiyat_hesaplama.hesapla_hedef_toplam(
            hedef_toplam=bf,
            gram=gram if gram is not None else Decimal("0"),
            para_birimi=hedef_para_birimi,
        )
    else:
        raise ValueError(f"Geçersiz fiyat_modeli: {fiyat_modeli!r}")

    if donusum_meta:
        sonuc["pb_donusum"] = donusum_meta
    return sonuc
