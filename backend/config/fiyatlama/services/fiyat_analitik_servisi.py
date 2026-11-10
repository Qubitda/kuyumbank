"""F11-011 — Quote/Lock geçmiş özeti (platform finans; alıcıya maliyet yok)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Max, Min, Sum

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import record_audit_durable
from firmalar.services.yetki_servisi import can_view_all_tenants, require_perm
from fiyatlama.models import PriceLock, PriceQuote


def _require_platform_finance(actor):
    try:
        require_perm(actor, P["manage_sozlesme"], message="Fiyat analitiği yetkisi yok.")
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action="fiyatlama.analitik.denied",
            entity_type="FiyatAnalitik",
            entity_id="",
            success=False,
            reason="yetki_yok",
        )
        raise
    if not can_view_all_tenants(actor):
        record_audit_durable(
            actor=actor,
            action="fiyatlama.analitik.denied",
            entity_type="FiyatAnalitik",
            entity_id="",
            success=False,
            reason="view_all_yok",
        )
        raise PermissionDenied("Yalnız platform finans/ops.")
    firma = getattr(actor, "firma", None)
    if not (firma and getattr(firma, "platform_mu", False)):
        record_audit_durable(
            actor=actor,
            action="fiyatlama.analitik.denied",
            entity_type="FiyatAnalitik",
            entity_id="",
            success=False,
            reason="platform_degil",
        )
        raise PermissionDenied("Platform firma gerekli.")


def quote_ozet(*, actor, alici_firma_id: int | None = None) -> dict:
    """Tenant kesitli quote özeti — maliyet/tedarikçi alanları yok."""
    _require_platform_finance(actor)
    qs = PriceQuote.objects.all()
    if alici_firma_id is not None:
        qs = qs.filter(alici_firma_id=int(alici_firma_id))
    agg = qs.aggregate(
        adet=Count("pk"),
        toplam_sum=Sum("toplam_vergisiz"),
        toplam_avg=Avg("toplam_vergisiz"),
        toplam_min=Min("toplam_vergisiz"),
        toplam_max=Max("toplam_vergisiz"),
    )
    return {
        "scope": "PriceQuote",
        "alici_firma_id": alici_firma_id,
        "adet": int(agg["adet"] or 0),
        "toplam_sum": str(agg["toplam_sum"] or Decimal("0")),
        "toplam_avg": str(agg["toplam_avg"] or Decimal("0")),
        "toplam_min": str(agg["toplam_min"]) if agg["toplam_min"] is not None else None,
        "toplam_max": str(agg["toplam_max"]) if agg["toplam_max"] is not None else None,
        # Gizlilik: maliyet / tedarikçi yok
    }


def lock_ozet(*, actor, alici_firma_id: int | None = None) -> dict:
    _require_platform_finance(actor)
    qs = PriceLock.objects.select_related("quote")
    if alici_firma_id is not None:
        qs = qs.filter(alici_firma_id=int(alici_firma_id))
    agg = qs.aggregate(
        adet=Count("pk"),
        toplam_sum=Sum("toplam_vergisiz"),
        toplam_avg=Avg("toplam_vergisiz"),
    )
    return {
        "scope": "PriceLock",
        "alici_firma_id": alici_firma_id,
        "adet": int(agg["adet"] or 0),
        "toplam_sum": str(agg["toplam_sum"] or Decimal("0")),
        "toplam_avg": str(agg["toplam_avg"] or Decimal("0")),
    }
