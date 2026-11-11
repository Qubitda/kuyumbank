"""Sistem e-posta şablonları + varsayılan kurallar (idempotent)."""

from __future__ import annotations

from bildirim.models import EmailTemplate, NotificationRule

_SEED_TEMPLATES: list[dict] = [
    {
        "kod": "order_created",
        "ad": "Sipariş oluşturuldu",
        "subject": "Sipariş #{{order_id}} alındı",
        "html_body": "<p>Merhaba {{firma_adi}},</p><p>Sipariş <strong>#{{order_id}}</strong> oluşturuldu ({{line_count}} kalem).</p>",
    },
    {
        "kod": "order_cancelled",
        "ad": "Sipariş iptal",
        "subject": "Sipariş #{{order_id}} iptal edildi",
        "html_body": "<p>Sipariş <strong>#{{order_id}}</strong> iptal edildi.</p>",
    },
    {
        "kod": "payment_succeeded",
        "ad": "Ödeme başarılı",
        "subject": "Ödeme alındı — sipariş #{{order_id}}",
        "html_body": "<p>Ödeme başarılı: {{amount}} {{currency}} (sipariş #{{order_id}}).</p>",
    },
    {
        "kod": "payment_failed",
        "ad": "Ödeme başarısız",
        "subject": "Ödeme başarısız — sipariş #{{order_id}}",
        "html_body": "<p>Ödeme başarısız (sipariş #{{order_id}}): {{reason}}</p>",
    },
    {
        "kod": "shipment_delivered",
        "ad": "Sevkiyat teslim",
        "subject": "Teslimat — sevkiyat #{{shipment_id}}",
        "html_body": "<p>Sevkiyat <strong>#{{shipment_id}}</strong> teslim edildi. Takip: {{takip_no}}</p>",
    },
    {
        "kod": "qc_passed",
        "ad": "QC geçti",
        "subject": "QC PASS — sipariş #{{order_id}}",
        "html_body": "<p>Kalite kontrolü geçti (inspection #{{inspection_id}}, sipariş #{{order_id}}).</p>",
    },
    {
        "kod": "qc_failed",
        "ad": "QC kaldı",
        "subject": "QC FAIL — sipariş #{{order_id}}",
        "html_body": "<p>Kalite kontrolü başarısız (inspection #{{inspection_id}}): {{reason}}</p>",
    },
    {
        "kod": "return_approved",
        "ad": "İade onaylandı",
        "subject": "İade onaylandı — #{{return_id}}",
        "html_body": "<p>İade talebi #{{return_id}} onaylandı (sipariş #{{order_id}}).</p>",
    },
    {
        "kod": "firma_approved",
        "ad": "Firma onaylandı",
        "subject": "Hesabınız onaylandı — {{firma_adi}}",
        "html_body": "<p>{{firma_adi}} ({{firma_kodu}}) hesabınız onaylandı.</p>",
    },
    {
        "kod": "user_welcome",
        "ad": "Hoş geldiniz",
        "subject": "Hoş geldiniz — {{platform_name}}",
        "html_body": "<p>Merhaba {{user_name}},</p><p>{{platform_name}} hesabınız oluşturuldu ({{user_email}}).</p>",
    },
    {
        "kod": "invoice_manual",
        "ad": "Fatura (manuel)",
        "subject": "Fatura — sipariş #{{order_id}}",
        "html_body": "<p>Fatura bilgisi (sipariş #{{order_id}}).</p><p>{{document_notes}}</p>",
    },
    {
        "kod": "voucher_manual",
        "ad": "Voucher (manuel)",
        "subject": "Voucher — sipariş #{{order_id}}",
        "html_body": "<p>Voucher (sipariş #{{order_id}}).</p><p>{{document_notes}}</p>",
    },
    {
        "kod": "list_manual",
        "ad": "Liste (manuel)",
        "subject": "Liste belgesi",
        "html_body": "<p>Liste belgesi.</p><p>{{document_notes}}</p>",
    },
]

_EVENT_TEMPLATE = {
    "order.created": "order_created",
    "order.cancelled": "order_cancelled",
    "payment.succeeded": "payment_succeeded",
    "payment.failed": "payment_failed",
    "shipment.delivered": "shipment_delivered",
    "qc.passed": "qc_passed",
    "qc.failed": "qc_failed",
    "return.approved": "return_approved",
    "firma.approved": "firma_approved",
    "user.welcome": "user_welcome",
}


def seed_templates_and_rules() -> dict[str, int]:
    created_t = 0
    updated_t = 0
    for row in _SEED_TEMPLATES:
        obj, created = EmailTemplate.objects.update_or_create(
            kod=row["kod"],
            defaults={
                "ad": row["ad"],
                "subject": row["subject"],
                "html_body": row["html_body"],
                "aktif": True,
                "sistem_mi": True,
            },
        )
        if created:
            created_t += 1
        else:
            updated_t += 1

    created_r = 0
    for event, kod in _EVENT_TEMPLATE.items():
        tpl = EmailTemplate.objects.get(kod=kod)
        _, created = NotificationRule.objects.get_or_create(
            event_type=event,
            template=tpl,
            recipient_mode=NotificationRule.RecipientMode.CUSTOMER,
            defaults={"enabled": True, "aciklama": f"Seed: {event}"},
        )
        if created:
            created_r += 1
        # Admin kopyası (BOTH yerine ayrı ADMIN kuralı — log netliği)
        _, created_a = NotificationRule.objects.get_or_create(
            event_type=event,
            template=tpl,
            recipient_mode=NotificationRule.RecipientMode.ADMIN,
            defaults={
                "enabled": event
                in ("order.created", "payment.failed", "qc.failed", "firma.approved"),
                "aciklama": f"Seed admin: {event}",
            },
        )
        if created_a:
            created_r += 1

    return {
        "templates_created": created_t,
        "templates_updated": updated_t,
        "rules_created": created_r,
    }
