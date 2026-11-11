"""F10-013 — OnayTalebi SM."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import OnayTalebi
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm

_TRANSITIONS = {
    OnayTalebi.Durum.TASLAK: {OnayTalebi.Durum.BEKLEMEDE, OnayTalebi.Durum.REDDEDILDI},
    OnayTalebi.Durum.BEKLEMEDE: {
        OnayTalebi.Durum.ONAYLANDI,
        OnayTalebi.Durum.REDDEDILDI,
    },
    OnayTalebi.Durum.ONAYLANDI: set(),
    OnayTalebi.Durum.REDDEDILDI: set(),
}


def _require(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(actor, P["manage_approval"])
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="OnayTalebi",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def olustur(
    *,
    actor,
    firma,
    tutar: Decimal,
    para_birimi: str = "TRY",
    org_birimi=None,
    order=None,
    gerekce: str = "",
    idempotency_key: str = "",
) -> OnayTalebi:
    _require(actor, action="firmalar.onay.create_denied")
    if tutar <= 0:
        raise ValidationError({"tutar": "Pozitif olmalı."})
    key = (idempotency_key or "").strip()[:64]
    if key:
        existing = OnayTalebi.objects.filter(
            firma=firma, idempotency_key=key
        ).first()
        if existing is not None:
            return existing
    with domain_atomic():
        ot = OnayTalebi(
            firma=firma,
            org_birimi=org_birimi,
            order=order,
            durum=OnayTalebi.Durum.TASLAK,
            tutar=tutar,
            para_birimi=(para_birimi or "TRY").upper(),
            gerekce=gerekce or "",
            idempotency_key=key,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        ot.save()
        record_audit(
            actor=actor,
            action="firmalar.onay.created",
            entity_type="OnayTalebi",
            entity_id=str(ot.pk),
            success=True,
            detail={"tutar": str(ot.tutar)},
        )
        return ot


def _set_durum(ot: OnayTalebi, yeni: str, *, update_fields=None) -> OnayTalebi:
    allowed = _TRANSITIONS.get(ot.durum, set())
    if yeni not in allowed:
        raise ValidationError(f"Geçersiz onay geçişi: {ot.durum} → {yeni}.")
    ot.durum = yeni
    fields = list(update_fields or ["durum", "guncelleme_tarihi"])
    if "durum" not in fields:
        fields.append("durum")
    if "guncelleme_tarihi" not in fields:
        fields.append("guncelleme_tarihi")
    ot._allow_status_transition = True
    try:
        ot.save(update_fields=fields)
    finally:
        ot._allow_status_transition = False
    return ot


def beklemede_al(*, actor, onay: OnayTalebi) -> OnayTalebi:
    _require(actor, action="firmalar.onay.transition_denied", entity_id=str(onay.pk))
    with domain_atomic():
        locked = OnayTalebi.objects.select_for_update().get(pk=onay.pk)
        _set_durum(locked, OnayTalebi.Durum.BEKLEMEDE)
        record_audit(
            actor=actor,
            action="firmalar.onay.beklemede",
            entity_type="OnayTalebi",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def onayla(*, actor, onay: OnayTalebi) -> OnayTalebi:
    _require(actor, action="firmalar.onay.transition_denied", entity_id=str(onay.pk))
    with domain_atomic():
        locked = OnayTalebi.objects.select_for_update().get(pk=onay.pk)
        locked.karar_veren = actor if getattr(actor, "pk", None) else None
        _set_durum(
            locked,
            OnayTalebi.Durum.ONAYLANDI,
            update_fields=["durum", "karar_veren", "guncelleme_tarihi"],
        )
        record_audit(
            actor=actor,
            action="firmalar.onay.onaylandi",
            entity_type="OnayTalebi",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def reddet(*, actor, onay: OnayTalebi, reason: str = "") -> OnayTalebi:
    _require(actor, action="firmalar.onay.transition_denied", entity_id=str(onay.pk))
    with domain_atomic():
        locked = OnayTalebi.objects.select_for_update().get(pk=onay.pk)
        locked.karar_veren = actor if getattr(actor, "pk", None) else None
        fields = ["durum", "karar_veren", "guncelleme_tarihi"]
        if reason:
            locked.gerekce = (
                (locked.gerekce + " | " if locked.gerekce else "") + reason[:200]
            )
            fields.append("gerekce")
        _set_durum(
            locked,
            OnayTalebi.Durum.REDDEDILDI,
            update_fields=fields,
        )
        record_audit(
            actor=actor,
            action="firmalar.onay.reddedildi",
            entity_type="OnayTalebi",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum, "reason": reason[:120]},
        )
        return locked
