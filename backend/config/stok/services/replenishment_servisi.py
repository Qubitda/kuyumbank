"""F11-020 — Kural tabanlı stok yenileme önerisi (otomatik checkout yok)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm
from stok.services.atp_servisi import atp_satirlari


def _require(actor, *, action: str):
    ok = has_perm(actor, P["manage_warehouse"]) or has_perm(
        actor, P["manage_own_warehouse"]
    )
    if not ok:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="Replenishment",
            entity_id="",
            success=False,
            reason="yetki_yok",
        )
        raise PermissionDenied("Replenishment yetkisi yok.")


def oneri_uret(
    *,
    actor,
    esik_atp: Decimal,
    hedef_atp: Decimal | None = None,
    birim: str | None = None,
) -> list[dict]:
    """ATP < eşik → önerilen miktar = max(0, hedef − ATP). Checkout yok."""
    _require(actor, action="stok.replenishment.denied")
    esik = Decimal(str(esik_atp))
    if esik < 0:
        raise ValidationError({"esik_atp": "Negatif olamaz."})
    hedef = Decimal(str(hedef_atp if hedef_atp is not None else esik))
    if hedef < esik:
        raise ValidationError({"hedef_atp": "Hedef eşikten küçük olamaz."})
    birim_f = (birim or "").strip().upper() or None
    if birim_f and birim_f not in {"ADET", "GRAM", "KARAT"}:
        raise ValidationError({"birim": "Geçersiz."})

    oneriler: list[dict] = []
    for row in atp_satirlari(actor=actor):
        if birim_f and row["birim"] != birim_f:
            continue
        atp = Decimal(row["atp"])
        if atp >= esik:
            continue
        miktar = hedef - atp
        if miktar <= 0:
            continue
        oneriler.append(
            {
                "varyant_id": row["varyant_id"],
                "teklif_id": row["teklif_id"],
                "warehouse_id": row.get("warehouse_id"),
                "birim": row["birim"],
                "atp": str(atp),
                "esik_atp": str(esik),
                "onerilen_miktar": str(miktar),
                "otomatik_checkout": False,
            }
        )

    with domain_atomic():
        record_audit(
            actor=actor,
            action="stok.replenishment.oneri",
            entity_type="Replenishment",
            entity_id="",
            success=True,
            detail={"adet": len(oneriler), "esik": str(esik)},
        )
    return oneriler
