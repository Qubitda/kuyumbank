"""B4 — org / onay / RFQ sunum (maske + allowed_actions)."""

from __future__ import annotations

from django.utils import timezone

from api.masking import assert_masked
from firmalar.models import OnayTalebi, OrgBirimi, OrgUyeligi
from siparis.models import RFQ


def present_org(ob: OrgBirimi, *, can_manage: bool = False) -> dict:
    actions = []
    if can_manage and ob.aktif:
        actions.append("add_member")
    data = {
        "id": ob.pk,
        "kod": ob.kod,
        "ad": ob.ad,
        "aktif": ob.aktif,
        "parent_id": ob.parent_id,
        "firma_id": ob.firma_id,
        "allowed_actions": actions,
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_org_member(uy: OrgUyeligi) -> dict:
    data = {
        "id": uy.pk,
        "org_birimi_id": uy.org_birimi_id,
        "kullanici_id": uy.kullanici_id,
        "olusturma_tarihi": uy.olusturma_tarihi.isoformat()
        if uy.olusturma_tarihi
        else None,
        "allowed_actions": ["view"],
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_onay(ot: OnayTalebi, *, can_manage: bool = False) -> dict:
    # SM geçişleri public Durum sabitleriyle (servis private _TRANSITIONS yok).
    actions: list[str] = []
    if can_manage:
        if ot.durum == OnayTalebi.Durum.TASLAK:
            actions.extend(["submit", "reject"])
        elif ot.durum == OnayTalebi.Durum.BEKLEMEDE:
            actions.extend(["approve", "reject"])
    data = {
        "id": ot.pk,
        "durum": ot.durum,
        "tutar": str(ot.tutar),
        "para_birimi": ot.para_birimi,
        "gerekce": ot.gerekce or "",
        "org_birimi_id": ot.org_birimi_id,
        "order_id": ot.order_id,
        "olusturma_tarihi": ot.olusturma_tarihi.isoformat()
        if ot.olusturma_tarihi
        else None,
        "allowed_actions": actions,
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_rfq(rfq: RFQ) -> dict:
    lines = [
        {
            "id": ln.pk,
            "aciklama": ln.aciklama,
            "miktar": str(ln.miktar),
            "birim": ln.birim,
            "varyant_id": ln.varyant_id,
            "katalog_disi": ln.varyant_id is None,
        }
        for ln in rfq.lines.all().order_by("pk")
    ]
    messages = [
        {
            "id": m.pk,
            "govde": m.govde,
            "gonderen_rol": m.gonderen_rol,
            "olusturma_tarihi": m.olusturma_tarihi.isoformat()
            if m.olusturma_tarihi
            else None,
        }
        for m in rfq.messages.all().order_by("pk")
    ]
    revizyonlar = [
        {
            "sira": r.sira,
            "ozet": r.ozet,
            "gonderen_rol": r.gonderen_rol,
            "olusturma_tarihi": r.olusturma_tarihi.isoformat()
            if r.olusturma_tarihi
            else None,
        }
        for r in rfq.revizyonlar.all().order_by("sira")
    ]
    actions: list[str] = []
    if rfq.durum == RFQ.Durum.TASLAK:
        actions.append("send")
    if rfq.durum in {RFQ.Durum.TASLAK, RFQ.Durum.GONDERILDI}:
        actions.append("add_message")
    if (
        rfq.talep_tipi == RFQ.TalepTipi.OZEL_URETIM
        and rfq.durum in {RFQ.Durum.TASLAK, RFQ.Durum.GONDERILDI}
    ):
        actions.append("add_revision")
    # KAPANDI/IPTAL action yok — servis fonksiyonu yok (uydurulmaz).
    data = {
        "id": rfq.pk,
        "baslik": rfq.baslik,
        "talep_tipi": rfq.talep_tipi,
        "durum": rfq.durum,
        "sube_id": rfq.sube_id,
        "lines": lines,
        "messages": messages,
        "revizyonlar": revizyonlar,
        "allowed_actions": actions,
        "olusturma_tarihi": rfq.olusturma_tarihi.isoformat()
        if rfq.olusturma_tarihi
        else None,
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data
