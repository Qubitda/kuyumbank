# ADR-0028 — Kullanıcı daveti + e-posta doğrulama

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — API-only onay paketi)  
**Bağımlılık:** ADR-0003 RBAC; soft-launch §11d  
**Kapsam ID:** CAP-INVITE-EMAIL

## Kararlar

| ID | Karar |
|----|--------|
| IE-1 | Firma kullanıcısı **davet** ile oluşturulur (`manage_users` / `manage_all_users`); public self-reg yok. |
| IE-2 | Davet: e-posta + rol + TTL token; kabulde parola set + `email_verified_at` doldurulur. |
| IE-3 | Mevcut kullanıcılar için ayrı e-posta doğrulama token’ı; login engeli varsayılan **kapalı** (`EMAIL_VERIFY_REQUIRED_FOR_WRITE`). |
| IE-4 | Platform rolleri daveti yalnız `manage_all_users`. |
| IE-5 | FE/Next bu ADR’de zorunlu değil; API + Admin. |

## Yüzey

| Yol | Not |
|-----|-----|
| `POST /api/v1/auth/invites/create/` | `manage_users`; platform `firma_id` |
| `GET /api/v1/auth/invites/` | bekleyen davetler |
| `POST /api/v1/auth/invites/accept/` | anon; username+parola |
| `POST /api/v1/auth/email-verify/` | request |
| `POST /api/v1/auth/email-verify/confirm/` | uid+token |
| `/me` | `email_verified` + `capabilities.can_manage_users` |
| Settings | `INVITE_TTL_HOURS` (72), `EMAIL_VERIFY_REQUIRED_FOR_WRITE` (False) |
| Mig | `firmalar.0012_invite_email_verify` |

## Checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10) |
| Kod + odaklı test | `firmalar.tests.test_invite_email_verify` **8 OK** |
