"""
Saf Python fiyat hesaplama. Django'ya bağımlı DEĞİL — birim test kolay olsun.

Kural:
- Tüm hesap Decimal. Ara adımda yuvarlama yok; sadece sonda.
- Yüzde tabanı: `islcilik_dahil_mi` True ise metal+işçilik, değilse metal.
- TL_GR: marj = gram × marj_degeri
- TL_PARCA: marj = marj_degeri (parça başı)
- Toplam = metal + işçilik + marj + taş bedeli
"""

from decimal import Decimal, ROUND_HALF_UP

ISTENED_HASSASIYET = Decimal("0.01")


def _d(x) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def hesapla(
    *,
    gram: Decimal,
    milyem: Decimal,
    saf_birim_fiyat: Decimal,
    marj_tipi: str,
    marj_degeri: Decimal,
    iscilik: Decimal = Decimal("0"),
    islcilik_dahil_mi: bool = False,
    tas_bedeli: Decimal = Decimal("0"),
) -> dict:
    """
    Dönen sözlük:
      - metal_bedeli, iscilik, marj, tas_bedeli, toplam : ham (yuvarlanmamış)
      - toplam_yuvarlanmis, metal_bedeli_yuvarlanmis, ... : gösterim için
      - taban (yüzde için hesaplanan taban)

    Not: milyem, 0.0-1.0 aralığında oran olarak beklenir (ör. 0.585 = 14K, 0.995 = 24K).
    """
    gram = _d(gram)
    milyem = _d(milyem)
    saf_birim_fiyat = _d(saf_birim_fiyat)
    marj_degeri = _d(marj_degeri)
    iscilik = _d(iscilik)
    tas_bedeli = _d(tas_bedeli)

    # 1) Metal bedeli
    # milyem 0.0-1.0 aralığında saklanır (ör. 0.585 = 14K, 0.995 = 24K).
    metal_bedeli = gram * milyem * saf_birim_fiyat

    # 2) Marj
    taban = Decimal("0")
    if marj_tipi == "YUZDE":
        taban = metal_bedeli + (iscilik if islcilik_dahil_mi else Decimal("0"))
        marj = taban * (marj_degeri / Decimal("100"))
    elif marj_tipi == "TL_GR":
        marj = gram * marj_degeri
    elif marj_tipi == "TL_PARCA":
        marj = marj_degeri
    else:
        raise ValueError(f"Geçersiz marj_tipi: {marj_tipi!r}")

    toplam = metal_bedeli + iscilik + marj + tas_bedeli

    def y_round(d: Decimal) -> Decimal:
        return d.quantize(ISTENED_HASSASIYET, rounding=ROUND_HALF_UP)

    return {
        "metal_bedeli": metal_bedeli,
        "iscilik": iscilik,
        "marj": marj,
        "tas_bedeli": tas_bedeli,
        "taban": taban,
        "toplam": toplam,
        "metal_bedeli_yuvarlanmis": y_round(metal_bedeli),
        "marj_yuvarlanmis": y_round(marj),
        "toplam_yuvarlanmis": y_round(toplam),
    }
