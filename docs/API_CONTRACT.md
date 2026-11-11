# Kuyumbank API sözleşmesi (insan özeti)

**Rol:** Frontend / entegrasyon için kısa rehber.  
**Normatif teknik sözleşme:** [`docs/api/openapi-v1.json`](api/openapi-v1.json)  
**Politika:** [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md) (Taslak; NX-1…12 madde Kabul)  
**Durum:** API-B7 dondurma dilimi — OpenAPI ile çelişen ikinci sözleşme değildir; şüphede OpenAPI + kod kazanır.

Üretim / doğrulama:

```text
python scripts/export_openapi.py
python scripts/export_openapi.py --check
python scripts/lint_openapi.py
```

Canlı dokümantasyon (aynı şema kaynağı):

| Yüzey | URL | Not |
|-------|-----|-----|
| OpenAPI JSON | `/api/schema/` (alias `/api/v1/schema/`) | DRF generator + DTO enrich |
| Swagger UI | `/api/docs/` | drf-spectacular UI |
| ReDoc | `/api/redoc/` | drf-spectacular UI |

Erişim: `DEBUG=True` veya `API_DOCS_PUBLIC=True`; aksi halde kimlikli staff/platform. Try it out gerçek RBAC uygular.

---

## 1. Frontend-ready checklist

| # | Konu | Beklenti |
|---|------|----------|
| 1 | Auth (tarayıcı) | Session cookie; `GET /api/v1/auth/csrf/` → login; CSRF header; Token tarayıcıda yok (NX-1). Davet/verify (ADR-0028); act-as `/act-as/start|stop/` (ADR-0029); `/me` + `/me/dashboard/`. Django HTML portal yok. |
| 2 | Auth (S2S) | `TokenAuthentication` / Basic; ayrı istemci |
| 3 | Tenant | `firma_id` / `tedarikci_id` / `alici_id` client’tan **güvenilmez**; sunucu `request.user.firma` |
| 4 | Keşif | `GET /api/v1/me/` → `firma` + `capabilities` (UI bayrak; her uç yine RBAC) |
| 5 | Sözleşme | Path/method/status → OpenAPI; alan uydurma yok |
| 6 | Hata | `application/problem+json` (`type`/`title`/`status`/`detail`/`code`/`request_id`) — `api.exception_handler` |
| 7 | Sayfalama | `page` + `page_size` (NX-2); sıralama whitelist view’da |
| 8 | Idempotency | Yazma `POST`’larda `Idempotency-Key` (actor-scoped storage); 409 conflict |
| 9 | Maske | Buyer’da tedarikçi kimlik/maliyet yok; supplier RFQ’da alıcı firma/şube yok |
| 10 | Throttle | buyer / supplier / ops / login scope’ları |
| 11 | OpenAPI drift + lint | CI: `export_openapi.py --check` + `lint_openapi.py` |
| 12 | Docs UI | `/api/docs/` + `/api/redoc/` (erişim politikası §üst) |
| 13 | Bilinen sınır | Aşağı §4; CORS erteli (aynı-origin) |

---

## 2. Yetki ve veri sızıntısı matrisi

Kanıt etiketi: **DOĞRULANDI** = dosya/test; aksi belirtilmez.

### 2.1 Yüzey × aktör (özet)

| Yüzey | Buyer | Supplier | Ops (`view_all` / QC / lojistik) | Finance ops |
|-------|-------|----------|----------------------------------|-------------|
| `/catalog`, `/quotes`, `/carts`, `/checkouts`, `/orders` (buyer yazma) | R/W (RBAC) | 403 | Ops okuma (order list QC/lojistik: `can_ops_read_orders`) | — |
| `/finance/*`, `/credit/*`, `/payments` | R/W maskeli | 403 | `/ops/finance/*` | Platform finance |
| `/shipments` (buyer) | R | 403 | Yazma: `/ops/shipments/*` | — |
| `/returns` | R/W | 403 | `manage_return` | — |
| `/org`, `/approvals`, `/rfqs` (buyer) | R/W `manage_*` | 403 buyer RFQ | Ops `view_all` / `manage_rfq` | — |
| `/ops/inspections/*` | 403 | 403 | `view_qc` / `manage_qc` | — |
| `/ops/shipments/*` | 403 | 403 | `manage_shipment` | — |
| `/supplier/offers|stock|rfqs` | 403 | R + yaşam döngüsü/stok/RFQ yazma (teklif **create HTTP yok**) | `view_all` kapıdan geçer; teklif/stok kendi firma filtresi | — |

### 2.2 Kör havuz kuralları

| Kural | Kanıt |
|-------|--------|
| Buyer DTO’da `tedarikci_id` / maliyet / supplier ad yok | `api/masking.py` `FORBIDDEN_KEYS`; B2/B4 `assert_masked` |
| Supplier RFQ’da `alici_firma_id` / `sube_id` yok | `api/presenters/supplier.py` `present_rfq_supplier`; `test_api_b6_supplier` |
| Çapraz tenant → 404 (varlık sızdırılmaz) tercih | B4 org/RFQ; B6 draft RFQ 404; F8-007 |
| Client `firma_id` yok sayılır | Order/list ve ops view’larda ignore; B1/B2 desen |

### 2.3 Rol notları

- **Buyer:** `ALICI_*` + `manage_rfq` / `lock_quote` / onay perm’leri.
- **Supplier:** `TEDARIKCI_*` + `manage_own_teklif` / `manage_own_warehouse`; RFQ mesajı `rfq_servisi._supplier_may_participate` (GONDERILDI).
- **Ops QC/Log:** `manage_qc` / `manage_shipment` / `view_qc` — `view_all` zorunlu değil (B5).
- **Finance:** `/ops/finance/*` platform finance; buyer `/finance/me` maskeli cari.

### 2.4 `allowed_actions`

Presenter’lar durum + yetkiye göre aksiyon listesi döner (RFQ, QC, shipment, teklif). UI keşif içindir; sunucu her yazmada servis + RBAC yeniden doğrular. **DOĞRULANDI:** B4/B5/B6 testleri `allowed_actions` içerir.

---

## 3. Endpoint grupları (B1–B6)

Tam liste: OpenAPI `paths` (**98** path, çift `/api/v1` önek **0** — `export_openapi.py --check`, 2026-11-11).

| Dilim | Örnek path’ler |
|-------|----------------|
| B1 | `/health`, `/auth/*`, `/me`, schema |
| B2 | `/catalog`, `/quotes`, `/price-locks`, `/carts`, `/checkouts`, `/orders` |
| B3 | `/finance/*`, `/credit/*`, `/payments`, `/shipments`, `/returns` |
| B4 | `/org/*`, `/approvals/*`, `/rfqs/*` |
| B5 | `/ops/inspections/*`, `/ops/shipments/*` |
| B6 | `/supplier/offers/*`, `/supplier/stock/*`, `/supplier/rfqs/*` |

---

## 4. Bilinen sınırlamalar (v1)

1. **CORS erteli** — aynı-origin reverse proxy (ADR-0017).
2. **RFQ eşleştirme HTTP yok** — servis F10-021 var; supplier B6 ters kör havuz (bilinçli). Platform eşleştirme REST: [API_READINESS](API_READINESS.md).
3. **Teklif create HTTP yok** — yalnız yaşam döngüsü (`submit` / `deactivate` / `versions`); create admin/servis dışı.
4. **Mahsup HTTP** — **UYGULANDI** (ADR-0023): `POST /api/v1/returns/{id}/mahsup/` + approve `mahsup`; ödeme iadesi yok (U-004).
5. **Rapor/anomali HTTP** — **UYGULANDI** (ADR-0026): `GET /reports/orders/`, `/reports/buyer-behavior/`, `/ops/anomalies/ciro/`.
6. **OpenAPI** — OpenAPI 3.1 hedef; path keşfi DRF AutoSchema; response DTO `openapi_components.py` (path sayısı: `openapi-v1.json`; docs_sync AUTO); request DTO `openapi_requests.py` (tüm POST/PUT/PATCH). Runtime presenter + test esas.
7. **NX-1…12** madde **Kabul**; ADR-0017 bütünü **Taslak**.
8. **`frontend/`** — NX-FE iskelet; API kapısı **FRONTEND READY** ([API_READINESS](API_READINESS.md)); Next ürün dilimleri ayrı talimat.
9. **Django HTML ürün portalı yok** (ADR-0029 **Kabul**): `/buyer|/supplier|/ops` kaldırıldı; karşılık `/api/v1/` (+ `/me/dashboard/`, act-as, invite). Admin + OpenAPI docs UI korunur. **Deprecated:** eski F9 HTML miras iddiası.
10. **Idempotency bilinçli hariç:** `auth/login|logout`, `payments/webhook`.
11. **TS client üretimi** — **UYGULANDI** (`frontend/lib/api/schema.d.ts`, `npm run generate:api`); tek kaynak OpenAPI.

---

## 5. Odaklı test kanıtı (API readiness)

| Dilim | Modül | Odaklı OK |
|-------|--------|-----------|
| B1 | `api.tests` (çekirdek) | 28 |
| B2 | `test_api_b2_*` | 11 + concurrency 7 |
| B3 | `test_api_b3_*` | 10 |
| B4 | `test_api_b4_enterprise` | 11 |
| B5 | `test_api_b5_ops` | 7 |
| B6 | `test_api_b6_supplier` | 3 |
| B7 | `test_api_b7_openapi` | OpenAPI freeze smoke |
| NX-3…12 smoke | `test_api_nx_contract` | **4 OK** (madde **Kabul**) |

---

## 6. Frontend-ready kapısı

Tek kaynak: **[API_READINESS](API_READINESS.md)**.  
Canlı karar (2026-11-10): **FRONTEND READY** (ürün sahibi override; FE-SUITE tam yeşil kanıtı MASTER §2.7’de izlenir).
