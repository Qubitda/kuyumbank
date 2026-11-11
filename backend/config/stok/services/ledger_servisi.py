"""Stok ledger yazımı — Movement + Balance (ADR-0011 F4-A3/A4/A13)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import has_perm, is_platform_firm_user
from fiyatlama.models import TedarikciTeklif
from stok.models import StockBalance, StockMovement, Warehouse
from stok.services.birim import assert_ayni_birim, birim_from_teklif


def assert_teklif_warehouse(warehouse: Warehouse, teklif: TedarikciTeklif) -> None:
    if warehouse.sahip_tipi == Warehouse.SahipTipi.TEDARIKCI:
        if teklif.tedarikci_id != warehouse.sahip_firma_id:
            raise ValidationError(
                "Tedarikçi deposuna yalnız kendi teklifi yazılır (konsinye yok)."
            )


def _assert_can_adjust(actor, warehouse: Warehouse) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Stok düzeltme için kimlik gerekli.")
    if is_platform_firm_user(actor) and has_perm(actor, P["manage_warehouse"]):
        return
    if (
        has_perm(actor, P["manage_own_warehouse"])
        and warehouse.sahip_tipi == Warehouse.SahipTipi.TEDARIKCI
        and getattr(actor, "firma_id", None) == warehouse.sahip_firma_id
    ):
        return
    raise PermissionDenied("Stok düzeltme yetkisi yok.")


def _apply_on_hand_delta(balance: StockBalance, delta: Decimal) -> None:
    yeni = balance.on_hand + delta
    if yeni < 0:
        raise ValidationError(
            f"Yetersiz stok: on_hand={balance.on_hand}, delta={delta}."
        )
    if balance.available + delta < 0:
        raise ValidationError(
            f"Yetersiz available: available={balance.available}, delta={delta}."
        )
    balance.on_hand = yeni


def get_or_create_balance_locked(
    *,
    warehouse: Warehouse,
    teklif: TedarikciTeklif,
    birim: str,
) -> StockBalance:
    """Balance satır kilidi — reservation/ledger ortak (select_for_update).

    Eşzamanlı ilk oluşturmada UniqueConstraint yarışını IntegrityError →
    yeniden kilitleyerek çözer.
    """
    from django.db import IntegrityError

    bal = (
        StockBalance.objects.select_for_update()
        .filter(warehouse=warehouse, teklif=teklif, birim=birim)
        .first()
    )
    if bal is not None:
        return bal
    bal = StockBalance(
        warehouse=warehouse,
        teklif=teklif,
        varyant_id=teklif.varyant_id,
        birim=birim,
        on_hand=Decimal("0"),
        reserved=Decimal("0"),
        blocked=Decimal("0"),
    )
    try:
        bal.save()
    except IntegrityError:
        bal = (
            StockBalance.objects.select_for_update()
            .filter(warehouse=warehouse, teklif=teklif, birim=birim)
            .get()
        )
        return bal
    return StockBalance.objects.select_for_update().get(pk=bal.pk)


def save_balance_fields(balance: StockBalance, *, update_fields: list[str]) -> None:
    """Ledger/reservation servisleri için kontrollü balance kaydı."""
    fields = list(update_fields)
    if "guncelleme_tarihi" not in fields:
        fields.append("guncelleme_tarihi")
    balance._allow_ledger_update = True
    try:
        balance.save(update_fields=fields)
    finally:
        balance._allow_ledger_update = False


def kaydet_hareket(
    *,
    actor,
    warehouse: Warehouse,
    teklif: TedarikciTeklif,
    tip: str,
    miktar: Decimal,
    neden: str = "",
) -> StockMovement:
    """Immutable movement yazar ve balance on_hand günceller (GIRIS/CIKIS/DUZELTME)."""
    if tip not in {
        StockMovement.Tip.GIRIS,
        StockMovement.Tip.CIKIS,
        StockMovement.Tip.DUZELTME,
    }:
        raise ValidationError(f"Bu dilimde desteklenmeyen hareket tipi: {tip}")

    miktar = Decimal(miktar)
    if miktar == 0:
        raise ValidationError("Miktar sıfır olamaz.")

    if tip == StockMovement.Tip.GIRIS and miktar < 0:
        raise ValidationError("GIRIS miktarı pozitif olmalı.")
    if tip == StockMovement.Tip.CIKIS and miktar > 0:
        miktar = -abs(miktar)
    if tip == StockMovement.Tip.CIKIS and miktar >= 0:
        raise ValidationError("CIKIS miktarı negatif olmalı.")

    birim = birim_from_teklif(teklif)
    assert_teklif_warehouse(warehouse, teklif)

    with domain_atomic():
        bal = get_or_create_balance_locked(
            warehouse=warehouse, teklif=teklif, birim=birim
        )
        assert_ayni_birim(bal.birim, birim, context="balance")
        _apply_on_hand_delta(bal, miktar)
        save_balance_fields(bal, update_fields=["on_hand"])

        mv = StockMovement(
            warehouse=warehouse,
            teklif=teklif,
            varyant_id=teklif.varyant_id,
            birim=birim,
            miktar=miktar,
            tip=tip,
            neden=(neden or "").strip(),
            olusturan=actor,
        )
        mv.save()
        record_audit(
            actor=actor,
            action="stock_movement.create",
            entity_type="StockMovement",
            entity_id=str(mv.pk),
            success=True,
            detail={
                "tip": tip,
                "miktar": str(miktar),
                "birim": birim,
                "warehouse_id": warehouse.pk,
                "teklif_id": teklif.pk,
                "on_hand": str(bal.on_hand),
            },
        )
        return mv


def duzeltme(
    *,
    actor,
    warehouse: Warehouse,
    teklif: TedarikciTeklif,
    miktar: Decimal,
    neden: str,
) -> StockMovement:
    """F4-013 — signed DUZELTME; neden zorunlu."""
    neden_n = (neden or "").strip()
    if len(neden_n) < 5:
        raise ValidationError("Düzeltme nedeni en az 5 karakter olmalı.")

    try:
        _assert_can_adjust(actor, warehouse)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="stock_movement.create",
            entity_type="StockMovement",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"warehouse_id": warehouse.pk, "teklif_id": teklif.pk},
        )
        raise

    return kaydet_hareket(
        actor=actor,
        warehouse=warehouse,
        teklif=teklif,
        tip=StockMovement.Tip.DUZELTME,
        miktar=Decimal(miktar),
        neden=neden_n,
    )
