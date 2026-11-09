"""F6-020 — Shipment SM + QC gate (ADR-0013 F6-K6 / F6-K8)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from kalite.services.inspection_servisi import order_shipment_blocked
from lojistik.models import Shipment
from siparis.models import Order

_TRANSITIONS = {
    Shipment.Durum.TASLAK: {
        Shipment.Durum.HAZIR,
        Shipment.Durum.IPTAL,
    },
    Shipment.Durum.HAZIR: {
        Shipment.Durum.YOLDA,
        Shipment.Durum.IPTAL,
    },
    Shipment.Durum.YOLDA: {
        Shipment.Durum.TESLIM,
        Shipment.Durum.IPTAL,
    },
    Shipment.Durum.TESLIM: set(),
    Shipment.Durum.IPTAL: set(),
}


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_shipment"],
            message="Sevkiyat için manage_shipment gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="Shipment",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def _set_durum(ship: Shipment, yeni: str) -> Shipment:
    allowed = _TRANSITIONS.get(ship.durum, set())
    if yeni not in allowed:
        raise ValidationError(
            f"Geçersiz sevkiyat geçişi: {ship.durum} → {yeni}."
        )
    ship.durum = yeni
    ship._allow_status_transition = True
    try:
        ship.save(update_fields=["durum", "guncelleme_tarihi"])
    finally:
        ship._allow_status_transition = False
    return ship


def olustur(
    *,
    actor,
    order: Order,
    notlar: str = "",
    takip_no: str = "",
) -> Shipment:
    """F6-K6: QC PASS yoksa / FAIL / açık QC → ValidationError."""
    _require_manage(actor, action="lojistik.shipment.create_denied")
    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError("Sevkiyat yalnız OLUSTURULDU siparişe açılır.")
    if order_shipment_blocked(order):
        record_audit_durable(
            actor=actor,
            action="lojistik.shipment.create_denied",
            entity_type="Shipment",
            entity_id="",
            success=False,
            reason="qc_gate",
            detail={"order_id": order.pk},
        )
        raise ValidationError(
            "Sevkiyat açılamaz: siparişte QC PASS yok veya shipment_blok "
            "(F6-K6)."
        )

    with domain_atomic():
        # Gate yeniden kontrol (yarış)
        if order_shipment_blocked(order):
            raise ValidationError(
                "Sevkiyat açılamaz: QC gate (eşzamanlı kontrol)."
            )
        ship = Shipment(
            order=order,
            durum=Shipment.Durum.TASLAK,
            notlar=notlar or "",
            takip_no=takip_no or "",
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        ship.save()
        record_audit(
            actor=actor,
            action="lojistik.shipment.created",
            entity_type="Shipment",
            entity_id=str(ship.pk),
            success=True,
            detail={"order_id": order.pk, "durum": ship.durum},
        )
        return ship


def hazirla(*, actor, shipment: Shipment) -> Shipment:
    _require_manage(
        actor,
        action="lojistik.shipment.transition_denied",
        entity_id=str(shipment.pk),
    )
    with domain_atomic():
        locked = Shipment.objects.select_for_update().get(pk=shipment.pk)
        _set_durum(locked, Shipment.Durum.HAZIR)
        record_audit(
            actor=actor,
            action="lojistik.shipment.hazir",
            entity_type="Shipment",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def sevk_et(
    *, actor, shipment: Shipment, takip_no: str = ""
) -> Shipment:
    """HAZIR → YOLDA. takip_no boşsa F6-021 carrier fake label üretir."""
    _require_manage(
        actor,
        action="lojistik.shipment.transition_denied",
        entity_id=str(shipment.pk),
    )
    from lojistik.carriers import LabelRequest, get_carrier_adapter

    # Carrier çağrısı domain_atomic DIŞINDA (fail audit durable + I/O)
    resolved = (takip_no or shipment.takip_no or "").strip()
    if not resolved:
        if shipment.durum != Shipment.Durum.HAZIR:
            raise ValidationError(
                f"Sevk yalnız HAZIR iken; şu an {shipment.durum}."
            )
        adapter = get_carrier_adapter()
        label = adapter.create_label(
            LabelRequest(
                shipment_id=shipment.pk,
                order_id=shipment.order_id,
                idempotency_key=f"ship-{shipment.pk}",
            )
        )
        if not label.ok:
            record_audit_durable(
                actor=actor,
                action="lojistik.shipment.sevk_denied",
                entity_type="Shipment",
                entity_id=str(shipment.pk),
                success=False,
                reason="carrier_fail",
                detail={"message": label.message},
            )
            raise ValidationError(
                f"Kargo etiketi alınamadı: {label.message} (F6-021)."
            )
        resolved = label.tracking_no

    with domain_atomic():
        locked = Shipment.objects.select_for_update().get(pk=shipment.pk)
        if locked.durum != Shipment.Durum.HAZIR:
            raise ValidationError(
                f"Sevk yalnız HAZIR iken; şu an {locked.durum}."
            )
        locked.takip_no = resolved[:64]
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["takip_no", "guncelleme_tarihi"])
        finally:
            locked._allow_status_transition = False
        _set_durum(locked, Shipment.Durum.YOLDA)
        record_audit(
            actor=actor,
            action="lojistik.shipment.yolda",
            entity_type="Shipment",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum, "takip_no": locked.takip_no},
        )
        return locked


def teslim_et(*, actor, shipment: Shipment) -> Shipment:
    """YOLDA → TESLIM. SHIPMENT_POD_REQUIRED=True ise POD zorunlu (F6-022)."""
    _require_manage(
        actor,
        action="lojistik.shipment.transition_denied",
        entity_id=str(shipment.pk),
    )
    from lojistik.models import ProofOfDelivery
    from lojistik.services.pod_servisi import pod_required

    with domain_atomic():
        locked = Shipment.objects.select_for_update().get(pk=shipment.pk)
        if pod_required() and not ProofOfDelivery.objects.filter(
            shipment=locked
        ).exists():
            raise ValidationError(
                "POD zorunlu (SHIPMENT_POD_REQUIRED); teslimat kanıtı yok (F6-022)."
            )
        _set_durum(locked, Shipment.Durum.TESLIM)
        record_audit(
            actor=actor,
            action="lojistik.shipment.teslim",
            entity_type="Shipment",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def iptal_et(*, actor, shipment: Shipment) -> Shipment:
    _require_manage(
        actor,
        action="lojistik.shipment.transition_denied",
        entity_id=str(shipment.pk),
    )
    with domain_atomic():
        locked = Shipment.objects.select_for_update().get(pk=shipment.pk)
        _set_durum(locked, Shipment.Durum.IPTAL)
        record_audit(
            actor=actor,
            action="lojistik.shipment.iptal",
            entity_type="Shipment",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked
