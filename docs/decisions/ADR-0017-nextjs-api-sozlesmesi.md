# ADR-0017 — Next.js tüketici + `/api/v1/` uyumluluk sözleşmesi

**Durum:** **Kabul (API sözleşmesi)** — NX-1…12 madde **Kabul** (Qubit, 2026-11-09); UI runtime → [ADR-0031](ADR-0031-vite-spa-portal.md) **Kabul** (dosya adı tarihsel “Next.js”; içerik Vite’ye güncellendi)
**Bağımlılık:** ADR-0002/0003/0004 **Kabul**; PRE/F7; [ADR-0016](ADR-0016-faz9-frontend.md) **Supersede**
**Kod:** API-B1…B7 **Kabul**; NX-3…12 **kod UYGULANDI/KISMİ** (TECH-NX-CONTRACT-01). Agent yeni maddeyi Kabul etmez.

## Sabit ürün yönü

| Konu | Karar |
|------|-------|
| Yeni Django HTML | **Yok** |
| Mevcut `/buyer/`, `/ops/` | **Supersede** → [ADR-0029](ADR-0029-api-only-html-portal-kaldirma.md) **Kabul** (HTML kaldırıldı; API + Admin) |
| Yeni ürün UI | **Vite SPA** — [ADR-0031](ADR-0031-vite-spa-portal.md) **Kabul** (Qubit, 2026-11-12); Next App Router bu ADR’de supersede. API NX-1…12 aynı |
| Backend | Mevcut servisleri güvenli REST ile sunmak |
| Deploy | Aynı-origin reverse proxy tercih |

## Madde durumları

**Etiket:** Madde **Kabul** = ürün sahibi onayı. **Kod: UYGULANDI** = runtime/test kanıtı (agent maddeyi Kabul etmez).

| ID | Konu | Madde | Kod | Karar / kanıt |
|----|------|-------|-----|----------------|
| **NX-1** | Kimlik | **Kabul** (Qubit, 2026-11-09) | UYGULANDI | Session; cookie HttpOnly + Secure (prod) + SameSite=Lax; CSRF; tarayıcıda token yok; Token/Basic S2S |
| **NX-2** | Sayfalama | **Kabul** (Qubit, 2026-11-09) | UYGULANDI | `page` + `page_size`; max; sıra `-pk`; tenant |
| **CORS** | Cross-origin | **Ertelendi** | — | Aynı-origin; ihtiyaçta ayrı karar |
| **NX-3** | Hata zarfı | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `api.exception_handler` → `type`/`title`/`status`/`detail`/`code`/`request_id`; `Content-Type: application/problem+json`; `test_api_b1_standards` + `test_api_nx_contract` |
| **NX-4** | OpenAPI/drift | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `docs/api/openapi-v1.json` + `export_openapi.py --check`; B7 + TECH-OPENAPI-01 |
| **NX-5** | `/me` capabilities | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `GET /api/v1/me/` → `firma` + `capabilities`; B1 testleri |
| **NX-6** | Idempotency yazmalar | **Kabul** (Qubit, 2026-11-09) | **KISMİ (bilinçli)** | `IdempotencyMixin` + actor-scoped storage: commerce/finance/ops/supplier yazmaları. **Hariç:** `auth/login|logout` (oturum); `payments/webhook` (olay kimliği). B2 concurrency **7 OK** |
| **NX-7** | Rol sunum ayrımı | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `api.presenters.buyer` / `supplier` / `ops` / `enterprise` / `finance_ops`; ters kör B6 |
| **NX-8** | PriceLock alanları | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `expires_at`, `server_now`, `gecerli`, Decimal string; `BuyerPriceLockPresenter`; `test_api_nx_contract` |
| **NX-9** | `allowed_actions` | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | Presenter’lar; UI keşif; yazmada RBAC yeniden; B2–B6 testleri |
| **NX-10** | Cache-Control no-store | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `ApiNoStoreMiddleware` kimlikli `/api/v1/`; B1 + NX test |
| **NX-11** | API sürüm | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | `settings.API_VERSION=v1`; path `/api/v1/`; `GET /health` → `api: v1` |
| **NX-12** | Katman | **Kabul** (Qubit, 2026-11-09) | **UYGULANDI** | ADR-0004 paketler + `api` views/presenters/services; erken mikroservis yok (ROADMAP §1.1) |

## Fazlar

Canlı B0–B7 tablosu **tek kaynak:** [MASTER §12.1b](../MASTER.md). Bu ADR’de kopya tutulmaz.

Özet (yalnız okuma kolaylığı; çelişide MASTER kazanır): B1…B7 **Kabul** — 2026-11-09 (Qubit).
