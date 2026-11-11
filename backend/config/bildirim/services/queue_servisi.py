"""PENDING EmailDelivery kuyruğu — SMTP gönder + retry."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from bildirim.models import EmailDelivery
from bildirim.services import smtp_servisi

logger = logging.getLogger(__name__)


def _max_attempts() -> int:
    smtp = smtp_servisi.get_or_create_singleton()
    return int(smtp.max_attempts or 5)


def process_email_queue(*, limit: int = 100) -> dict[str, int]:
    if limit <= 0:
        from django.core.exceptions import ValidationError

        raise ValidationError("limit pozitif olmalı.")

    max_att = _max_attempts()
    ids = list(
        EmailDelivery.objects.filter(status=EmailDelivery.Status.PENDING)
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    sent = 0
    failed = 0
    skipped = 0

    for pk in ids:
        with transaction.atomic():
            row = (
                EmailDelivery.objects.select_for_update()
                .filter(pk=pk, status=EmailDelivery.Status.PENDING)
                .first()
            )
            if row is None:
                skipped += 1
                continue
            try:
                smtp_servisi.send_raw(
                    to=list(row.to_emails or []),
                    subject=row.subject,
                    body_html=row.body_html,
                    cc=list(row.cc_emails or []),
                    bcc=list(row.bcc_emails or []),
                )
                row.status = EmailDelivery.Status.SENT
                row.attempts = row.attempts + 1
                row.error = ""
                row.sent_at = timezone.now()
                row.save(
                    update_fields=[
                        "status",
                        "attempts",
                        "error",
                        "sent_at",
                        "updated_at",
                    ]
                )
                sent += 1
            except Exception as exc:  # noqa: BLE001
                row.attempts = row.attempts + 1
                row.error = str(exc)[:255]
                if row.attempts >= max_att:
                    row.status = EmailDelivery.Status.FAILED
                row.save(update_fields=["attempts", "error", "status", "updated_at"])
                failed += 1
                logger.exception("email queue send failed id=%s", pk)

    return {
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "seen": len(ids),
    }


def retry_delivery(delivery: EmailDelivery) -> EmailDelivery:
    """FAILED → PENDING (attempts korunur; limit aşımında admin bilinçli)."""
    if delivery.status == EmailDelivery.Status.SENT:
        from django.core.exceptions import ValidationError

        raise ValidationError("Gönderilmiş kayıt yeniden kuyruğa alınamaz.")
    delivery.status = EmailDelivery.Status.PENDING
    delivery.error = ""
    delivery.save(update_fields=["status", "error", "updated_at"])
    return delivery
