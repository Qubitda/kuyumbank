"""
Saf Python fiyat hesaplama (ADR-0008 §2.1.1, Dilim 3.4).

Django'ya bağımlı DEĞİL. Orkestrasyon: `pricing_service.quote` (Dilim 3.5).
B-01 platform_servis kalemi kodlanmaz. B-06 vergi yok.

Kurallar:
- Tüm hesap Decimal; ara adımda yuvarlama yok.
- Final satır + toplam_vergisiz: quantize (TRY: 0.01, HALF_UP).
- milyem: 0–1 oran (ör. 0.585 = 14K) — /1000 uygulanmaz.
- METAL_BAZLI: metal = gram × milyem × saf_birim_fiyat
- GRAM_BIRIM: gram_birim = gram × birim_fiyat (metal satırı yok)
- SABIT_PARCA: sabit_parca = birim_fiyat (gram çarpılmaz)
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

ISTENED_HASSASIYET = Decimal("0.01")
ROUNDING = ROUND_HALF_UP

FIYAT_MODELLERI = frozenset({"METAL_BAZLI", "GRAM_BIRIM", "SABIT_PARCA", "HEDEF_TOPLAM"})
MARJ_TIPLERI = frozenset({"YUZDE", "TL_GR", "TL_PARCA"})


def _d(x) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _q(d: Decimal, *, hassasiyet: Decimal = ISTENED_HASSASIYET) -> Decimal:
    return d.quantize(hassasiyet, rounding=ROUNDING)


def _assert_pozitif(ad: str, deger: Decimal, *, sifir_ok: bool = False) -> None:
    if sifir_ok:
        if deger < 0:
            raise ValueError(f"{ad} negatif olamaz.")
    elif deger <= 0:
        raise ValueError(f"{ad} sıfırdan büyük olmalıdır.")


def _marj_hesapla(
    *,
    marj_tipi: str,
    marj_degeri: Decimal,
    taban: Decimal,
    gram: Decimal,
    iscilik: Decimal,
    islcilik_dahil_mi: bool,
) -> tuple[Decimal, Decimal]:
    """Döner: (marj, yuzde_taban)."""
    if marj_tipi not in MARJ_TIPLERI:
        raise ValueError(f"Geçersiz marj_tipi: {marj_tipi!r}")
    marj_degeri = _d(marj_degeri)
    if marj_degeri < 0:
        raise ValueError("marj_degeri negatif olamaz.")
    yuzde_taban = Decimal("0")
    if marj_tipi == "YUZDE":
        yuzde_taban = taban + (iscilik if islcilik_dahil_mi else Decimal("0"))
        marj = yuzde_taban * (marj_degeri / Decimal("100"))
    elif marj_tipi == "TL_GR":
        _assert_pozitif("gram (TL_GR marj)", gram)
        marj = gram * marj_degeri
    else:  # TL_PARCA
        marj = marj_degeri
    return marj, yuzde_taban


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
    Geriye dönük METAL_BAZLI çekirdek (ek_bedel yok).

    Dönen sözlük: metal_bedeli, iscilik, marj, tas_bedeli, toplam (ham) +
    *_yuvarlanmis alanları.
    """
    gram = _d(gram)
    milyem = _d(milyem)
    saf_birim_fiyat = _d(saf_birim_fiyat)
    iscilik = _d(iscilik)
    tas_bedeli = _d(tas_bedeli)

    _assert_pozitif("gram", gram)
    if milyem <= 0 or milyem > 1:
        raise ValueError("milyem 0 ile 1 arasında (0 hariç, 1 dahil) oran olmalıdır.")
    _assert_pozitif("saf_birim_fiyat", saf_birim_fiyat)
    if iscilik < 0:
        raise ValueError("iscilik negatif olamaz.")
    if tas_bedeli < 0:
        raise ValueError("tas_bedeli negatif olamaz.")

    metal_bedeli = gram * milyem * saf_birim_fiyat
    marj, taban = _marj_hesapla(
        marj_tipi=marj_tipi,
        marj_degeri=marj_degeri,
        taban=metal_bedeli,
        gram=gram,
        iscilik=iscilik,
        islcilik_dahil_mi=islcilik_dahil_mi,
    )
    toplam = metal_bedeli + iscilik + marj + tas_bedeli

    return {
        "metal_bedeli": metal_bedeli,
        "iscilik": iscilik,
        "marj": marj,
        "tas_bedeli": tas_bedeli,
        "taban": taban,
        "toplam": toplam,
        "metal_bedeli_yuvarlanmis": _q(metal_bedeli),
        "marj_yuvarlanmis": _q(marj),
        "toplam_yuvarlanmis": _q(toplam),
    }


def _sonuc_paketle(
    *,
    fiyat_modeli: str,
    para_birimi: str,
    kalemler: dict[str, Decimal],
    taban: Decimal,
    hassasiyet: Decimal,
) -> dict[str, Any]:
    """Kalemler ham; toplam_vergisiz yuvarlanmış."""
    toplam_ham = sum(kalemler.values(), Decimal("0"))
    kalemler_yuvarlanmis = {k: _q(v, hassasiyet=hassasiyet) for k, v in kalemler.items()}
    return {
        "fiyat_modeli": fiyat_modeli,
        "para_birimi": para_birimi,
        "kalemler": kalemler,
        "kalemler_yuvarlanmis": kalemler_yuvarlanmis,
        "taban": taban,
        "toplam": toplam_ham,
        "toplam_vergisiz": _q(toplam_ham, hassasiyet=hassasiyet),
        "toplam_yuvarlanmis": _q(toplam_ham, hassasiyet=hassasiyet),
        # Geriye dönük alias’lar (METAL_BAZLI testleri / eski çağrılar)
        "metal_bedeli": kalemler.get("metal", Decimal("0")),
        "iscilik": kalemler.get("iscilik", Decimal("0")),
        "marj": kalemler.get("kanal_marj", Decimal("0")),
        "tas_bedeli": kalemler.get("tas", Decimal("0")),
        "ek_bedel": kalemler.get("ek_bedel", Decimal("0")),
        "metal_bedeli_yuvarlanmis": kalemler_yuvarlanmis.get("metal", _q(Decimal("0"))),
        "marj_yuvarlanmis": kalemler_yuvarlanmis.get("kanal_marj", _q(Decimal("0"))),
    }


def hesapla_metal_bazli(
    *,
    gram: Decimal,
    milyem: Decimal,
    saf_birim_fiyat: Decimal,
    marj_tipi: str,
    marj_degeri: Decimal,
    iscilik: Decimal = Decimal("0"),
    islcilik_dahil_mi: bool = False,
    tas_bedeli: Decimal = Decimal("0"),
    ek_bedel: Decimal = Decimal("0"),
    para_birimi: str = "TRY",
    hassasiyet: Decimal | None = None,
) -> dict[str, Any]:
    """ADR-0008 METAL_BAZLI — platform_servis yok (B-01)."""
    hassasiyet = hassasiyet or ISTENED_HASSASIYET
    ek_bedel = _d(ek_bedel)
    if ek_bedel < 0:
        raise ValueError("ek_bedel negatif olamaz.")

    base = hesapla(
        gram=gram,
        milyem=milyem,
        saf_birim_fiyat=saf_birim_fiyat,
        marj_tipi=marj_tipi,
        marj_degeri=marj_degeri,
        iscilik=iscilik,
        islcilik_dahil_mi=islcilik_dahil_mi,
        tas_bedeli=tas_bedeli,
    )
    kalemler = {
        "metal": base["metal_bedeli"],
        "iscilik": base["iscilik"],
        "kanal_marj": base["marj"],
        "tas": base["tas_bedeli"],
        "ek_bedel": ek_bedel,
    }
    return _sonuc_paketle(
        fiyat_modeli="METAL_BAZLI",
        para_birimi=para_birimi,
        kalemler=kalemler,
        taban=base["taban"],
        hassasiyet=hassasiyet,
    )


def hesapla_gram_birim(
    *,
    gram: Decimal,
    birim_fiyat: Decimal,
    marj_tipi: str,
    marj_degeri: Decimal,
    tas_bedeli: Decimal = Decimal("0"),
    ek_bedel: Decimal = Decimal("0"),
    islcilik_dahil_mi: bool = False,
    para_birimi: str = "TRY",
    hassasiyet: Decimal | None = None,
) -> dict[str, Any]:
    """ADR-0008 GRAM_BIRIM — metal satırı yok; platform_servis yok (B-01)."""
    hassasiyet = hassasiyet or ISTENED_HASSASIYET
    gram = _d(gram)
    birim_fiyat = _d(birim_fiyat)
    tas_bedeli = _d(tas_bedeli)
    ek_bedel = _d(ek_bedel)

    _assert_pozitif("gram", gram)
    _assert_pozitif("birim_fiyat", birim_fiyat)
    if tas_bedeli < 0 or ek_bedel < 0:
        raise ValueError("tas_bedeli/ek_bedel negatif olamaz.")

    gram_birim = gram * birim_fiyat
    # GRAM_BIRIM’de ayrı işçilik satırı yok; YUZDE tabanı = gram_birim
    marj, taban = _marj_hesapla(
        marj_tipi=marj_tipi,
        marj_degeri=marj_degeri,
        taban=gram_birim,
        gram=gram,
        iscilik=Decimal("0"),
        islcilik_dahil_mi=False,
    )
    del islcilik_dahil_mi  # modelde işçilik satırı yok
    kalemler = {
        "gram_birim": gram_birim,
        "kanal_marj": marj,
        "tas": tas_bedeli,
        "ek_bedel": ek_bedel,
    }
    return _sonuc_paketle(
        fiyat_modeli="GRAM_BIRIM",
        para_birimi=para_birimi,
        kalemler=kalemler,
        taban=taban,
        hassasiyet=hassasiyet,
    )


def hesapla_sabit_parca(
    *,
    birim_fiyat: Decimal,
    marj_tipi: str,
    marj_degeri: Decimal,
    gram: Decimal | None = None,
    tas_bedeli: Decimal = Decimal("0"),
    ek_bedel: Decimal = Decimal("0"),
    para_birimi: str = "TRY",
    hassasiyet: Decimal | None = None,
) -> dict[str, Any]:
    """ADR-0008 SABIT_PARCA — gram fiyatı çarpmaz; TL_GR marj için gram gerekir."""
    hassasiyet = hassasiyet or ISTENED_HASSASIYET
    birim_fiyat = _d(birim_fiyat)
    tas_bedeli = _d(tas_bedeli)
    ek_bedel = _d(ek_bedel)
    gram_d = _d(gram) if gram is not None else Decimal("0")

    _assert_pozitif("birim_fiyat", birim_fiyat)
    if tas_bedeli < 0 or ek_bedel < 0:
        raise ValueError("tas_bedeli/ek_bedel negatif olamaz.")

    sabit_parca = birim_fiyat
    marj, taban = _marj_hesapla(
        marj_tipi=marj_tipi,
        marj_degeri=marj_degeri,
        taban=sabit_parca,
        gram=gram_d,
        iscilik=Decimal("0"),
        islcilik_dahil_mi=False,
    )
    kalemler = {
        "sabit_parca": sabit_parca,
        "kanal_marj": marj,
        "tas": tas_bedeli,
        "ek_bedel": ek_bedel,
    }
    return _sonuc_paketle(
        fiyat_modeli="SABIT_PARCA",
        para_birimi=para_birimi,
        kalemler=kalemler,
        taban=taban,
        hassasiyet=hassasiyet,
    )


def hesapla_hedef_toplam(
    *,
    hedef_toplam: Decimal,
    gram: Decimal,
    para_birimi: str = "TRY",
    hassasiyet: Decimal | None = None,
) -> dict[str, Any]:
    """ADR-0014 KS-6 — quote toplamı = hedef; banka/GV/işletme yok (KS-4).

    Tek kalem `hedef_toplam`. Marj/metal yeniden hesaplanmaz; örtük gr satış
    yalnız denetim için `hesap_girdisi`'ne yazılır (çağıran).
    """
    hassasiyet = hassasiyet or ISTENED_HASSASIYET
    hedef = _d(hedef_toplam)
    gram = _d(gram)
    _assert_pozitif("hedef_toplam", hedef)
    _assert_pozitif("gram", gram)
    kalemler = {"hedef_toplam": hedef}
    return _sonuc_paketle(
        fiyat_modeli="HEDEF_TOPLAM",
        para_birimi=para_birimi,
        kalemler=kalemler,
        taban=hedef,
        hassasiyet=hassasiyet,
    )


def hesapla_modele_gore(fiyat_modeli: str, **kwargs) -> dict[str, Any]:
    """Modelleri tek girişten seçer (`pricing_service.quote` tüketir)."""
    if fiyat_modeli not in FIYAT_MODELLERI:
        raise ValueError(f"Geçersiz fiyat_modeli: {fiyat_modeli!r}")
    if fiyat_modeli == "METAL_BAZLI":
        return hesapla_metal_bazli(**kwargs)
    if fiyat_modeli == "GRAM_BIRIM":
        return hesapla_gram_birim(**kwargs)
    if fiyat_modeli == "HEDEF_TOPLAM":
        return hesapla_hedef_toplam(**kwargs)
    return hesapla_sabit_parca(**kwargs)
