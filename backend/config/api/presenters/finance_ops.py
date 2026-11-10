"""B3 — finans / sevkiyat / iade sunum (maske + allowed_actions)."""

from __future__ import annotations

from django.utils import timezone

from api.masking import assert_masked
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from firmalar.role_permissions import P
from finans.models import CariHesap, LedgerEntry, PaymentIntent
from finans.services import buyer_finans_servisi
from lojistik.models import ReturnRequest, Shipment
from lojistik.services.buyer_shipment_servisi import present_shipment as _raw_ship
from lojistik.services.return_servisi import _TRANSITIONS


def BuyerShipmentPresenter(ship: Shipment) -> dict:
    data = _raw_ship(ship)
    actions = []
    if ship.durum == Shipment.Durum.TESLIM:
        actions.append("request_return")
    data["allowed_actions"] = actions
    data["server_now"] = timezone.now().isoformat()
    assert_masked(data)
    return data


def BuyerFinancePresenter(data: dict) -> dict:
    out = dict(data)
    out["allowed_actions"] = ["view_credit", "create_payment_intent", "view_cari", "view_ledger"]
    out["server_now"] = timezone.now().isoformat()
    buyer_finans_servisi.assert_masked(out)
    assert_masked(out)
    return out


def BuyerCariPresenter(hesap: CariHesap) -> dict:
    data = {
        "id": hesap.pk,
        "para_birimi": hesap.para_birimi,
        "bakiye": str(hesap.bakiye),
        "kredi_limiti": str(hesap.kredi_limiti),
        "guncelleme_tarihi": (
            hesap.guncelleme_tarihi.isoformat() if hesap.guncelleme_tarihi else None
        ),
        "allowed_actions": ["view"],
        "server_now": timezone.now().isoformat(),
    }
    buyer_finans_servisi.assert_masked(data)
    assert_masked(data)
    return data


def BuyerLedgerPresenter(entry: LedgerEntry) -> dict:
    data = {
        "id": entry.pk,
        "yon": entry.yon,
        "tutar": str(entry.tutar),
        "para_birimi": entry.para_birimi,
        "hareket_tipi": entry.hareket_tipi,
        "referans_tip": entry.referans_tip,
        "referans_id": entry.referans_id,
        "olusturma_tarihi": (
            entry.olusturma_tarihi.isoformat() if entry.olusturma_tarihi else None
        ),
        "allowed_actions": ["view"],
        "server_now": timezone.now().isoformat(),
    }
    buyer_finans_servisi.assert_masked(data)
    assert_masked(data)
    return data


def BuyerPaymentIntentPresenter(pi: PaymentIntent) -> dict:
    data = buyer_finans_servisi.present_payment_intent_masked(pi)
    actions = []
    if pi.durum == PaymentIntent.Durum.BEKLEMEDE:
        actions.append("await_settlement")
    data["allowed_actions"] = actions
    data["server_now"] = timezone.now().isoformat()
    buyer_finans_servisi.assert_masked(data)
    assert_masked(data)
    return data


def present_return(req: ReturnRequest, *, actor=None) -> dict:
    lines = [
        {
            "id": ln.pk,
            "order_line_id": ln.order_line_id,
            "miktar": str(ln.miktar),
            "birim": ln.birim,
        }
        for ln in req.lines.all().order_by("pk")
    ]
    next_states = sorted(_TRANSITIONS.get(req.durum, set()))
    actions: list[str] = []
    can_manage = False
    if actor is not None:
        can_manage = has_perm(actor, P["manage_return"]) or can_view_all_tenants(
            actor
        )
    if can_manage:
        if ReturnRequest.Durum.INCELENIYOR in next_states:
            actions.append("submit_review")
        if ReturnRequest.Durum.ONAYLANDI in next_states:
            actions.append("approve")
        if ReturnRequest.Durum.REDDEDILDI in next_states:
            actions.append("reject")
        if ReturnRequest.Durum.IPTAL in next_states:
            actions.append("cancel")
    can_mahsup = False
    if actor is not None:
        can_mahsup = has_perm(actor, P["post_ledger"]) and (
            can_manage or can_view_all_tenants(actor)
        )
    if (
        can_mahsup
        and req.durum == ReturnRequest.Durum.ONAYLANDI
        and not req.finans_mahsup_yapildi
    ):
        actions.append("mahsup")
    data = {
        "id": req.pk,
        "order_id": req.order_id,
        "shipment_id": req.shipment_id,
        "durum": req.durum,
        "sebep": req.sebep,
        "lines": lines,
        "allowed_actions": actions,
        "server_now": timezone.now().isoformat(),
        "olusturma_tarihi": req.olusturma_tarihi.isoformat()
        if req.olusturma_tarihi
        else None,
    }
    if can_manage or can_mahsup:
        data["stok_iade_yapildi"] = req.stok_iade_yapildi
        data["finans_mahsup_yapildi"] = req.finans_mahsup_yapildi
    assert_masked(data)
    return data
