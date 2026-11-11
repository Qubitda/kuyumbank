# ADR-0029 — API-only HTTP: buyer/supplier/ops HTML portal kaldırma

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “onaylıyorum”)  
**Bağımlılık:** ADR-0021 (act-as çekirdek kalır; HTML portal maddeleri bu ADR ile supersede); ADR-0017 Next; B1–B7 API  
**Kapsam ID:** CAP-API-ONLY

## Amaç

Django ürün yüzeyi **yalnız** `/admin/` + `/api/v1/` (+ OpenAPI docs).  
`/buyer/`, `/supplier/`, `/ops/` HTML SSR kaldırılır. Kullanıcı işlemleri REST/JSON.

## Kararlar

| ID | Karar |
|----|--------|
| AO-1 | `/buyer/`, `/supplier/`, `/ops/` URL + template + `*_ui` view **silinir**. |
| AO-2 | Domain servisleri değişmez; RBAC/API permission aynı. |
| AO-3 | Act-as servis+middleware+audit **kalır**; JSON API `POST /api/v1/act-as/start|stop/`; redirect `FRONTEND_PORTAL_BASE_URL` veya `/admin/`. |
| AO-4 | `LOGIN_URL` → `/admin/login/`; HTML login throttle yalnız Admin. |
| AO-5 | Buyer dashboard HTTP: `GET /api/v1/me/dashboard/` (`buyer_dashboard_servisi`). |
| AO-6 | Django Admin + admin şablonları **korunur**. |
| AO-7 | ADR-0021 AA-6/AA-7 HTML portal maddeleri **supersede**; act-as AA-1…5, AA-9 geçerli. |
| AO-8 | Next/FE `PASSWORD_RESET_BASE_URL` + API; Django HTML portal yok. |

## Checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10) |
| Kod + odaklı test | Act-as/dashboard/throttle/security/auth/invite odaklı **36 OK** |
| HTML portal silindi | UYGULANDI |
