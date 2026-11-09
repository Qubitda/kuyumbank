"""F10-012 — Harcama limiti assert."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import HarcamaLimiti, OnayTalebi, OrgBirimi
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from siparis.models import Order


def kaydet_limit(
    *,
    actor,
    firma,
    tutar: Decimal,
    para_birimi: str = "TRY",
    donem: str = HarcamaLimiti.Donem.SIPARIS,
    org_birimi: OrgBirimi | None = None,
) -> HarcamaLimiti:
    try:
        require_perm(actor, P["manage_spend_limit"])
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="firmalar.limit.denied",
            entity_type="HarcamaLimiti",
            entity_id="",
            success=False,
            reason=str(exc),
        )
        raise

    with domain_atomic():
        row = HarcamaLimiti(
            firma=firma,
            org_birimi=org_birimi,
            donem=donem,
            tutar=tutar,
            para_birimi=para_birimi,
            aktif=True,
        )
        row.save()
        record_audit(
            actor=actor,
            action="firmalar.limit.created",
            entity_type="HarcamaLimiti",
            entity_id=str(row.pk),
            success=True,
            detail={"tutar": str(row.tutar), "donem": row.donem},
        )
        return row


def _order_tutar(order: Order) -> tuple[Decimal, str]:
    lines = list(order.lines.all())
    if not lines:
        return Decimal("0.00"), "TRY"
    pb = lines[0].para_birimi
    toplam = sum((ln.snapshot_satir_tutari_vergisiz for ln in lines), Decimal("0"))
    return toplam.quantize(Decimal("0.01")), pb


def assert_musait(*, firma, tutar: Decimal, para_birimi: str, org_birimi=None) -> None:
    """Aktif SIPARIS limiti varsa tutar ≤ limit; yoksa geç."""
    qs = HarcamaLimiti.objects.filter(
        firma=firma,
        aktif=True,
        para_birimi=(para_birimi or "TRY").upper(),
        donem=HarcamaLimiti.Donem.SIPARIS,
    )
    if org_birimi is not None:
        lim = qs.filter(org_birimi=org_birimi).order_by("-pk").first()
        if lim is None:
            lim = qs.filter(org_birimi__isnull=True).order_by("-pk").first()
    else:
        lim = qs.filter(org_birimi__isnull=True).order_by("-pk").first()
    if lim is None:
        return
    if tutar > lim.tutar:
        raise ValidationError(
            f"Harcama limiti aşıldı: {tutar} > {lim.tutar} {lim.para_birimi} (F10-012)."
        )


def assert_order_limit(order: Order) -> None:
    tutar, pb = _order_tutar(order)
    if tutar <= 0:
        return
    # Onaylanmış talep varsa limit bypass (F10-013)
    if OnayTalebi.objects.filter(
        order=order,
        durum=OnayTalebi.Durum.ONAYLANDI,
        para_birimi=(pb or "TRY").upper(),
        tutar__gte=tutar,
    ).exists():
        return
    # Fail audit order_servisi domain_atomic dışında; burada yalnız ValidationError
    assert_musait(
        firma=order.alici_firma,
        tutar=tutar,
        para_birimi=pb,
        org_birimi=order.sube,
    )
