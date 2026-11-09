"""RFQ tenant scope — alıcı kendi; view_all ops; tedarikçi GONDERILDI havuz; başkası DoesNotExist."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import RFQ


class RFQNotFound(ObjectDoesNotExist):
    """404 semantiği — varlık / çapraz tenant sızdırılmaz."""


def scope_rfq_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(alici_firma_id=firma_id)
    return qs.none()


def scope_supplier_rfq_queryset(qs, user):
    """B6 ters kör havuz: açık (GONDERILDI) RFQ; alıcı kimliği presenter'da yok."""
    if can_view_all_tenants(user):
        return qs.filter(durum=RFQ.Durum.GONDERILDI)
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "tedarikci_mi", False):
        return qs.filter(durum=RFQ.Durum.GONDERILDI)
    return qs.none()


def get_rfq_for_actor(user, rfq_id: int) -> RFQ:
    if user is None or not getattr(user, "is_authenticated", False):
        raise RFQNotFound("RFQ bulunamadı.")
    qs = scope_rfq_queryset(
        RFQ.objects.select_related("alici_firma", "sube").prefetch_related(
            "lines", "messages", "revizyonlar"
        ),
        user,
    )
    try:
        return qs.get(pk=rfq_id)
    except RFQ.DoesNotExist as exc:
        raise RFQNotFound("RFQ bulunamadı.") from exc


def get_supplier_rfq_for_actor(user, rfq_id: int) -> RFQ:
    if user is None or not getattr(user, "is_authenticated", False):
        raise RFQNotFound("RFQ bulunamadı.")
    qs = scope_supplier_rfq_queryset(
        RFQ.objects.select_related("alici_firma", "sube").prefetch_related(
            "lines", "messages", "revizyonlar"
        ),
        user,
    )
    try:
        return qs.get(pk=rfq_id)
    except RFQ.DoesNotExist as exc:
        raise RFQNotFound("RFQ bulunamadı.") from exc
