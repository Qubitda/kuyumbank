"""Perakende / iç P&L simülatörü (ADR-0014 + ADR-0022 birimli kesinti).

Excel A/B: gr maliyet + marj veya hedef toplam → net kar (banka/GV dahil).
KS-6: ticari quote için `pricing_service.quote(hedef_toplam=...)` — banka/GV
quote'a girmez (KS-4). B-01/B-06 bu modülde yok.

Kesinti: tip YUZDE | TL + deger. Eski `banka_pct=` kwargs geriye uyumlu.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

_CENT = Decimal("0.01")
_Q4 = Decimal("0.0001")
_HUNDRED = Decimal("100")
_ZERO = Decimal("0")

YUZDE = "YUZDE"
TL = "TL"
KESINTI_TIPLERI = frozenset({YUZDE, TL})


def _d(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _q2(v: Decimal) -> Decimal:
    return _d(v).quantize(_CENT, rounding=ROUND_HALF_UP)


def _q4(v: Decimal) -> Decimal:
    return _d(v).quantize(_Q4, rounding=ROUND_HALF_UP)


def _normalize_kesinti(
    *,
    ad: str,
    tip_deger: dict | None,
    legacy_pct: Decimal | None,
    default_tip: str,
    default_deger: Decimal,
) -> tuple[str, Decimal]:
    if tip_deger is not None:
        tip = str(tip_deger.get("tip", default_tip)).upper()
        deger = _d(tip_deger.get("deger", default_deger))
    elif legacy_pct is not None:
        tip = YUZDE
        deger = _d(legacy_pct)
    else:
        tip = default_tip
        deger = _d(default_deger)
    if tip not in KESINTI_TIPLERI:
        raise ValueError(f"Geçersiz {ad} tipi: {tip!r}")
    if deger < 0:
        raise ValueError(f"{ad} değeri negatif olamaz.")
    if tip == YUZDE and deger >= _HUNDRED and ad != "gelir_vergisi":
        # GV %100 teorik mümkün; banka/işletme için üst sınır
        if ad in ("banka", "isletme", "diger"):
            raise ValueError(f"{ad} yüzde kesintisi 100'den küçük olmalı.")
    return tip, deger


def _tutar_yuzde_veya_tl(*, taban: Decimal, tip: str, deger: Decimal) -> Decimal:
    if tip == TL:
        return _q2(deger)
    return _q2(taban * deger / _HUNDRED)


@dataclass(frozen=True, slots=True)
class KarlilikSonuc:
    maden_fiyati: Decimal
    iscilik_tl: Decimal
    gr_maliyet: Decimal
    kar_gr: Decimal
    gr_satis: Decimal
    agirlik_gr: Decimal
    toplam_satis: Decimal
    brut_kar: Decimal
    brut_kar_marji_pct: Decimal
    banka_kesinti: Decimal
    isletme_gideri: Decimal
    gelir_vergisi: Decimal
    diger_kesintiler: Decimal
    net_kar: Decimal
    net_kar_marji_pct: Decimal
    mod: str  # "MARJ_PCT" | "HEDEF_TOPLAM"
    banka_tipi: str = YUZDE
    isletme_tipi: str = YUZDE
    gelir_vergisi_tipi: str = YUZDE
    diger_tipi: str = TL


def simule_marj_pct(
    *,
    maden_fiyati: Decimal,
    iscilik_tl: Decimal,
    agirlik_gr: Decimal,
    kar_pct: Decimal,
    banka_pct: Decimal | None = None,
    isletme_pct: Decimal | None = None,
    gelir_vergisi_pct: Decimal | None = None,
    diger_kesintiler: Decimal | None = None,
    banka: dict | None = None,
    isletme: dict | None = None,
    gelir_vergisi: dict | None = None,
    diger: dict | None = None,
) -> KarlilikSonuc:
    """A senaryosu: gr satış = gr maliyet × (1 + kar_pct/100)."""
    maden = _d(maden_fiyati)
    iscilik = _d(iscilik_tl)
    gram = _d(agirlik_gr)
    if gram <= 0:
        raise ValueError("agirlik_gr pozitif olmalı.")
    gr_maliyet = _q2(maden + iscilik)
    kar_gr = _q2(gr_maliyet * _d(kar_pct) / _HUNDRED)
    gr_satis = _q2(gr_maliyet + kar_gr)
    toplam = _q2(gr_satis * gram)
    return _kesintiler(
        maden=maden,
        iscilik=iscilik,
        gr_maliyet=gr_maliyet,
        kar_gr=kar_gr,
        gr_satis=gr_satis,
        gram=gram,
        toplam=toplam,
        banka=banka,
        isletme=isletme,
        gelir_vergisi=gelir_vergisi,
        diger=diger,
        banka_pct=banka_pct,
        isletme_pct=isletme_pct,
        gelir_vergisi_pct=gelir_vergisi_pct,
        diger_kesintiler=diger_kesintiler,
        mod="MARJ_PCT",
    )


def simule_hedef_toplam(
    *,
    maden_fiyati: Decimal,
    iscilik_tl: Decimal,
    agirlik_gr: Decimal,
    hedef_toplam: Decimal,
    banka_pct: Decimal | None = None,
    isletme_pct: Decimal | None = None,
    gelir_vergisi_pct: Decimal | None = None,
    diger_kesintiler: Decimal | None = None,
    banka: dict | None = None,
    isletme: dict | None = None,
    gelir_vergisi: dict | None = None,
    diger: dict | None = None,
) -> KarlilikSonuc:
    """B senaryosu: hedef toplam → ters gr satış ve örtük kar."""
    maden = _d(maden_fiyati)
    iscilik = _d(iscilik_tl)
    gram = _d(agirlik_gr)
    hedef = _d(hedef_toplam)
    if gram <= 0:
        raise ValueError("agirlik_gr pozitif olmalı.")
    if hedef <= 0:
        raise ValueError("hedef_toplam pozitif olmalı.")
    gr_maliyet = _q2(maden + iscilik)
    gr_satis = _q2(hedef / gram)
    kar_gr = _q2(gr_satis - gr_maliyet)
    toplam = _q2(hedef)
    return _kesintiler(
        maden=maden,
        iscilik=iscilik,
        gr_maliyet=gr_maliyet,
        kar_gr=kar_gr,
        gr_satis=gr_satis,
        gram=gram,
        toplam=toplam,
        banka=banka,
        isletme=isletme,
        gelir_vergisi=gelir_vergisi,
        diger=diger,
        banka_pct=banka_pct,
        isletme_pct=isletme_pct,
        gelir_vergisi_pct=gelir_vergisi_pct,
        diger_kesintiler=diger_kesintiler,
        mod="HEDEF_TOPLAM",
    )


def _kesintiler(
    *,
    maden: Decimal,
    iscilik: Decimal,
    gr_maliyet: Decimal,
    kar_gr: Decimal,
    gr_satis: Decimal,
    gram: Decimal,
    toplam: Decimal,
    banka: dict | None,
    isletme: dict | None,
    gelir_vergisi: dict | None,
    diger: dict | None,
    banka_pct: Decimal | None,
    isletme_pct: Decimal | None,
    gelir_vergisi_pct: Decimal | None,
    diger_kesintiler: Decimal | None,
    mod: str,
) -> KarlilikSonuc:
    banka_tip, banka_deg = _normalize_kesinti(
        ad="banka",
        tip_deger=banka,
        legacy_pct=banka_pct if banka is None else None,
        default_tip=YUZDE,
        default_deger=Decimal("2"),
    )
    isletme_tip, isletme_deg = _normalize_kesinti(
        ad="isletme",
        tip_deger=isletme,
        legacy_pct=isletme_pct if isletme is None else None,
        default_tip=YUZDE,
        default_deger=Decimal("1"),
    )
    gv_tip, gv_deg = _normalize_kesinti(
        ad="gelir_vergisi",
        tip_deger=gelir_vergisi,
        legacy_pct=gelir_vergisi_pct if gelir_vergisi is None else None,
        default_tip=YUZDE,
        default_deger=Decimal("20"),
    )
    if diger is not None:
        diger_tip, diger_deg = _normalize_kesinti(
            ad="diger",
            tip_deger=diger,
            legacy_pct=None,
            default_tip=TL,
            default_deger=_ZERO,
        )
    elif diger_kesintiler is not None:
        diger_tip, diger_deg = TL, _d(diger_kesintiler)
    else:
        diger_tip, diger_deg = TL, _ZERO

    maliyet_toplam = _q2(gr_maliyet * gram)
    brut = _q2(toplam - maliyet_toplam)
    brut_pct = _q4((brut / toplam * _HUNDRED) if toplam else _ZERO)

    banka_t = _tutar_yuzde_veya_tl(taban=toplam, tip=banka_tip, deger=banka_deg)
    isletme_t = _tutar_yuzde_veya_tl(taban=toplam, tip=isletme_tip, deger=isletme_deg)
    diger_t = _tutar_yuzde_veya_tl(taban=toplam, tip=diger_tip, deger=diger_deg)

    # GV: YUZDE → (brut - banka - isletme - diger) matrah; TL → sabit
    matrah = brut - banka_t - isletme_t - diger_t
    if matrah < 0:
        matrah = _ZERO
    if gv_tip == TL:
        gv = _q2(gv_deg)
    else:
        gv = _q2(matrah * gv_deg / _HUNDRED)

    net = _q2(brut - banka_t - isletme_t - gv - diger_t)
    net_pct = _q4((net / toplam * _HUNDRED) if toplam else _ZERO)
    return KarlilikSonuc(
        maden_fiyati=maden,
        iscilik_tl=iscilik,
        gr_maliyet=gr_maliyet,
        kar_gr=kar_gr,
        gr_satis=gr_satis,
        agirlik_gr=gram,
        toplam_satis=toplam,
        brut_kar=brut,
        brut_kar_marji_pct=brut_pct,
        banka_kesinti=banka_t,
        isletme_gideri=isletme_t,
        gelir_vergisi=gv,
        diger_kesintiler=_q2(diger_t),
        net_kar=net,
        net_kar_marji_pct=net_pct,
        mod=mod,
        banka_tipi=banka_tip,
        isletme_tipi=isletme_tip,
        gelir_vergisi_tipi=gv_tip,
        diger_tipi=diger_tip,
    )


def kesinti_from_any(payload: Any | None, *, default_tip: str, default_deger) -> dict:
    """Admin/servis yardımcı: dict veya düz değer → {tip, deger}."""
    if payload is None:
        return {"tip": default_tip, "deger": _d(default_deger)}
    if isinstance(payload, dict):
        return {
            "tip": str(payload.get("tip", default_tip)).upper(),
            "deger": _d(payload.get("deger", default_deger)),
        }
    return {"tip": default_tip, "deger": _d(payload)}
