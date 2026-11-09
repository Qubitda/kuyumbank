"""F5-023 — İade mahsup (ledger MAHSUP); ödeme iadesi yok (U-004)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.platform_kurulum import ensure_platform_firma
from finans.models import LedgerEntry
from finans.services.finans_audit import (
    record_finans_audit,
    record_finans_audit_durable,
)
from finans.services.ledger_servisi import kaydet_hareket
from lojistik.models import ReturnRequest


def odeme_iadesi_yap(*, actor, return_request: ReturnRequest):
    """U-004: v1 ödeme iadesi yok — her zaman reddedilir."""
    record_finans_audit_durable(
        actor=actor,
        action="finans.refund.denied",
        amount=Decimal("0.00"),
        currency="TRY",
        order_ref=str(return_request.order_id),
        entity_type="ReturnRequest",
        entity_id=str(return_request.pk),
        success=False,
        reason="odeme_iadesi_yok_u004",
    )
    raise ValidationError(
        "Ödeme iadesi yok (U-004 / F5-023); yalnız stok IADE + isteğe bağlı mahsup."
    )


def _return_tutar(return_request: ReturnRequest) -> tuple[Decimal, str]:
    lines = list(
        return_request.lines.select_related("order_line")
    )
    if not lines:
        raise ValidationError("İade satırı yok.")
    pb = lines[0].order_line.para_birimi
    toplam = Decimal("0.00")
    for rl in lines:
        ol = rl.order_line
        if ol.para_birimi != pb:
            raise ValidationError("İade satırlarında para birimi karışık.")
        # Oransal satır tutarı (kısmi iade)
        oran = rl.miktar / ol.miktar
        toplam += (ol.snapshot_satir_tutari_vergisiz * oran).quantize(
            Decimal("0.01")
        )
    if toplam <= 0:
        raise ValidationError("Mahsup tutarı sıfır.")
    return toplam, pb


def iade_mahsup(*, actor, return_request: ReturnRequest) -> LedgerEntry | None:
    """Alıcı carisine ALACAK mahsup (platform↔alıcı). Ödeme provider yok.

    Idempotent: finans_mahsup_yapildi True ise mevcut satırı döner / no-op.
    """
    if return_request.durum != ReturnRequest.Durum.ONAYLANDI:
        raise ValidationError("Mahsup yalnız ONAYLANDI iade için.")
    if return_request.finans_mahsup_yapildi:
        existing = LedgerEntry.objects.filter(
            referans_tip="ReturnRequest",
            referans_id=str(return_request.pk),
            hareket_tipi=LedgerEntry.HareketTipi.MAHSUP,
        ).first()
        return existing

    try:
        tutar, pb = _return_tutar(return_request)
    except ValidationError as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.mahsup.denied",
            amount=Decimal("0.00"),
            currency="TRY",
            order_ref=str(return_request.order_id),
            entity_type="ReturnRequest",
            entity_id=str(return_request.pk),
            success=False,
            reason=str(exc)[:200],
        )
        raise

    platform = ensure_platform_firma()
    alici = return_request.order.alici_firma
    key = f"mahsup:return:{return_request.pk}"

    try:
        entry = kaydet_hareket(
            actor=actor,
            firma=alici,
            karsi_firma=platform,
            tutar=tutar,
            para_birimi=pb,
            yon=LedgerEntry.Yon.ALACAK,
            hareket_tipi=LedgerEntry.HareketTipi.MAHSUP,
            idempotency_key=key,
            referans_tip="ReturnRequest",
            referans_id=str(return_request.pk),
            aciklama=f"İade mahsup RR#{return_request.pk} (ödeme iadesi yok)",
        )
    except PermissionDenied as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.mahsup.denied",
            amount=tutar,
            currency=pb,
            order_ref=str(return_request.order_id),
            entity_type="ReturnRequest",
            entity_id=str(return_request.pk),
            success=False,
            reason=str(exc),
        )
        raise

    return_request.finans_mahsup_yapildi = True
    return_request._allow_status_transition = True
    try:
        return_request.save(
            update_fields=["finans_mahsup_yapildi", "guncelleme_tarihi"]
        )
    finally:
        return_request._allow_status_transition = False

    record_finans_audit(
        actor=actor,
        action="finans.mahsup.posted",
        amount=tutar,
        currency=pb,
        order_ref=str(return_request.order_id),
        entity_type="LedgerEntry",
        entity_id=str(entry.pk),
        success=True,
        extra={"return_request_id": return_request.pk},
    )
    return entry
