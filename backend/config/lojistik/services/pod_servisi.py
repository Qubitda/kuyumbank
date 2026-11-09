"""F6-022 — POD kaydı; teslim politikası settings.SHIPMENT_POD_REQUIRED."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from lojistik.models import ProofOfDelivery, Shipment


def pod_required() -> bool:
    return bool(getattr(settings, "SHIPMENT_POD_REQUIRED", False))


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_shipment"],
            message="POD için manage_shipment gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="ProofOfDelivery",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def kaydet_pod(
    *,
    actor,
    shipment: Shipment,
    teslim_alan: str,
    notlar: str = "",
    belgeler_ref: str = "",
) -> ProofOfDelivery:
    _require_manage(
        actor,
        action="lojistik.pod.create_denied",
        entity_id=str(shipment.pk),
    )
    teslim_alan = (teslim_alan or "").strip()
    if len(teslim_alan) < 2:
        raise ValidationError({"teslim_alan": "Teslim alan en az 2 karakter."})
    if shipment.durum not in (
        Shipment.Durum.YOLDA,
        Shipment.Durum.TESLIM,
    ):
        raise ValidationError(
            f"POD yalnız YOLDA/TESLIM iken; şu an {shipment.durum}."
        )
    if ProofOfDelivery.objects.filter(shipment=shipment).exists():
        raise ValidationError("Bu sevkiyatta POD zaten var.")

    with domain_atomic():
        locked = Shipment.objects.select_for_update().get(pk=shipment.pk)
        if ProofOfDelivery.objects.filter(shipment=locked).exists():
            raise ValidationError("Bu sevkiyatta POD zaten var.")
        pod = ProofOfDelivery(
            shipment=locked,
            teslim_alan=teslim_alan[:120],
            notlar=(notlar or "")[:255],
            belgeler_ref=(belgeler_ref or "")[:255],
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        pod.save()
        record_audit(
            actor=actor,
            action="lojistik.pod.created",
            entity_type="ProofOfDelivery",
            entity_id=str(pod.pk),
            success=True,
            detail={"shipment_id": locked.pk, "teslim_alan": pod.teslim_alan},
        )
        return pod
