# Kuyumbank API sözleşmesi (insan özeti)

**Rol:** Frontend / entegrasyon için kısa rehber.  
**Normatif teknik sözleşme:** [`docs/api/openapi-v1.json`](api/openapi-v1.json)  
**Politika:** [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md) (Taslak; NX-1/NX-2 madde Kabul)  
**Durum:** API-B7 dondurma dilimi — OpenAPI ile çelişen ikinci sözleşme değildir; şüphede OpenAPI + kod kazanır.

Üretim / doğrulama:

```text
python scripts/export_openapi.py
python scripts/export_openapi.py --check
```

---

## 1. Frontend-ready checklist

| # | Konu | Beklenti |
|---|------|----------|
| 1 | Auth (tarayıcı) | Session cookie; `GET /api/v1/auth/csrf/` → login; CSRF header; Token tarayıcıda yok (NX-1) |
| 2 | Auth (S2S) | `TokenAuthentication` / Basic; ayrı istemci |
| 3 | Tenant | `firma_id` / `tedarikci_id` / `alici_id` client’tan **güvenilmez**; sunucu `request.user.firma` |
| 4 | Keşif | `GET /api/v1/me/` → `firma` + `capabilities` (UI bayrak; her uç yine RBAC) |
| 5 | Sözleşme | Path/method/status → OpenAPI; alan uydurma yok |
| 6 | Hata | `problem+json` (`type`/`title`/`status`/`detail`) — `api.exception_handler` |
| 7 | Sayfalama | `page` + `page_size` (NX-2); sıralama whitelist view’da |
| 8 | Idempotency | Yazma `POST`’larda `Idempotency-Key` (actor-scoped storage); 409 conflict |
| 9 | Maske | Buyer’da tedarikçi kimlik/maliyet yok; supplier RFQ’da alıcı firma/şube yok |
| 10 | Throttle | buyer / supplier / ops / login scope’ları |
| 11 | OpenAPI drift | CI/yerel: `export_openapi.py --check` |
| 12 | Bilinen sınır | Aşağı §4; CORS erteli (aynı-origin) |

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

Tam liste: OpenAPI `paths` (**81** path, çift `/api/v1` önek **0** — `export_openapi.py --check`, 2026-11-09).

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
2. **RFQ eşleştirme yok** — supplier tüm `GONDERILDI` havuzunu görür (ters kör; B6 bilinçli v1).
3. **Teklif create HTTP yok** — yalnız yaşam döngüsü (`submit` / `deactivate` / `versions`); create admin/servis dışı.
4. **Mahsup HTTP** — servis var; B3 HTTP yüzeyi iade SM odaklı (mahsup uç uydurulmaz).
5. **OpenAPI alan şemaları** — DRF AutoSchema; bazı body alanları generic olabilir → runtime presenter + test esas.
6. **NX-3…12** ADR maddeleri açık (uygulama kısmen var; ADR bütünü Taslak).
7. **`frontend/`** henüz yok — Next.js iskeleti B7 sonrası ayrı dilim.
8. **F9 Django HTML WIP** commit dışı; API yüzeyi bundan bağımsız.

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
