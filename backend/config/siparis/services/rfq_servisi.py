"""F10-020 — RFQ SM (kör havuz; kimlik mesajda yok)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.org_servisi import assert_org_in_firma
from firmalar.services.yetki_servisi import require_perm
from siparis.models import RFQ, RFQLine, RFQMessage

_TRANSITIONS = {
    RFQ.Durum.TASLAK: {RFQ.Durum.GONDERILDI, RFQ.Durum.IPTAL},
    RFQ.Durum.GONDERILDI: {RFQ.Durum.KAPANDI, RFQ.Durum.IPTAL},
    RFQ.Durum.KAPANDI: set(),
    RFQ.Durum.IPTAL: set(),
}


def _require(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(actor, P["manage_rfq"])
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="RFQ",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def olustur(
    *,
    actor,
    baslik: str,
    line_specs: list[dict],
    sube=None,
) -> RFQ:
    _require(actor, action="siparis.rfq.create_denied")
    firma = getattr(actor, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied("RFQ yalnız alıcı firma için.")
    assert_org_in_firma(org=sube, firma=firma)
    if not line_specs:
        raise ValidationError("En az bir RFQ satırı gerekir.")

    with domain_atomic():
        rfq = RFQ(
            alici_firma=firma,
            sube=sube,
            baslik=(baslik or "").strip()[:200] or "RFQ",
            durum=RFQ.Durum.TASLAK,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        rfq.save()
        for spec in line_specs:
            miktar = spec.get("miktar")
            if not isinstance(miktar, Decimal):
                miktar = Decimal(str(miktar))
            RFQLine(
                rfq=rfq,
                aciklama=(spec.get("aciklama") or "")[:255],
                miktar=miktar,
                birim=spec.get("birim") or "ADET",
                varyant=spec.get("varyant"),
            ).save()
        record_audit(
            actor=actor,
            action="siparis.rfq.created",
            entity_type="RFQ",
            entity_id=str(rfq.pk),
            success=True,
            detail={"line_count": len(line_specs)},
        )
        return rfq


def _set(rfq: RFQ, yeni: str) -> RFQ:
    allowed = _TRANSITIONS.get(rfq.durum, set())
    if yeni not in allowed:
        raise ValidationError(f"Geçersiz RFQ geçişi: {rfq.durum} → {yeni}.")
    rfq.durum = yeni
    rfq._allow_status_transition = True
    try:
        rfq.save(update_fields=["durum", "guncelleme_tarihi"])
    finally:
        rfq._allow_status_transition = False
    return rfq


def gonder(*, actor, rfq: RFQ) -> RFQ:
    _require(actor, action="siparis.rfq.transition_denied", entity_id=str(rfq.pk))
    with domain_atomic():
        locked = RFQ.objects.select_for_update().get(pk=rfq.pk)
        _set(locked, RFQ.Durum.GONDERILDI)
        record_audit(
            actor=actor,
            action="siparis.rfq.gonderildi",
            entity_type="RFQ",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def mesaj_ekle(*, actor, rfq: RFQ, govde: str) -> RFQMessage:
    _require(actor, action="siparis.rfq.message_denied", entity_id=str(rfq.pk))
    text = (govde or "").strip()
    if len(text) < 2:
        raise ValidationError("Mesaj çok kısa.")
    with domain_atomic():
        msg = RFQMessage(
            rfq=rfq,
            govde=text[:2000],
            gonderen_rol=getattr(actor, "rol", "") or "",
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        msg.save()
        record_audit(
            actor=actor,
            action="siparis.rfq.message",
            entity_type="RFQMessage",
            entity_id=str(msg.pk),
            success=True,
            detail={"rfq_id": rfq.pk, "gonderen_rol": msg.gonderen_rol},
        )
        return msg
