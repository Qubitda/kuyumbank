"""F5-021 — Ödeme webhook işleme; aynı event_id → tek sonuç."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from firmalar import roles
from firmalar.models import Kullanici
from finans.models import PaymentIntent, PaymentWebhookEvent
from finans.services import payment_servisi
from finans.services.finans_audit import record_finans_audit_durable


def _platform_finance_actor() -> Kullanici:
    user = (
        Kullanici.objects.filter(
            rol=roles.PLATFORM_FINANCE,
            firma__platform_mu=True,
            is_active=True,
        )
        .order_by("pk")
        .first()
    )
    if user is None:
        raise ValidationError("Webhook: platform finance aktör bulunamadı.")
    return user


def isle_webhook(
    *,
    provider: str,
    event_id: str,
    event_type: str,
    payload: dict,
    actor=None,
) -> PaymentWebhookEvent:
    """Tekrarlayan (provider, event_id) → mevcut kayıt (idempotent).

    Başarısız işlemde satır yazılmaz → aynı event yeniden denenebilir.
    """
    provider = (provider or "fake").strip().lower()
    event_id = (event_id or "").strip()
    event_type = (event_type or "").strip()
    if not event_id:
        raise ValidationError({"event_id": "Zorunlu."})
    if not event_type:
        raise ValidationError({"event_type": "Zorunlu."})
    payload = payload or {}

    existing = PaymentWebhookEvent.objects.filter(
        provider=provider, event_id=event_id
    ).first()
    if existing is not None:
        return existing

    actor = actor or _platform_finance_actor()
    intent = None

    try:
        with transaction.atomic():
            if event_type == "payment.succeeded":
                intent_id = payload.get("intent_id")
                if not intent_id:
                    raise ValidationError(
                        {"intent_id": "payment.succeeded için zorunlu."}
                    )
                try:
                    intent = PaymentIntent.objects.select_for_update().get(
                        pk=intent_id
                    )
                except PaymentIntent.DoesNotExist as exc:
                    raise ValidationError(
                        {"intent_id": "PaymentIntent yok."}
                    ) from exc

                payment_servisi.tahsil_et(
                    actor=actor, intent=intent, skip_provider=True
                )
                intent.refresh_from_db()
                sonuc = PaymentWebhookEvent.Sonuc.ISLENDI
                detail = f"PI#{intent.pk} {intent.durum}"
            else:
                sonuc = PaymentWebhookEvent.Sonuc.YOK_SAYILDI
                detail = f"desteklenmeyen event_type={event_type}"

            try:
                row = PaymentWebhookEvent(
                    provider=provider,
                    event_id=event_id,
                    event_type=event_type,
                    payload=payload,
                    payment_intent=intent,
                    sonuc=sonuc,
                    detail=detail[:255],
                )
                row.save()
                return row
            except IntegrityError:
                return PaymentWebhookEvent.objects.get(
                    provider=provider, event_id=event_id
                )
    except Exception as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.payment.webhook_failed",
            amount=getattr(intent, "tutar", None) or "0.00",
            currency=getattr(intent, "para_birimi", None) or "TRY",
            order_ref=str(
                getattr(getattr(intent, "order", None), "pk", "") or ""
            ),
            entity_type="PaymentWebhookEvent",
            entity_id=event_id,
            success=False,
            reason=str(exc)[:255],
        )
        raise
