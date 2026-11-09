"""F6-010 — QualityInspection SM (ADR-0013 F6-K5 / F6-K8)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from kalite.models import QualityInspection
from siparis.models import Order, OrderLine

_TRANSITIONS = {
    QualityInspection.Durum.TASLAK: {
        QualityInspection.Durum.OLCUMDE,
        QualityInspection.Durum.IPTAL,
    },
    QualityInspection.Durum.OLCUMDE: {
        QualityInspection.Durum.PASS,
        QualityInspection.Durum.FAIL,
        QualityInspection.Durum.IPTAL,
    },
    QualityInspection.Durum.PASS: set(),
    QualityInspection.Durum.FAIL: set(),
    QualityInspection.Durum.IPTAL: set(),
}


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_qc"],
            message="QC yönetimi için manage_qc gerekir.",
        )
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="QualityInspection",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def _set_durum(insp: QualityInspection, yeni: str) -> QualityInspection:
    allowed = _TRANSITIONS.get(insp.durum, set())
    if yeni not in allowed:
        raise ValidationError(
            f"Geçersiz QC geçişi: {insp.durum} → {yeni}."
        )
    insp.durum = yeni
    insp.shipment_blok = yeni == QualityInspection.Durum.FAIL
    insp._allow_status_transition = True
    try:
        insp.save(update_fields=["durum", "shipment_blok", "guncelleme_tarihi"])
    finally:
        insp._allow_status_transition = False
    return insp


def olustur(
    *,
    actor,
    order: Order,
    order_line: OrderLine | None = None,
    notlar: str = "",
) -> QualityInspection:
    _require_manage(actor, action="kalite.qc.create_denied")
    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError("QC yalnız OLUSTURULDU siparişe açılır.")
    if order_line is not None and order_line.order_id != order.pk:
        raise ValidationError("order_line bu siparişe ait değil.")

    with domain_atomic():
        insp = QualityInspection(
            order=order,
            order_line=order_line,
            durum=QualityInspection.Durum.TASLAK,
            shipment_blok=False,
            notlar=notlar or "",
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        insp.save()
        record_audit(
            actor=actor,
            action="kalite.qc.created",
            entity_type="QualityInspection",
            entity_id=str(insp.pk),
            success=True,
            detail={"order_id": order.pk, "durum": insp.durum},
        )
        return insp


def olcume_al(*, actor, inspection: QualityInspection) -> QualityInspection:
    _require_manage(
        actor,
        action="kalite.qc.transition_denied",
        entity_id=str(inspection.pk),
    )
    with domain_atomic():
        locked = QualityInspection.objects.select_for_update().get(
            pk=inspection.pk
        )
        _set_durum(locked, QualityInspection.Durum.OLCUMDE)
        record_audit(
            actor=actor,
            action="kalite.qc.olcumde",
            entity_type="QualityInspection",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def pass_et(*, actor, inspection: QualityInspection) -> QualityInspection:
    _require_manage(
        actor,
        action="kalite.qc.transition_denied",
        entity_id=str(inspection.pk),
    )
    with domain_atomic():
        locked = QualityInspection.objects.select_for_update().get(
            pk=inspection.pk
        )
        _set_durum(locked, QualityInspection.Durum.PASS)
        record_audit(
            actor=actor,
            action="kalite.qc.pass",
            entity_type="QualityInspection",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum, "shipment_blok": locked.shipment_blok},
        )
        return locked


def fail_et(
    *, actor, inspection: QualityInspection, reason: str = ""
) -> QualityInspection:
    _require_manage(
        actor,
        action="kalite.qc.transition_denied",
        entity_id=str(inspection.pk),
    )
    with domain_atomic():
        locked = QualityInspection.objects.select_for_update().get(
            pk=inspection.pk
        )
        _set_durum(locked, QualityInspection.Durum.FAIL)
        if reason:
            locked.notlar = (locked.notlar + " | " if locked.notlar else "") + reason[
                :200
            ]
            locked._allow_status_transition = True
            try:
                locked.save(update_fields=["notlar", "guncelleme_tarihi"])
            finally:
                locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="kalite.qc.fail",
            entity_type="QualityInspection",
            entity_id=str(locked.pk),
            success=True,
            detail={
                "durum": locked.durum,
                "shipment_blok": locked.shipment_blok,
                "reason": reason[:120],
            },
        )
        return locked


def iptal_et(*, actor, inspection: QualityInspection) -> QualityInspection:
    _require_manage(
        actor,
        action="kalite.qc.transition_denied",
        entity_id=str(inspection.pk),
    )
    with domain_atomic():
        locked = QualityInspection.objects.select_for_update().get(
            pk=inspection.pk
        )
        _set_durum(locked, QualityInspection.Durum.IPTAL)
        record_audit(
            actor=actor,
            action="kalite.qc.iptal",
            entity_type="QualityInspection",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def order_shipment_blocked(order: Order) -> bool:
    """F6-K6 / F6-010: FAIL veya açık QC veya hiç PASS yok → blok.

    Shipment create (F6-020) bu helper'ı kullanır.
    """
    qs = QualityInspection.objects.filter(order=order).exclude(
        durum=QualityInspection.Durum.IPTAL
    )
    if not qs.exists():
        return True
    if qs.filter(shipment_blok=True).exists():
        return True
    if qs.filter(
        durum__in=[
            QualityInspection.Durum.TASLAK,
            QualityInspection.Durum.OLCUMDE,
            QualityInspection.Durum.FAIL,
        ]
    ).exists():
        return True
    return not qs.filter(durum=QualityInspection.Durum.PASS).exists()
