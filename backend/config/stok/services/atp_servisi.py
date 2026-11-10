"""F11-012 — Kural tabanlı ATP görünümü (ML yok).

Formül (deterministik):
  ATP = available = on_hand − reserved − blocked
  (StockBalance projeksiyonu; F4-012)

Birim karışmaz: satırlar birim bazında ayrı kalır (ADET↔GRAM yok).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from stok.models import StockBalance, Warehouse


def _scope_balances(actor):
    qs = StockBalance.objects.select_related(
        "warehouse", "teklif", "varyant", "warehouse__sahip_firma"
    )
    if can_view_all_tenants(actor):
        return qs
    firma_id = getattr(actor, "firma_id", None)
    if not firma_id:
        return qs.none()
    # Tedarikçi: kendi depoları; alıcı: boş (kör — depo sahipliği sızdırılmaz)
    firma = getattr(actor, "firma", None)
    if firma is not None and getattr(firma, "tedarikci_mi", False):
        return qs.filter(warehouse__sahip_firma_id=firma_id)
    return qs.none()


def atp_satirlari(
    *,
    actor,
    varyant_id: int | None = None,
    teklif_id: int | None = None,
    warehouse_id: int | None = None,
) -> list[dict]:
    """ATP satırları. Alıcıya tedarikçi/depo kimliği yok (boş liste — kör havuz).

    Platform `view_all_tenants`: tüm bakiyeler.
    Tedarikçi: yalnız kendi warehouse.
    """
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Kimlik gerekli.")
    qs = _scope_balances(actor)
    if varyant_id is not None:
        qs = qs.filter(varyant_id=int(varyant_id))
    if teklif_id is not None:
        qs = qs.filter(teklif_id=int(teklif_id))
    if warehouse_id is not None:
        qs = qs.filter(warehouse_id=int(warehouse_id))
    rows: list[dict] = []
    for bal in qs.order_by("varyant_id", "birim", "pk"):
        atp = bal.available
        row = {
            "balance_id": bal.pk,
            "varyant_id": bal.varyant_id,
            "teklif_id": bal.teklif_id,
            "birim": bal.birim,
            "on_hand": str(bal.on_hand),
            "reserved": str(bal.reserved),
            "blocked": str(bal.blocked),
            "atp": str(atp),
            "formul": "on_hand - reserved - blocked",
        }
        if can_view_all_tenants(actor) or (
            getattr(getattr(actor, "firma", None), "tedarikci_mi", False)
        ):
            row["warehouse_id"] = bal.warehouse_id
            row["warehouse_kod"] = bal.warehouse.kod
        rows.append(row)
    return rows


def atp_toplam_varyant(*, actor, varyant_id: int, birim: str) -> Decimal:
    """Aynı varyant+birim ATP toplamı (birim karışmaz)."""
    birim = (birim or "").strip().upper()
    if birim not in {"ADET", "GRAM", "KARAT"}:
        raise ValidationError({"birim": "Geçersiz birim."})
    total = Decimal("0")
    for row in atp_satirlari(actor=actor, varyant_id=varyant_id):
        if row["birim"] != birim:
            continue
        total += Decimal(row["atp"])
    return total
