"""PaymentIntent — Order tahsilatı (F5-012)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.audit_servisi import domain_atomic
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from finans.models import LedgerEntry, PaymentIntent
from finans.services.finans_audit import (
    record_finans_audit,
    record_finans_audit_durable,
)
from finans.services.ledger_servisi import POST_LEDGER, kaydet_hareket
from siparis.models import Order


def _order_tutar_para(order: Order) -> tuple[Decimal, str]:
    lines = list(order.lines.all())
    if not lines:
        raise ValidationError("Siparişte satır yok.")
    pb = lines[0].para_birimi
    if any(ln.para_birimi != pb for ln in lines):
        raise ValidationError("Sipariş satırlarında para birimi karışık.")
    toplam = sum((ln.snapshot_satir_tutari_vergisiz for ln in lines), Decimal("0"))
    if toplam <= 0:
        raise ValidationError("Sipariş tutarı sıfır.")
    return toplam.quantize(Decimal("0.01")), pb


def _assert_can_pay(actor, order: Order) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Ödeme için kimlik gerekli.")
    if has_perm(actor, POST_LEDGER) or can_view_all_tenants(actor):
        return
    if getattr(actor, "firma_id", None) == order.alici_firma_id:
        return
    raise PermissionDenied("Bu sipariş için ödeme yetkisi yok.")


def olustur_intent(
    *,
    actor,
    order: Order,
    idempotency_key: str,
) -> PaymentIntent:
    try:
        tutar_guess, pb_guess = _order_tutar_para(order)
    except ValidationError:
        tutar_guess, pb_guess = Decimal("0.00"), "TRY"

    try:
        _assert_can_pay(actor, order)
    except PermissionDenied as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.payment.intent_denied",
            amount=tutar_guess,
            currency=pb_guess,
            order_ref=str(order.pk),
            entity_type="Order",
            entity_id=str(order.pk),
            success=False,
            reason=str(exc),
        )
        raise

    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError("Yalnız OLUSTURULDU sipariş için ödeme niyeti.")

    key = (idempotency_key or "").strip()
    if not key:
        raise ValidationError({"idempotency_key": "Zorunlu."})

    existing = PaymentIntent.objects.filter(
        alici_firma=order.alici_firma, idempotency_key=key
    ).first()
    if existing is not None:
        return existing

    if PaymentIntent.objects.filter(
        order=order, durum=PaymentIntent.Durum.BASARILI
    ).exists():
        raise ValidationError("Bu sipariş zaten tahsil edilmiş.")

    tutar, pb = _order_tutar_para(order)
    try:
        with domain_atomic():
            pi = PaymentIntent(
                order=order,
                alici_firma=order.alici_firma,
                tutar=tutar,
                para_birimi=pb,
                durum=PaymentIntent.Durum.BEKLEMEDE,
                idempotency_key=key,
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            pi.save()
            record_finans_audit(
                actor=actor,
                action="finans.payment.intent_created",
                amount=tutar,
                currency=pb,
                order_ref=str(order.pk),
                entity_type="PaymentIntent",
                entity_id=str(pi.pk),
                success=True,
                extra={"order_id": order.pk},
            )
            return pi
    except Exception as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.payment.intent_failed",
            amount=tutar,
            currency=pb,
            order_ref=str(order.pk),
            entity_type="Order",
            entity_id=str(order.pk),
            success=False,
            reason=str(exc)[:255],
        )
        raise


def _assert_intent_capturable(locked: PaymentIntent, order: Order) -> None:
    if locked.durum == PaymentIntent.Durum.BASARILI:
        return
    if locked.durum != PaymentIntent.Durum.BEKLEMEDE:
        raise ValidationError(
            f"Intent durumu tahsilata uygun değil: {locked.durum}"
        )
    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError("İptal sipariş tahsil edilemez.")
    other = (
        PaymentIntent.objects.filter(
            order_id=order.pk, durum=PaymentIntent.Durum.BASARILI
        )
        .exclude(pk=locked.pk)
        .first()
    )
    if other is not None:
        raise ValidationError("Bu sipariş zaten tahsil edilmiş.")


def tahsil_et(
    *, actor, intent: PaymentIntent, skip_provider: bool = False
) -> PaymentIntent:
    """BEKLEMEDE → BASARILI; SATIS borç (yoksa) + TAHSILAT; çift tahsilat yok.

    skip_provider=True: webhook yolu (sağlayıcı zaten tahsil etti; F5-021).
    Sağlayıcı I/O domain_atomic dışında; ledger yazımında intent+order kilidi.
    """
    order = intent.order
    if not has_perm(actor, POST_LEDGER):
        record_finans_audit_durable(
            actor=actor,
            action="finans.payment.capture_denied",
            amount=intent.tutar,
            currency=intent.para_birimi,
            order_ref=str(order.pk),
            entity_type="PaymentIntent",
            entity_id=str(intent.pk),
            success=False,
            reason="post_ledger yok",
        )
        raise PermissionDenied("Tahsilat için finans yetkisi yok.")

    # Ön kontrol (kilitli): eşzamanlı ikinci çağrı BASARILI görür / çakışmayı erken keser.
    with domain_atomic():
        locked_pre = PaymentIntent.objects.select_for_update().get(pk=intent.pk)
        order_pre = Order.objects.select_for_update().get(pk=locked_pre.order_id)
        if locked_pre.durum == PaymentIntent.Durum.BASARILI:
            return locked_pre
        _assert_intent_capturable(locked_pre, order_pre)
        intent = locked_pre
        order = order_pre

    from finans.payments import ChargeRequest, ChargeResult, get_payment_adapter

    if skip_provider:
        charge = ChargeResult(
            ok=True, provider_ref="webhook", message="skip_provider"
        )
    else:
        # F5-020: sağlayıcı charge (ledger öncesi); fail-closed
        try:
            adapter = get_payment_adapter()
            charge = adapter.charge(
                ChargeRequest(
                    intent_id=intent.pk,
                    order_id=order.pk,
                    amount=intent.tutar,
                    currency=intent.para_birimi,
                    idempotency_key=intent.idempotency_key,
                )
            )
        except ValidationError as exc:
            record_finans_audit_durable(
                actor=actor,
                action="finans.payment.provider_rejected",
                amount=intent.tutar,
                currency=intent.para_birimi,
                order_ref=str(order.pk),
                entity_type="PaymentIntent",
                entity_id=str(intent.pk),
                success=False,
                reason=str(exc)[:255],
            )
            raise

        if not charge.ok:
            reason = (charge.message or "provider_fail")[:255]
            record_finans_audit_durable(
                actor=actor,
                action="finans.payment.provider_rejected",
                amount=intent.tutar,
                currency=intent.para_birimi,
                order_ref=str(order.pk),
                entity_type="PaymentIntent",
                entity_id=str(intent.pk),
                success=False,
                reason=reason,
                extra={"provider_ref": charge.provider_ref},
            )
            with domain_atomic():
                locked = PaymentIntent.objects.select_for_update().get(pk=intent.pk)
                if locked.durum == PaymentIntent.Durum.BEKLEMEDE:
                    locked.durum = PaymentIntent.Durum.BASARISIZ
                    locked._allow_status_transition = True
                    try:
                        locked.save(update_fields=["durum", "guncelleme_tarihi"])
                    finally:
                        locked._allow_status_transition = False
                    from firmalar.services import outbox_servisi

                    outbox_servisi.enqueue(
                        event_type="payment.failed",
                        payload={
                            "intent_id": locked.pk,
                            "order_id": order.pk,
                            "alici_firma_id": order.alici_firma_id,
                            "amount": str(locked.tutar),
                            "currency": locked.para_birimi,
                            "reason": reason[:120],
                        },
                    )
            raise ValidationError(
                f"Ödeme sağlayıcı reddetti (fail-closed): {charge.message}"
            )

    platform = ensure_platform_firma()
    try:
        with domain_atomic():
            locked = PaymentIntent.objects.select_for_update().get(pk=intent.pk)
            order_locked = Order.objects.select_for_update().get(pk=locked.order_id)
            if locked.durum == PaymentIntent.Durum.BASARILI:
                return locked
            _assert_intent_capturable(locked, order_locked)

            kaydet_hareket(
                actor=actor,
                firma=order_locked.alici_firma,
                karsi_firma=platform,
                tutar=locked.tutar,
                para_birimi=locked.para_birimi,
                yon=LedgerEntry.Yon.BORC,
                hareket_tipi=LedgerEntry.HareketTipi.SATIS,
                idempotency_key=f"order-{order_locked.pk}-satis",
                referans_tip="Order",
                referans_id=str(order_locked.pk),
                aciklama=f"Sipariş #{order_locked.pk} satış borcu",
            )
            tahsil = kaydet_hareket(
                actor=actor,
                firma=order_locked.alici_firma,
                karsi_firma=platform,
                tutar=locked.tutar,
                para_birimi=locked.para_birimi,
                yon=LedgerEntry.Yon.ALACAK,
                hareket_tipi=LedgerEntry.HareketTipi.TAHSILAT,
                idempotency_key=f"pi-{locked.pk}-tahsil",
                referans_tip="PaymentIntent",
                referans_id=str(locked.pk),
                aciklama=f"PI#{locked.pk} tahsilat",
            )
            locked.durum = PaymentIntent.Durum.BASARILI
            locked.ledger_entry = tahsil
            locked._allow_status_transition = True
            try:
                locked.save(
                    update_fields=["durum", "ledger_entry", "guncelleme_tarihi"]
                )
            finally:
                locked._allow_status_transition = False
            record_finans_audit(
                actor=actor,
                action="finans.payment.captured",
                amount=locked.tutar,
                currency=locked.para_birimi,
                order_ref=str(order_locked.pk),
                entity_type="PaymentIntent",
                entity_id=str(locked.pk),
                success=True,
                extra={
                    "order_id": order_locked.pk,
                    "ledger_entry_id": tahsil.pk,
                    "provider_ref": charge.provider_ref,
                },
            )
            from firmalar.services import outbox_servisi

            outbox_servisi.enqueue(
                event_type="payment.succeeded",
                payload={
                    "intent_id": locked.pk,
                    "order_id": order_locked.pk,
                    "alici_firma_id": order_locked.alici_firma_id,
                    "amount": str(locked.tutar),
                    "currency": locked.para_birimi,
                },
            )
            return locked
    except Exception as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.payment.capture_failed",
            amount=intent.tutar,
            currency=intent.para_birimi,
            order_ref=str(order.pk),
            entity_type="PaymentIntent",
            entity_id=str(intent.pk),
            success=False,
            reason=str(exc)[:255],
        )
        raise
