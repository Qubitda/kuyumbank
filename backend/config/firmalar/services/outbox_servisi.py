"""Transactional outbox — F4-090.

`enqueue` domain_atomic içinde çağrılır → rollback outbox satırını da siler.
`process_pending` management command / sync worker; at-least-once.
Celery yok (F8).
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from firmalar.models import OutboxMessage
from firmalar.services.audit_servisi import _in_domain_atomic

logger = logging.getLogger(__name__)

Handler = Callable[[OutboxMessage], None]

# İskelet handler kaydı — gerçek bildirim F7/F8.
_HANDLERS: dict[str, Handler] = {}


def register_handler(event_type: str, handler: Handler) -> None:
    _HANDLERS[event_type] = handler


def _default_handler(msg: OutboxMessage) -> None:
    """İskelet: olay kabul edildi (yan etki yok)."""
    logger.info(
        "outbox processed event_type=%s id=%s payload_keys=%s",
        msg.event_type,
        msg.pk,
        sorted((msg.payload or {}).keys()),
    )


def enqueue(
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> OutboxMessage:
    """Domain yazımıyla aynı atomic'te outbox satırı oluşturur.

    domain_atomic dışında çağrı → ValidationError (yanlışlıkla durable sandırmamak).
    """
    event_type = (event_type or "").strip()
    if not event_type:
        raise ValidationError("event_type zorunlu.")
    if not _in_domain_atomic.get():
        raise ValidationError(
            "outbox.enqueue yalnız domain_atomic() içinde çağrılır "
            "(F4-090 transactional outbox)."
        )
    return OutboxMessage.objects.create(
        event_type=event_type,
        payload=payload or {},
        durum=OutboxMessage.Durum.PENDING,
    )


def process_pending(*, limit: int = 100) -> dict[str, int]:
    """PENDING mesajları işle; en az bir kez (at-least-once).

    Başarılı handler → PROCESSED. Hata → attempts++ / FAILED (attempts>=5).
    """
    if limit <= 0:
        raise ValidationError("limit pozitif olmalı.")

    processed = 0
    failed = 0
    skipped = 0

    # id listesini önce al; her satırı kendi atomic'inde kilitle
    ids = list(
        OutboxMessage.objects.filter(durum=OutboxMessage.Durum.PENDING)
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )

    for pk in ids:
        with transaction.atomic():
            msg = (
                OutboxMessage.objects.select_for_update()
                .filter(pk=pk, durum=OutboxMessage.Durum.PENDING)
                .first()
            )
            if msg is None:
                skipped += 1
                continue
            handler = _HANDLERS.get(msg.event_type, _default_handler)
            try:
                handler(msg)
                msg.durum = OutboxMessage.Durum.PROCESSED
                msg.processed_at = timezone.now()
                msg.attempts = msg.attempts + 1
                msg.last_error = ""
                msg.save(
                    update_fields=[
                        "durum",
                        "processed_at",
                        "attempts",
                        "last_error",
                    ]
                )
                processed += 1
            except Exception as exc:  # noqa: BLE001 — worker dayanıklılığı
                msg.attempts = msg.attempts + 1
                msg.last_error = str(exc)[:255]
                if msg.attempts >= 5:
                    msg.durum = OutboxMessage.Durum.FAILED
                msg.save(update_fields=["attempts", "last_error", "durum"])
                failed += 1
                logger.exception("outbox handler failed id=%s", pk)

    return {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "seen": len(ids),
    }
