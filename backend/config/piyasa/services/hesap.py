"""Piyasa panosu saf hesap — Django yok.

Katman 1 (pano / GoldXT sağ panel):
  ham = ölçek×PB formülü (GRAM/ONS/KG × TRY/USD)
  alış = ham − TL  veya  ham × (1 − %/100)
  satış = ham + TL  veya  ham × (1 + %/100)
  nihai = yuvarla(...)

Katman 2 (kullanıcı ekleri, isteğe bağlı): baz birimin üstüne ek; bazı değiştirmez.
"""

from __future__ import annotations

from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_UP,
    Decimal,
)
from typing import Any

ALIS = "ALIS"
SATIS = "SATIS"
TL = "TL"
YUZDE = "YUZDE"
YOK = "YOK"
PB_GRAM = "PB_GRAM"
PB_ADET = "PB_ADET"
YAKIN = "YAKIN"
YUKARI = "YUKARI"
ASAGI = "ASAGI"
GRAM = "GRAM"
ONS = "ONS"
KG = "KG"
TRY = "TRY"
USD = "USD"

TARAFLAR = frozenset({ALIS, SATIS})
MARJ_MODLARI = frozenset({TL, YUZDE})
TIPLER = frozenset({YOK, YUZDE, PB_GRAM, PB_ADET})
OLCEKLER = frozenset({GRAM, ONS, KG})
CIKTI_PB = frozenset({TRY, USD})
HASSASIYET = Decimal("0.01")
_SIFIR = Decimal("0")
_YUZ = Decimal("100")
_BIN = Decimal("1000")
# tanimlar.fiyat_kaynagi.TROY_OZ_GRAM ile aynı (Django’suz kopya)
TROY_OZ_GRAM = Decimal("31.1035")
_YUVARLAMA = {YAKIN: ROUND_HALF_UP, YUKARI: ROUND_CEILING, ASAGI: ROUND_FLOOR}


def _d(x) -> Decimal:
    if x is None:
        return _SIFIR
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _q(d: Decimal, hassasiyet: Decimal = HASSASIYET) -> Decimal:
    return d.quantize(hassasiyet, rounding=ROUND_HALF_UP)


def yuvarla(deger, adim, yontem: str = YAKIN) -> Decimal:
    deger, adim = _d(deger), _d(adim)
    if adim <= 0:
        return deger
    if yontem not in _YUVARLAMA:
        raise ValueError(f"Geçersiz yuvarlama yöntemi: {yontem!r}")
    return (deger / adim).quantize(Decimal(1), rounding=_YUVARLAMA[yontem]) * adim


def uygula_pano_marj(
    ham,
    *,
    taraf: str,
    marj_modu: str,
    alis_marj=0,
    satis_marj=0,
) -> Decimal:
    """GoldXT `applyMarginResult`: alış marjı düşer, satış marjı ekler (değerler ≥0)."""
    if taraf not in TARAFLAR:
        raise ValueError(f"Geçersiz taraf: {taraf!r}")
    if marj_modu not in MARJ_MODLARI:
        raise ValueError(f"Geçersiz marj modu: {marj_modu!r}")
    ham = _d(ham)
    alis_m = _d(alis_marj)
    satis_m = _d(satis_marj)
    if alis_m < 0 or satis_m < 0:
        raise ValueError("Alış/satış marjı negatif olamaz.")
    if taraf == ALIS:
        if marj_modu == TL:
            return ham - alis_m
        if alis_m >= _YUZ:
            raise ValueError("Alış yüzde marjı 100'den küçük olmalı.")
        return ham * (_YUZ - alis_m) / _YUZ
    # SATIS
    if marj_modu == TL:
        return ham + satis_m
    if satis_m >= _YUZ:
        raise ValueError("Satış yüzde marjı 100'den küçük olmalı.")
    return ham * (_YUZ + satis_m) / _YUZ


def hesapla_ham(
    *,
    saf_birim_fiyat,
    milyem,
    miktar,
    olcek: str = GRAM,
    cikti_pb: str = TRY,
    usd_try=None,
) -> Decimal:
    """Ölçek + çıktı PB → ham (marj öncesi). saf = TRY/gram metal kuru."""
    olcek = (olcek or GRAM).upper()
    cikti_pb = (cikti_pb or TRY).upper()
    if olcek not in OLCEKLER:
        raise ValueError(f"Geçersiz olcek: {olcek!r}")
    if cikti_pb not in CIKTI_PB:
        raise ValueError(f"Geçersiz cikti_pb: {cikti_pb!r}")
    saf = _d(saf_birim_fiyat)
    milyem = _d(milyem)
    miktar = _d(miktar)
    if saf <= 0:
        raise ValueError("saf_birim_fiyat sıfırdan büyük olmalı.")
    if not (_SIFIR < milyem <= 1):
        raise ValueError("milyem (0, 1] aralığında olmalı.")
    if miktar <= 0:
        raise ValueError("miktar sıfırdan büyük olmalı.")

    if olcek == GRAM:
        ham_try = saf * milyem * miktar
    elif olcek == KG:
        ham_try = saf * milyem * _BIN * miktar
    else:  # ONS
        ham_try = saf * TROY_OZ_GRAM * milyem * miktar

    if cikti_pb == TRY:
        return ham_try
    usd = _d(usd_try)
    if usd <= 0:
        raise ValueError("USD çıktı için usd_try (TRY/USD) zorunlu ve pozitif.")
    return ham_try / usd


def hesapla_taraf(
    *,
    taraf: str,
    saf_birim_fiyat,
    milyem,
    gram,
    marj_modu: str = YUZDE,
    alis_marj=0,
    satis_marj=0,
    yuvarlama_adimi=0,
    yuvarlama_yontemi: str = YAKIN,
    olcek: str = GRAM,
    cikti_pb: str = TRY,
    usd_try=None,
    hassasiyet: Decimal = HASSASIYET,
) -> dict[str, Any]:
    """Ham → pano marjı → yuvarlama → nihai (tek taraf)."""
    if taraf not in TARAFLAR:
        raise ValueError(f"Geçersiz taraf: {taraf!r}")

    ham = hesapla_ham(
        saf_birim_fiyat=saf_birim_fiyat,
        milyem=milyem,
        miktar=gram,
        olcek=olcek,
        cikti_pb=cikti_pb,
        usd_try=usd_try,
    )
    marjli = uygula_pano_marj(
        ham,
        taraf=taraf,
        marj_modu=marj_modu,
        alis_marj=alis_marj,
        satis_marj=satis_marj,
    )
    nihai = yuvarla(marjli, yuvarlama_adimi, yuvarlama_yontemi)
    if nihai <= 0:
        raise ValueError("Nihai fiyat ≤ 0; marj/yuvarlama kontrol edin.")

    return {
        "taraf": taraf,
        "olcek": (olcek or GRAM).upper(),
        "cikti_pb": (cikti_pb or TRY).upper(),
        "ham": _q(ham, hassasiyet),
        "marjli": _q(marjli, hassasiyet),
        "nihai": _q(nihai, hassasiyet),
    }


def _bilesen(*, ad: str, tip: str, deger, kur, taban: Decimal, gram: Decimal) -> Decimal:
    if tip not in TIPLER:
        raise ValueError(f"Geçersiz {ad} tipi: {tip!r}")
    if tip == YOK:
        return _SIFIR
    deger = _d(deger)
    if tip == YUZDE:
        if deger <= -_YUZ:
            raise ValueError(f"{ad} yüzdesi -100'den büyük olmalı.")
        return taban * deger / _YUZ
    kur = _d(kur)
    if kur <= 0:
        raise ValueError(f"{ad} için kur sıfırdan büyük olmalı.")
    if tip == PB_GRAM:
        return deger * kur * gram
    return deger * kur


def kullanici_fiyati(
    *,
    baz_birim_fiyat,
    agirlik_gr,
    iscilik: dict | None = None,
    servis_bedeli: dict | None = None,
    marj: dict | None = None,
    hassasiyet: Decimal = HASSASIYET,
) -> dict[str, Any]:
    """Katman 2 — kullanıcının kendi ekleri (pano bazını ezmez)."""
    baz = _d(baz_birim_fiyat)
    agirlik = _d(agirlik_gr)
    if baz <= 0:
        raise ValueError("baz_birim_fiyat sıfırdan büyük olmalı.")
    if agirlik <= 0:
        raise ValueError("agirlik_gr sıfırdan büyük olmalı.")

    metal = baz * agirlik
    sonuc = {"metal_bedeli": metal}
    for ad, ek in (
        ("iscilik", iscilik),
        ("servis_bedeli", servis_bedeli),
        ("marj", marj),
    ):
        ek = ek or {}
        sonuc[ad] = _bilesen(
            ad=ad,
            tip=ek.get("tip", YOK),
            deger=ek.get("deger", 0),
            kur=ek.get("kur", 1),
            taban=metal,
            gram=agirlik,
        )
    toplam = sum(sonuc.values(), _SIFIR)
    if toplam <= 0:
        raise ValueError("Toplam sıfır veya negatif; ekleri kontrol edin.")
    sonuc["toplam"] = toplam
    sonuc["birim_toplam"] = toplam / agirlik
    return {k: _q(v, hassasiyet) for k, v in sonuc.items()}
