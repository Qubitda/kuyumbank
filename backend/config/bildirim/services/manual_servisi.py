"""Admin manuel gönderim → EmailDelivery."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError

from bildirim.models import EmailDelivery, EmailTemplate
from bildirim.services import template_servisi
from firmalar.services.yetki_servisi import has_perm

SEND_MANUAL = "bildirim.send_manual_email"


def enqueue_manual(
    *,
    actor,
    to_emails: list[str],
    subject: str | None = None,
    body_html: str | None = None,
    template: EmailTemplate | None = None,
    context: dict[str, Any] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    order_id: int | None = None,
) -> EmailDelivery:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Kimlik gerekli.")
    if not has_perm(actor, SEND_MANUAL) and not getattr(actor, "is_superuser", False):
        raise PermissionDenied("Manuel e-posta yetkisi yok.")

    tos = [e.strip() for e in (to_emails or []) if e and str(e).strip()]
    if not tos:
        raise ValidationError("Alıcı zorunlu.")

    tpl = template
    if tpl is not None:
        subj, html = template_servisi.render_template(tpl, context)
    else:
        if not (subject or "").strip():
            raise ValidationError("Konu veya şablon zorunlu.")
        subj, html = template_servisi.render(
            subject=subject or "",
            body=body_html or "",
            context=context,
        )

    key = f"manual:{uuid.uuid4().hex}"
    return EmailDelivery.objects.create(
        to_emails=tos,
        cc_emails=[e for e in (cc or []) if e],
        bcc_emails=[e for e in (bcc or []) if e],
        subject=subj,
        body_html=html,
        status=EmailDelivery.Status.PENDING,
        template=tpl,
        event_type="manual",
        idempotency_key=key[:191],
        order_id=order_id,
        related_refs={"manual": True, "actor_id": getattr(actor, "pk", None)},
    )
