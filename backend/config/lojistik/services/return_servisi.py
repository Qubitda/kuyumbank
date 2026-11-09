"""F6-030/031 — Return/Dispute SM + stok IADE (U-004 stok-only; ödeme iadesi yok)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from lojistik.models import ReturnLine, ReturnRequest, Shipment
from siparis.models import Order, OrderLine
from stok.models import StockMovement, StockReservation
from stok.services.ledger_servisi import (
    get_or_create_balance_locked,
    save_balance_fields,
)

_TRANSITIONS = {
    ReturnRequest.Durum.TASLAK: {
        ReturnRequest.Durum.INCELENIYOR,
        ReturnRequest.Durum.IPTAL,
    },
    ReturnRequest.Durum.INCELENIYOR: {
        ReturnRequest.Durum.ONAYLANDI,
        ReturnRequest.Durum.REDDEDILDI,
        ReturnRequest.Durum.IPTAL,
    },
    ReturnRequest.Durum.ONAYLANDI: set(),
    ReturnRequest.Durum.REDDEDILDI: set(),
    ReturnRequest.Durum.IPTAL: set(),
}


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_return"],
            message="İade yönetimi için manage_return gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="ReturnRequest",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def _set_durum(req: ReturnRequest, yeni: str, *, extra_fields=None) -> ReturnRequest:
    allowed = _TRANSITIONS.get(req.durum, set())
    if yeni not in allowed:
        raise ValidationError(f"Geçersiz iade geçişi: {req.durum} → {yeni}.")
    req.durum = yeni
    fields = ["durum", "guncelleme_tarihi"]
    if extra_fields:
        fields = list(dict.fromkeys(fields + extra_fields))
    req._allow_status_transition = True
    try:
        req.save(update_fields=fields)
    finally:
        req._allow_status_transition = False
    return req


def _validate_line_specs(order: Order, line_specs: list[dict]) -> list[tuple[OrderLine, Decimal]]:
    if not line_specs:
        raise ValidationError("İade için en az bir satır gerekir.")
    resolved: list[tuple[OrderLine, Decimal]] = []
    seen: set[int] = set()
    for spec in line_specs:
        ol = spec.get("order_line")
        miktar = spec.get("miktar")
        if ol is None or miktar is None:
            raise ValidationError("order_line ve miktar zorunlu.")
        if not isinstance(miktar, Decimal):
            miktar = Decimal(str(miktar))
        if miktar <= 0:
            raise ValidationError("İade miktarı pozitif olmalı.")
        if ol.order_id != order.pk:
            raise ValidationError("order_line bu siparişe ait değil.")
        if ol.pk in seen:
            raise ValidationError("Aynı order_line birden fazla verilemez.")
        seen.add(ol.pk)
        if miktar > ol.miktar:
            raise ValidationError("İade miktarı sipariş satırını aşamaz.")
        resolved.append((ol, miktar))
    return resolved


def olustur(
    *,
    actor,
    order: Order,
    shipment: Shipment,
    sebep: str,
    line_specs: list[dict],
    notlar: str = "",
) -> ReturnRequest:
    """TASLAK iade talebi. Finans hareketi yok (F6-030)."""
    _require_manage(actor, action="lojistik.return.create_denied")
    sebep_n = (sebep or "").strip()
    if len(sebep_n) < 5:
        raise ValidationError("İade sebebi en az 5 karakter olmalı.")
    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError("İade yalnız OLUSTURULDU siparişe açılır.")
    if shipment.order_id != order.pk:
        raise ValidationError("Sevkiyat bu siparişe ait değil.")
    if shipment.durum != Shipment.Durum.TESLIM:
        raise ValidationError("İade yalnız TESLIM sevkiyat için açılır.")
    resolved = _validate_line_specs(order, line_specs)

    with domain_atomic():
        req = ReturnRequest(
            order=order,
            shipment=shipment,
            durum=ReturnRequest.Durum.TASLAK,
            sebep=sebep_n[:255],
            notlar=notlar or "",
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        req.save()
        for ol, miktar in resolved:
            ReturnLine(
                return_request=req,
                order_line=ol,
                miktar=miktar,
                birim=ol.birim,
            ).save()
        record_audit(
            actor=actor,
            action="lojistik.return.created",
            entity_type="ReturnRequest",
            entity_id=str(req.pk),
            success=True,
            detail={
                "order_id": order.pk,
                "shipment_id": shipment.pk,
                "line_count": len(resolved),
            },
        )
        return req


def incelemeye_al(*, actor, return_request: ReturnRequest) -> ReturnRequest:
    _require_manage(
        actor,
        action="lojistik.return.transition_denied",
        entity_id=str(return_request.pk),
    )
    with domain_atomic():
        locked = ReturnRequest.objects.select_for_update().get(pk=return_request.pk)
        _set_durum(locked, ReturnRequest.Durum.INCELENIYOR)
        record_audit(
            actor=actor,
            action="lojistik.return.inceleniyor",
            entity_type="ReturnRequest",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def _stok_iade_yaz(*, actor, req: ReturnRequest) -> list[int]:
    """F6-031: onayda satır başına IADE movement + on_hand artışı."""
    if req.stok_iade_yapildi:
        return []
    iade_ids: list[int] = []
    for rl in req.lines.select_related(
        "order_line__stock_reservation__warehouse",
        "order_line__stock_reservation__teklif",
    ):
        line = rl.order_line
        res = line.stock_reservation
        if res.durum != StockReservation.Durum.TUKETILDI:
            raise ValidationError(
                "İade için satır rezervasyonu tüketilmiş olmalı."
            )
        bal = get_or_create_balance_locked(
            warehouse=res.warehouse,
            teklif=res.teklif,
            birim=res.birim,
        )
        bal.on_hand = bal.on_hand + rl.miktar
        save_balance_fields(bal, update_fields=["on_hand"])
        mv = StockMovement(
            warehouse=res.warehouse,
            teklif=res.teklif,
            varyant_id=line.varyant_id,
            birim=line.birim,
            miktar=rl.miktar,
            tip=StockMovement.Tip.IADE,
            neden=f"return:{req.pk}:line:{line.pk}",
            olusturan=actor,
        )
        mv.save()
        iade_ids.append(mv.pk)
    req.stok_iade_yapildi = True
    return iade_ids


def onayla(
    *,
    actor,
    return_request: ReturnRequest,
    mahsup: bool = False,
) -> ReturnRequest:
    """ONAYLANDI + F6-031 stok IADE. mahsup=True → F5-023 (ödeme iadesi yok)."""
    _require_manage(
        actor,
        action="lojistik.return.transition_denied",
        entity_id=str(return_request.pk),
    )
    try:
        with domain_atomic():
            locked = (
                ReturnRequest.objects.select_for_update()
                .prefetch_related("lines")
                .get(pk=return_request.pk)
            )
            if locked.durum == ReturnRequest.Durum.ONAYLANDI:
                return locked
            _set_durum(locked, ReturnRequest.Durum.ONAYLANDI)
            iade_ids = _stok_iade_yaz(actor=actor, req=locked)
            locked._allow_status_transition = True
            try:
                locked.save(
                    update_fields=["stok_iade_yapildi", "guncelleme_tarihi"]
                )
            finally:
                locked._allow_status_transition = False

            mahsup_entry_id = None
            if mahsup:
                from finans.services import mahsup_servisi

                entry = mahsup_servisi.iade_mahsup(
                    actor=actor, return_request=locked
                )
                mahsup_entry_id = entry.pk if entry is not None else None
                locked.refresh_from_db(
                    fields=["finans_mahsup_yapildi", "guncelleme_tarihi"]
                )

            record_audit(
                actor=actor,
                action="lojistik.return.onaylandi",
                entity_type="ReturnRequest",
                entity_id=str(locked.pk),
                success=True,
                detail={
                    "durum": locked.durum,
                    "iade_movement_ids": iade_ids,
                    "stok_iade_yapildi": locked.stok_iade_yapildi,
                    "mahsup": mahsup,
                    "mahsup_entry_id": mahsup_entry_id,
                },
            )
            return locked
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="lojistik.return.transition_denied",
            entity_type="ReturnRequest",
            entity_id=str(return_request.pk),
            success=False,
            reason=reason[:255],
        )
        raise


def reddet(*, actor, return_request: ReturnRequest, reason: str = "") -> ReturnRequest:
    _require_manage(
        actor,
        action="lojistik.return.transition_denied",
        entity_id=str(return_request.pk),
    )
    with domain_atomic():
        locked = ReturnRequest.objects.select_for_update().get(pk=return_request.pk)
        _set_durum(locked, ReturnRequest.Durum.REDDEDILDI)
        if reason:
            locked.notlar = (locked.notlar + " | " if locked.notlar else "") + reason[
                :200
            ]
            locked._allow_status_transition = True
            try:
                locked.save(update_fields=["notlar", "guncelleme_tarihi"])
            finally:
                locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="lojistik.return.reddedildi",
            entity_type="ReturnRequest",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum, "reason": reason[:120]},
        )
        return locked


def iptal_et(*, actor, return_request: ReturnRequest) -> ReturnRequest:
    _require_manage(
        actor,
        action="lojistik.return.transition_denied",
        entity_id=str(return_request.pk),
    )
    with domain_atomic():
        locked = ReturnRequest.objects.select_for_update().get(pk=return_request.pk)
        _set_durum(locked, ReturnRequest.Durum.IPTAL)
        record_audit(
            actor=actor,
            action="lojistik.return.iptal",
            entity_type="ReturnRequest",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked
