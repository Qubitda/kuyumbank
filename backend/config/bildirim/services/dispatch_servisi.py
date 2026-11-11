"""Outbox handler → NotificationRule → EmailDelivery (idempotent)."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from bildirim.models import EmailDelivery, NotificationRule, RecipientSettings
from bildirim.services import template_servisi
from firmalar.models import OutboxMessage
from firmalar.services import outbox_servisi

logger = logging.getLogger(__name__)

HANDLED_EVENTS = (
    "order.created",
    "order.cancelled",
    "payment.succeeded",
    "payment.failed",
    "shipment.delivered",
    "qc.passed",
    "qc.failed",
    "return.approved",
    "firma.approved",
    "user.welcome",
)


def _recipient_settings() -> RecipientSettings:
    obj, _ = RecipientSettings.objects.get_or_create(pk=1)
    return obj


def _emails_clean(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    out: list[str] = []
    for v in values:
        e = str(v or "").strip()
        if e and e not in out:
            out.append(e)
    return out


def _resolve_customer_emails(payload: dict[str, Any]) -> list[str]:
    """Alıcı firma kullanıcı e-postaları; payload override `customer_emails`."""
    override = _emails_clean(payload.get("customer_emails"))
    if override:
        return override
    firma_id = payload.get("alici_firma_id") or payload.get("firma_id")
    if not firma_id:
        return []
    from firmalar.models import Kullanici

    qs = (
        Kullanici.objects.filter(firma_id=firma_id, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)[:50]
    )
    return _emails_clean(list(qs))


def _resolve_admin_emails() -> list[str]:
    rs = _recipient_settings()
    return _emails_clean(rs.admin_notify_emails)


def _build_context(event_type: str, payload: dict[str, Any]) -> dict[str, str]:
    ctx: dict[str, Any] = {"event_type": event_type}
    for key in template_servisi.ALLOWED_KEYS:
        if key in payload and key != "event_type":
            ctx[key] = payload[key]
    # Kör havuz: yasaklı anahtarları payload'tan asla kopyalama (ALLOWED zaten filtreler)
    if "firma_adi" not in ctx and payload.get("alici_firma_id"):
        from firmalar.models import Firma

        f = Firma.objects.filter(pk=payload["alici_firma_id"]).first()
        if f:
            ctx["firma_adi"] = f.ad
            ctx.setdefault("firma_kodu", f.firma_kodu or "")
    if "platform_name" not in ctx:
        ctx["platform_name"] = getattr(settings, "PLATFORM_BRAND_NAME", "") or "Kuyumbank"
    # Document tips
    if payload.get("document_notes"):
        ctx["document_notes"] = payload["document_notes"]
    return {k: str(v) if v is not None else "" for k, v in ctx.items()}


def _document_notes_for_order(order_id: int | None) -> str:
    if not order_id:
        return ""
    try:
        from belgeler.models import Document
        from siparis.models import Order

        order = Order.objects.filter(pk=order_id).select_related("alici_firma").first()
        if order is None:
            return ""
        docs = Document.objects.filter(firma_id=order.alici_firma_id).order_by("-pk")[
            :5
        ]
        lines = [f"{d.baslik}: {d.storage_key}" for d in docs]
        return "\n".join(lines)
    except Exception:  # noqa: BLE001 — belge opsiyonel
        return ""


def _idempotency_key(event_type: str, entity: str, recipient: str, rule_id: int) -> str:
    # max 191
    raw = f"{event_type}:{entity}:{recipient}:{rule_id}"
    return raw[:191]


def _entity_key(event_type: str, payload: dict[str, Any]) -> str:
    for k in (
        "order_id",
        "intent_id",
        "shipment_id",
        "inspection_id",
        "return_id",
        "firma_id",
        "user_id",
        "idempotency_key",
    ):
        if payload.get(k) is not None:
            return f"{k}-{payload[k]}"
    return f"outbox-{payload.get('_outbox_id', 'x')}"


def create_deliveries_for_event(
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> list[EmailDelivery]:
    payload = dict(payload or {})
    rules = list(
        NotificationRule.objects.filter(event_type=event_type, enabled=True)
        .select_related("template")
        .order_by("pk")
    )
    if not rules:
        logger.info("bildirim: no rules for event_type=%s", event_type)
        return []

    order_id = payload.get("order_id")
    try:
        order_id_int = int(order_id) if order_id is not None else None
    except (TypeError, ValueError):
        order_id_int = None

    ctx = _build_context(event_type, payload)
    entity = _entity_key(event_type, payload)
    created: list[EmailDelivery] = []
    rs = _recipient_settings()
    default_bcc = _emails_clean(rs.default_bcc)

    for rule in rules:
        if not rule.template_id or not rule.template.aktif:
            continue
        recipients: list[str] = []
        if rule.recipient_mode in (
            NotificationRule.RecipientMode.CUSTOMER,
            NotificationRule.RecipientMode.BOTH,
        ):
            recipients.extend(_resolve_customer_emails(payload))
        if rule.recipient_mode in (
            NotificationRule.RecipientMode.ADMIN,
            NotificationRule.RecipientMode.BOTH,
        ):
            recipients.extend(_resolve_admin_emails())
        recipients = _emails_clean(recipients)
        if not recipients:
            logger.info(
                "bildirim: no recipients event=%s rule=%s mode=%s",
                event_type,
                rule.pk,
                rule.recipient_mode,
            )
            continue

        local_ctx = dict(ctx)
        attach_notes = ""
        if rule.attach_document_tips:
            attach_notes = _document_notes_for_order(order_id_int)
            if attach_notes:
                local_ctx["document_notes"] = attach_notes

        try:
            subject, body = template_servisi.render_template(rule.template, local_ctx)
        except Exception:
            logger.exception("bildirim render failed rule=%s", rule.pk)
            raise

        cc = _emails_clean(rule.cc)
        bcc = _emails_clean(list(rule.bcc or []) + default_bcc)

        for to in recipients:
            key = _idempotency_key(event_type, entity, to, rule.pk)
            if EmailDelivery.objects.filter(idempotency_key=key).exists():
                continue
            safe_refs = {}
            for k, v in payload.items():
                if k in ("customer_emails", "_outbox_id"):
                    continue
                if isinstance(v, (str, int, float, bool)) or v is None:
                    safe_refs[k] = v
                else:
                    safe_refs[k] = str(v)
            delivery, was_created = EmailDelivery.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    "to_emails": [to],
                    "cc_emails": cc,
                    "bcc_emails": bcc,
                    "subject": subject,
                    "body_html": body,
                    "status": EmailDelivery.Status.PENDING,
                    "template": rule.template,
                    "rule": rule,
                    "event_type": event_type,
                    "order_id": order_id_int,
                    "related_refs": safe_refs,
                    "attachment_notes": attach_notes,
                },
            )
            if was_created:
                created.append(delivery)
    return created


def handle_outbox_message(msg: OutboxMessage) -> None:
    payload = dict(msg.payload or {})
    payload["_outbox_id"] = msg.pk
    create_deliveries_for_event(event_type=msg.event_type, payload=payload)


def register_outbox_handlers() -> None:
    for event in HANDLED_EVENTS:
        outbox_servisi.register_handler(event, handle_outbox_message)
