# ADR-0027 — E-posta / bildirim (Django Admin)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “go”)  
**Bağımlılık:** F4-090 transactional outbox; F11-013 bildirim iskeleti; ADR-0004 paket düzeni  
**Kapsam ID:** CAP-EMAIL-BILDIRIM

## Kararlar

| ID | Karar |
|----|--------|
| EB-1 | UI = Django Admin (`bildirim` app); Next.js bu ADR’de yok. |
| EB-2 | Celery yok; domain → `OutboxMessage` → handler → `EmailDelivery` → `process_email_queue` (SMTP). |
| EB-3 | Tek platform SMTP (`SmtpSettings` singleton); parola SECRET_KEY türevi sealed at-rest; admin write-only. |
| EB-4 | Şablonlar allowlist context; kör havuz (alıcı mailinde tedarikçi kimliği/maliyet yok). |
| EB-5 | Idempotency: `EmailDelivery.idempotency_key` UNIQUE (`event_type:entity:recipient`). |
| EB-6 | Fatura/voucher/liste PDF üretimi ve object storage (K-014) **dışı**; ek yalnızca mevcut `Document` metadata varsa. |
| EB-7 | RBAC: `manage_smtp`, `manage_email_template`, `manage_notification_rule`, `send_manual_email`, `view_email_log`. |

## Event eşlemesi

| event_type | Kaynak |
|------------|--------|
| `order.created` | mevcut |
| `order.cancelled` | `iptal_siparis` enqueue |
| `payment.succeeded` / `payment.failed` | `payment_servisi` |
| `shipment.delivered` | `teslim_et` |
| `qc.passed` / `qc.failed` | mevcut |
| `return.approved` | mevcut |
| `firma.approved` | `firma_onay_servisi` |
| `user.welcome` | kullanıcı oluşturma (bootstrap dışı) |

## Checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10) |
| Kod + odaklı test + RUNBOOK | UYGULANDI |
| Migrate + cron (`process_outbox` + `process_email_queue`) | Bu dilim |
