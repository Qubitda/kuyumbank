"""B6 — Tedarikçi DTO; ters kör havuz (alıcı kimliği yok)."""

from __future__ import annotations

from django.utils import timezone

from api.masking import assert_masked
from fiyatlama.models import TedarikciTeklif
from siparis.models import RFQ
from stok.models import StockBalance, StockMovement


def present_offer(teklif: TedarikciTeklif, *, can_manage: bool = False) -> dict:
    """Kendi teklifi — fiyat alanları tedarikçiye açık; alıcı kimliği yok."""
    actions: list[str] = []
    if can_manage:
        if teklif.durum == TedarikciTeklif.Durum.TASLAK:
            actions.append("submit")
        if teklif.durum == TedarikciTeklif.Durum.YAYINDA:
            actions.extend(["deactivate", "new_version"])
    data = {
        "id": teklif.pk,
        "varyant_id": teklif.varyant_id,
        "tedarikci_kodu": teklif.tedarikci_kodu,
        "versiyon": teklif.versiyon,
        "durum": teklif.durum,
        "fiyat_modeli": teklif.fiyat_modeli,
        "gram": str(teklif.gram) if teklif.gram is not None else None,
        "birim_fiyat": str(teklif.birim_fiyat)
        if teklif.birim_fiyat is not None
        else None,
        "para_birimi": teklif.para_birimi,
        "gecerlilik_baslangic": teklif.gecerlilik_baslangic.isoformat()
        if teklif.gecerlilik_baslangic
        else None,
        "gecerlilik_bitis": teklif.gecerlilik_bitis.isoformat()
        if teklif.gecerlilik_bitis
        else None,
        "allowed_actions": actions,
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_balance(bal: StockBalance) -> dict:
    item = {
        "warehouse_id": bal.warehouse_id,
        "teklif_id": bal.teklif_id,
        "varyant_id": bal.varyant_id,
        "birim": bal.birim,
        "on_hand": str(bal.on_hand),
        "reserved": str(bal.reserved),
        "blocked": str(bal.blocked),
        "available": str(bal.available),
    }
    assert_masked(item)
    return item


def present_movement(mv: StockMovement) -> dict:
    item = {
        "id": mv.pk,
        "warehouse_id": mv.warehouse_id,
        "teklif_id": mv.teklif_id,
        "varyant_id": mv.varyant_id,
        "birim": mv.birim,
        "miktar": str(mv.miktar),
        "tip": mv.tip,
        "neden": mv.neden,
    }
    assert_masked(item)
    return item


def present_rfq_supplier(rfq: RFQ) -> dict:
    """Ters kör: RFQ içeriği var; alıcı firma / şube kimliği yok."""
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
    if rfq.durum == RFQ.Durum.GONDERILDI:
        actions.append("add_message")
        if rfq.talep_tipi == RFQ.TalepTipi.OZEL_URETIM:
            actions.append("add_revision")
    data = {
        "id": rfq.pk,
        "baslik": rfq.baslik,
        "talep_tipi": rfq.talep_tipi,
        "durum": rfq.durum,
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
