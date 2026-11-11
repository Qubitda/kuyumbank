# NX-FE Frontend Handoff

**Tarih:** 2026-11-11  
**Kaynak:** çalışan kod + OpenAPI (`docs/api/openapi-v1.json`) — niyet değil.  
**Normatif sözleşme:** [API_CONTRACT](API_CONTRACT.md) · [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md)  
**Frontend mimari:** [FRONTEND_ARCHITECTURE](../frontend/docs/FRONTEND_ARCHITECTURE.md)

Bu belge, Next.js (NX-FE) geliştiricisinin Django `/api/v1/` ile güvenli entegrasyon için ihtiyaç duyduğu **uygulanmış** davranışı özetler.

---

## 1. Backend architecture overview

- Django **6.1.2** modular monolith (`backend/config/`).
- Domain apps: `firmalar`, `urunler`, `fiyatlama`, `stok`, `siparis`, `finans`, … + HTTP app `api`.
- Business rules in `services/`; tenant reads in `selectors/`; HTTP presenters in `api/presenters/`.
- PostgreSQL required. Celery/Redis **yok** (bilinçli).
- Browser auth: **session + CSRF** (same-origin Next rewrite). DRF Token = S2S only.

## 2. API base URL

| Ortam | Tarayıcı tabanı | Gerçek Django |
|-------|-----------------|---------------|
| Yerel NX-FE | `/api/v1` (aynı origin) | `DJANGO_ORIGIN` → default `http://127.0.0.1:8000` |
| Prod | Aynı-origin reverse proxy `/api/v1` | Backend host (proxy arkasında) |

`next.config.ts` rewrite: `/api/v1/:path*` → `${DJANGO_ORIGIN}/api/v1/:path*`.

## 3. Authentication flow

```text
GET  /api/v1/auth/csrf/          → csrf_token + csrftoken cookie
POST /api/v1/auth/login/         → sessionid; body = me + mfa_* flags
GET  /api/v1/me/                 → identity + capabilities
POST /api/v1/auth/logout/        → session clear + kullanıcının DRF Token silinir
```

- Session cookie: **HttpOnly**, SameSite=**Lax**, Secure when `DEBUG=False`.
- CSRF cookie: **not** HttpOnly (JS/BFF okur); SameSite=Lax; Secure when `DEBUG=False`.
- **Tarayıcıda DRF Token yok** (NX-1).
- MFA: `MFA_ENFORCE_PLATFORM` açıkken platform kullanıcıları `mfa_ok` olmadan API’ye giremez; yanıt `application/problem+json` (`code=mfa_required`).

## 4. CSRF requirements

Mutating methods (`POST`/`PATCH`/`DELETE`/`PUT`): header `X-CSRFToken` = `csrftoken` cookie veya `/auth/csrf/` gövdesi.  
İstemci: `frontend/src/lib/api/client.ts` → `ensureCsrfToken()` + `credentials: "include"`.

Django: `CSRF_TRUSTED_ORIGINS` (yerel: `http://localhost:3000`). Rewrite aynı-origin olduğu için çoğu yazma SameSite Lax ile çalışır; trusted origins yine ayarlanmalı.

## 5. Next.js rewrite requirements

- CORS **yok** — tarayıcıdan doğrudan Django origin’e credentialed istek atma.
- `DJANGO_ORIGIN` `.env.local` içinde (bkz. `frontend/.env.example`).
- İkinci API client oluşturma.

## 6. Environment variables

**Frontend**

| Değişken | Örnek | Rol |
|----------|-------|-----|
| `DJANGO_ORIGIN` | `http://127.0.0.1:8000` | Rewrite hedefi |

**Backend (özet)** — tam tablo: [RUNBOOK](RUNBOOK.md) §2

| Değişken | Not |
|----------|-----|
| `SECRET_KEY`, `DB_*` | Zorunlu |
| `DEBUG` | Prod `False` |
| `ALLOWED_HOSTS` | Prod zorunlu |
| `CSRF_TRUSTED_ORIGINS` | Yerel Next |
| `SESSION_COOKIE_DOMAIN` / `CSRF_COOKIE_DOMAIN` | Paylaşımlı üst alan gerekirse |
| `MEDIA_URL` / `MEDIA_ROOT` | ImageField; belge HTTP yok |
| `API_DOCS_PUBLIC` | Prod varsayılan `False` |
| `MFA_ENFORCE_PLATFORM` | Prod soft-launch checklist |

## 7. OpenAPI location

- Normatif: `docs/api/openapi-v1.json` (**106** path / **120** op — 2026-11-11 hardening sonrası).
- Canlı: `/api/schema/`, UI `/api/docs/`, `/api/redoc/`.
- Prod/docs kapalıyken: kimlikli **staff** veya platform `view_all` (Session/Token).

## 8. TypeScript generation command

```bash
cd frontend
npm run generate:api
# → lib/api/schema.d.ts
```

API değişince OpenAPI export + generate birlikte.

## 9. API response format

- Başarı: `application/json` (presenter DTO).
- Listeler (standart): `{ count, next, previous, page, page_size, results }`.
- İstisnalar: invites (`results` only), bazı rapor/özet uçları (sayfasız), RFQ match hard-slice.
- Decimal / para / gram: **string** (JSON number değil).
- Tarih: ISO-8601 string; çoğu yanıtta `server_now`.

## 10. Error handling format

`Content-Type: application/problem+json`

```json
{
  "type": "https://kuyumbank.local/problems/<code>",
  "title": "...",
  "status": 400,
  "detail": "...",
  "code": "validation_error",
  "request_id": "...",
  "errors": { "field": [{ "code": "invalid", "message": "..." }] }
}
```

FE: `ApiError` / `ProblemDetail` (`src/lib/api/types.ts`).  
Webhook provider yolu `{"detail"}` dönebilir (bilinçli istisna).

## 11. Pagination conventions

Query: `page` (default 1), `page_size` (default 25, max 100).  
Bilinmeyen `ordering` alanları yok sayılır; whitelist view’da.

## 12. Filtering and sorting conventions

Per-endpoint query params (`durum`, `order_id`, `q`, tarihler, …).  
django-filter yok. Catalog search: `q`.  
Ops supplier list: `?tedarikci_id=` (yalnız `view_all`).

## 13. Permission model

- `GET /me/` → `rol`, `firma`, `email_verified`, `capabilities` (UI keşif).
- Kaynak DTO’larda `allowed_actions` (UI keşif).
- **Her yazma sunucuda RBAC + tenant yeniden doğrulanır.** UI gizleme güvenlik değildir.
- Tenant: client `firma_id` güvenilmez; çapraz tenant → **404**.

## 14. Idempotency requirements

Header: `Idempotency-Key` (actor-scoped).  
Zorunlu: commerce/finance/ops/supplier yazmalarının çoğu (cart line PATCH/DELETE, address yazma dahil).  
**Hariç (bilinçli):** `auth/login|logout`, `payments/webhook`; ayrıca invite create / MFA / act-as / profile PATCH şu an IK istemez.  
Çakışma (aynı key, farklı body) → **409**.

## 15. Decimal handling

Always `string` in JSON. FE display with `tabular-nums`; commercial math stays on Django.

## 16. File upload/download limitations

- Belge HTTP API **FE v1 dışı** (`belgeler` domain var; HTTP yok).
- `MEDIA_*` ayarlı; ImageField lokal disk. Prod’da public MEDIA serve etme; private document = `storage_key` modeli (henüz signed URL yok).

## 17. Known API limitations

- CORS yok (aynı-origin).
- Org update/deactivate HTTP yok.
- Spend-limit CRUD HTTP yok.
- Contract release HTTP yok.
- Ops order cancel HTTP yok (buyer cancel var).
- Payment/carrier provider = fake (prod fake yasak flag’leri).
- Invite list sayfalama zarfı standart değil.
- Health = liveness; **Ready** = DB (`GET /api/v1/ready/`).

## 18. Unsupported frontend operations

Uydurma endpoint yok. OpenAPI’de olmayan path/method çağırma.  
Browser Token auth yok.  
SSR’da keyfi cookie forward yok — mevcut portal iskeleti Client Components + rewrite ile yeterlidir; ek SSR cookie proxy **gerekmiyor**.

## 19. Local development instructions

```bash
# Backend
cd backend
# .venv aktif; config/.env: DEBUG, DB_*, CSRF_TRUSTED_ORIGINS=http://localhost:3000
cd config
python manage.py migrate
python manage.py seed_demo_portals
python manage.py seed_tanimlar
python manage.py seed_urunler
python manage.py seed_demo_commerce   # yayınlı ürün + teklif + sözleşme + stok
python manage.py runserver

# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Smoke (bağlayıcı): `cd frontend && npm run smoke` — **Next origin** üzerinden CSRF → login → `/me/` → health.  
Django’ya doğrudan istek bu kapıyı geçirmez. Auth/proxy/`next.config` değişince zorunlu.  
Ek: `npm run lint`, `npm run build`. Kural: `frontend/.cursor/rules/06-integration-gates.mdc`.

## 20. Production integration requirements

- `DEBUG=False`; secrets env’den; HTTPS + Secure cookies.
- Same-origin reverse proxy Next ↔ Django `/api/v1`.
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, proxy SSL header gerektiğinde.
- Liveness: `/api/v1/health/` · Readiness: `/api/v1/ready/` (DB).
- Docs: `API_DOCS_PUBLIC=False`; staff/platform Session veya Token.
- `soft_launch_check`; fake provider’lar kapalı; cache table; MFA politikası ürün kararı.
- Process server / static collect: RUNBOOK (hosting henüz yok — şablon).
- Logout Token revoke: S2S için ayrı service hesabı kullanın (browser logout aynı kullanıcının Token’ını siler).

---

**Karar özeti:** Backend **FRONTEND READY**; NX-FE iskelet **INTEGRATION READY**. Tam portal ürün dilimleri OpenAPI’ye bağlı geliştirilebilir.
