"""B5 — ops QC / sevkiyat sunum (maske + allowed_actions)."""

from __future__ import annotations

from django.utils import timezone

from api.masking import assert_masked
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm
from kalite.models import QualityInspection, QualityMeasurement
from lojistik.models import Shipment
from lojistik.services.buyer_shipment_servisi import present_shipment as _raw_ship


def present_inspection(insp: QualityInspection, *, can_manage: bool = False) -> dict:
    measurements = [
        {
            "id": m.pk,
            "order_line_id": m.order_line_id,
            "birim": m.birim,
            "beklenen": str(m.beklenen),
            "olculen": str(m.olculen),
            "sapma_abs": str(m.sapma_abs),
            "sonuc": m.sonuc,
            "override_uygulandi": m.override_uygulandi,
            "olusturma_tarihi": m.olusturma_tarihi.isoformat()
            if m.olusturma_tarihi
            else None,
        }
        for m in insp.measurements.all().order_by("pk")
    ]
    actions: list[str] = []
    if can_manage:
        if insp.durum == QualityInspection.Durum.TASLAK:
            actions.extend(["start", "cancel"])
        elif insp.durum == QualityInspection.Durum.OLCUMDE:
            actions.extend(["add_measurement", "pass", "fail", "cancel"])
    data = {
        "id": insp.pk,
        "order_id": insp.order_id,
        "order_line_id": insp.order_line_id,
        "durum": insp.durum,
        "shipment_blok": insp.shipment_blok,
        "notlar": insp.notlar or "",
        "measurements": measurements,
        "allowed_actions": actions,
        "olusturma_tarihi": insp.olusturma_tarihi.isoformat()
        if insp.olusturma_tarihi
        else None,
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_measurement(m: QualityMeasurement) -> dict:
    data = {
        "id": m.pk,
        "inspection_id": m.inspection_id,
        "order_line_id": m.order_line_id,
        "birim": m.birim,
        "beklenen": str(m.beklenen),
        "olculen": str(m.olculen),
        "sapma_abs": str(m.sapma_abs),
        "sonuc": m.sonuc,
        "override_uygulandi": m.override_uygulandi,
        "allowed_actions": ["view"],
        "server_now": timezone.now().isoformat(),
    }
    assert_masked(data)
    return data


def present_ops_shipment(ship: Shipment, *, can_manage: bool = False) -> dict:
    data = _raw_ship(ship)
    actions: list[str] = []
    if can_manage:
        if ship.durum == Shipment.Durum.TASLAK:
            actions.extend(["prepare", "cancel"])
        elif ship.durum == Shipment.Durum.HAZIR:
            actions.extend(["dispatch", "cancel"])
        elif ship.durum == Shipment.Durum.YOLDA:
            actions.extend(["deliver", "add_pod", "cancel"])
            if data.get("pod"):
                actions = [a for a in actions if a != "add_pod"]
    data["allowed_actions"] = actions
    data["server_now"] = timezone.now().isoformat()
    assert_masked(data)
    return data


def can_manage_qc(user) -> bool:
    return has_perm(user, P["manage_qc"])


def can_manage_shipment(user) -> bool:
    return has_perm(user, P["manage_shipment"])
