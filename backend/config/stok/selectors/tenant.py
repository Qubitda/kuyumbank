"""Warehouse tenant scope (ADR-0011 F4-A2)."""

from firmalar.services.yetki_servisi import can_view_all_tenants


def scope_warehouse_queryset(qs, user):
    """Platform: tümü; tedarikçi: kendi firması; alıcı: hiçbiri."""
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "tedarikci_mi", False):
        return qs.filter(sahip_firma_id=firma_id)
    return qs.none()
