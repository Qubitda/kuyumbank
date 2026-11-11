"""F11-014 — Basit eşik anomali (ticari ciro); audit + ops uyarı listesi."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum
from django.db.models.functions import Coalesce

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import can_view_all_tenants, require_perm
from siparis.models import OrderLine
from siparis.services.rapor_servisi import resolve_date_range


def _require_platform_ops(actor):
    try:
        require_perm(
            actor, P["manage_sozlesme"], message="Anomali tarama yetkisi yok."
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action="siparis.anomali.denied",
            entity_type="AnomaliTarama",
            entity_id="",
            success=False,
            reason="yetki_yok",
        )
        raise
    if not can_view_all_tenants(actor):
        record_audit_durable(
            actor=actor,
            action="siparis.anomali.denied",
            entity_type="AnomaliTarama",
            entity_id="",
            success=False,
            reason="view_all_yok",
        )
        raise PermissionDenied("Yalnız platform finans/ops.")
    firma = getattr(actor, "firma", None)
    if not (firma and getattr(firma, "platform_mu", False)):
        record_audit_durable(
            actor=actor,
            action="siparis.anomali.denied",
            entity_type="AnomaliTarama",
            entity_id="",
            success=False,
            reason="platform_degil",
        )
        raise PermissionDenied("Platform firma gerekli.")


def ciro_esik_tara(
    *,
    actor,
    esik_ciro: Decimal,
    alici_firma_id: int | None = None,
    date_from=None,
    date_to=None,
) -> dict:
    """Alıcı ciro (OrderLine snapshot) ≥ eşik → uyarı; kör (tedarikçi yok)."""
    _require_platform_ops(actor)
    esik = Decimal(str(esik_ciro))
    if esik <= 0:
        raise ValidationError({"esik_ciro": "Pozitif olmalı."})

    d_from, d_to = resolve_date_range(date_from=date_from, date_to=date_to)
    qs = OrderLine.objects.filter(
        order__olusturma_tarihi__date__gte=d_from,
        order__olusturma_tarihi__date__lte=d_to,
    )
    if alici_firma_id is not None:
        qs = qs.filter(order__alici_firma_id=int(alici_firma_id))

    rows = (
        qs.values("order__alici_firma_id")
        .annotate(
            ciro=Coalesce(Sum("snapshot_satir_tutari_vergisiz"), Decimal("0"))
        )
        .order_by("order__alici_firma_id")
    )

    uyarilar: list[dict] = []
    for row in rows:
        ciro = Decimal(str(row["ciro"] or 0))
        if ciro < esik:
            continue
        uyarilar.append(
            {
                "alici_firma_id": int(row["order__alici_firma_id"]),
                "ciro_vergisiz": str(ciro),
                "esik_ciro": str(esik),
                "anomali": True,
            }
        )

    with domain_atomic():
        record_audit(
            actor=actor,
            action="siparis.anomali.ciro_esik",
            entity_type="AnomaliTarama",
            entity_id="",
            success=True,
            detail={
                "esik_ciro": str(esik),
                "uyari_adet": len(uyarilar),
                "alici_firma_id": alici_firma_id,
                "date_from": d_from.isoformat(),
                "date_to": d_to.isoformat(),
            },
        )

    return {
        "scope": "ciro_esik",
        "esik_ciro": str(esik),
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "uyari_adet": len(uyarilar),
        "uyarilar": uyarilar,
        "read_model": "live_orm",
    }
