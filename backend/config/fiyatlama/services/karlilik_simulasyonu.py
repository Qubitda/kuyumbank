"""Perakende / iç P&L simülatörü (ADR-0014).

Excel A/B: gr maliyet + marj veya hedef toplam → net kar (banka/GV dahil).
KS-6: ticari quote için `pricing_service.quote(hedef_toplam=...)` — banka/GV
quote'a girmez (KS-4). B-01/B-06 bu modülde yok.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_CENT = Decimal("0.01")
_Q4 = Decimal("0.0001")
_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def _d(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _q2(v: Decimal) -> Decimal:
    return _d(v).quantize(_CENT, rounding=ROUND_HALF_UP)


def _q4(v: Decimal) -> Decimal:
    return _d(v).quantize(_Q4, rounding=ROUND_HALF_UP)


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


def simule_marj_pct(
    *,
    maden_fiyati: Decimal,
    iscilik_tl: Decimal,
    agirlik_gr: Decimal,
    kar_pct: Decimal,
    banka_pct: Decimal = Decimal("2"),
    isletme_pct: Decimal = Decimal("1"),
    gelir_vergisi_pct: Decimal = Decimal("20"),
    diger_kesintiler: Decimal = Decimal("0"),
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
        banka_pct=_d(banka_pct),
        isletme_pct=_d(isletme_pct),
        gv_pct=_d(gelir_vergisi_pct),
        diger=_d(diger_kesintiler),
        mod="MARJ_PCT",
    )


def simule_hedef_toplam(
    *,
    maden_fiyati: Decimal,
    iscilik_tl: Decimal,
    agirlik_gr: Decimal,
    hedef_toplam: Decimal,
    banka_pct: Decimal = Decimal("2"),
    isletme_pct: Decimal = Decimal("1"),
    gelir_vergisi_pct: Decimal = Decimal("20"),
    diger_kesintiler: Decimal = Decimal("0"),
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
        banka_pct=_d(banka_pct),
        isletme_pct=_d(isletme_pct),
        gv_pct=_d(gelir_vergisi_pct),
        diger=_d(diger_kesintiler),
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
    banka_pct: Decimal,
    isletme_pct: Decimal,
    gv_pct: Decimal,
    diger: Decimal,
    mod: str,
) -> KarlilikSonuc:
    maliyet_toplam = _q2(gr_maliyet * gram)
    brut = _q2(toplam - maliyet_toplam)
    brut_pct = _q4(
        (brut / toplam * _HUNDRED) if toplam else _ZERO
    )
    banka = _q2(toplam * banka_pct / _HUNDRED)
    isletme = _q2(toplam * isletme_pct / _HUNDRED)
    # GV: brut - banka - isletme - diger üzerinden (Excel benzeri)
    matrah = brut - banka - isletme - diger
    if matrah < 0:
        matrah = _ZERO
    gv = _q2(matrah * gv_pct / _HUNDRED)
    net = _q2(brut - banka - isletme - gv - diger)
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
        banka_kesinti=banka,
        isletme_gideri=isletme,
        gelir_vergisi=gv,
        diger_kesintiler=_q2(diger),
        net_kar=net,
        net_kar_marji_pct=net_pct,
        mod=mod,
    )
