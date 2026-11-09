"""F7-020 — Outbox üzerine idempotent webhook delivery kaydı."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from firmalar.models import OutboxMessage, WebhookDelivery


def ensure_delivery(
    *,
    outbox: OutboxMessage,
    endpoint_key: str,
    idempotency_key: str | None = None,
) -> WebhookDelivery:
    """Aynı (outbox, endpoint, idempotency) için tek satır — tekrar çağrı aynı kaydı döner."""
    key = (idempotency_key or f"outbox-{outbox.pk}-{endpoint_key}").strip()[:128]
    ep = (endpoint_key or "default").strip()[:64]
    existing = WebhookDelivery.objects.filter(
        outbox=outbox, endpoint_key=ep, idempotency_key=key
    ).first()
    if existing is not None:
        return existing
    return WebhookDelivery.objects.create(
        outbox=outbox,
        endpoint_key=ep,
        idempotency_key=key,
        durum=WebhookDelivery.Durum.PENDING,
    )


def mark_delivered(
    delivery: WebhookDelivery, *, response_code: int | None = 200
) -> WebhookDelivery:
    with transaction.atomic():
        locked = WebhookDelivery.objects.select_for_update().get(pk=delivery.pk)
        if locked.durum == WebhookDelivery.Durum.DELIVERED:
            return locked
        locked.durum = WebhookDelivery.Durum.DELIVERED
        locked.attempts = locked.attempts + 1
        locked.response_code = response_code
        locked.last_error = ""
        locked.delivered_at = timezone.now()
        locked.save(
            update_fields=[
                "durum",
                "attempts",
                "response_code",
                "last_error",
                "delivered_at",
            ]
        )
        return locked


def mark_failed(delivery: WebhookDelivery, *, error: str) -> WebhookDelivery:
    with transaction.atomic():
        locked = WebhookDelivery.objects.select_for_update().get(pk=delivery.pk)
        locked.attempts = locked.attempts + 1
        locked.last_error = (error or "")[:255]
        if locked.attempts >= 5:
            locked.durum = WebhookDelivery.Durum.FAILED
        locked.save(update_fields=["attempts", "last_error", "durum"])
        return locked


def deliver_fake(*, outbox: OutboxMessage, endpoint_key: str = "fake") -> WebhookDelivery:
    """Test/iskelet: delivery kaydı + hemen DELIVERED (HTTP yok)."""
    d = ensure_delivery(outbox=outbox, endpoint_key=endpoint_key)
    if d.durum == WebhookDelivery.Durum.DELIVERED:
        return d
    return mark_delivered(d, response_code=200)
