"""Warehouse oluşturma / güncelleme (ADR-0011 F4-A2)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import Firma
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import has_perm, is_platform_firm_user
from stok.models import Warehouse


def _resolve_sahip_tipi(firma: Firma) -> str:
    if firma.platform_mu:
        return Warehouse.SahipTipi.PLATFORM
    if firma.tedarikci_mi:
        return Warehouse.SahipTipi.TEDARIKCI
    raise ValidationError(
        {
            "sahip_firma": (
                "Depo yalnız platform veya tedarikçi firmaya bağlanır "
                "(konsinye yok)."
            )
        }
    )


def _assert_can_manage(actor, sahip_firma: Firma) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Depo için kimlik doğrulama gerekli.")

    if is_platform_firm_user(actor) and has_perm(actor, P["manage_warehouse"]):
        return

    if (
        has_perm(actor, P["manage_own_warehouse"])
        and getattr(actor, "firma_id", None) == sahip_firma.pk
        and sahip_firma.tedarikci_mi
    ):
        return

    raise PermissionDenied("Bu depo için yönetim yetkisi yok.")


def olustur_warehouse(
    *,
    actor,
    sahip_firma: Firma,
    kod: str,
    ad: str,
    aktif: bool = True,
) -> Warehouse:
    kod_n = (kod or "").strip()
    ad_n = (ad or "").strip()
    if not kod_n or not ad_n:
        raise ValidationError("Depo kodu ve adı zorunlu.")

    try:
        _assert_can_manage(actor, sahip_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="warehouse.create",
            entity_type="Warehouse",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"sahip_firma_id": getattr(sahip_firma, "pk", None)},
        )
        raise

    sahip_tipi = _resolve_sahip_tipi(sahip_firma)

    with domain_atomic():
        wh = Warehouse(
            kod=kod_n,
            ad=ad_n,
            sahip_firma=sahip_firma,
            sahip_tipi=sahip_tipi,
            aktif=aktif,
        )
        wh.save()
        record_audit(
            actor=actor,
            action="warehouse.create",
            entity_type="Warehouse",
            entity_id=str(wh.pk),
            success=True,
            detail={
                "kod": wh.kod,
                "sahip_firma_id": wh.sahip_firma_id,
                "sahip_tipi": wh.sahip_tipi,
            },
        )
        return wh
