# SESSION HANDOFF — Kuyumbank API readiness

**Tarih:** 2026-11-09  
**Amaç:** Yeni sohbet oturumu için tek başlangıç referansı. Geçmiş chat gerekmez.  
**Dal:** `adim-1-ilerleme`  
**Bu belge:** oturum kapanışı senkronu. **API-B4 burada başlatılmaz.**

---

## 1. Proje amacı ve mimari

**Kuyumbank** — Jewelry B2B platform. Django **6.1.2** modular monolith (`backend/config/`), PostgreSQL, DRF `/api/v1/`.

- Alıcı–tedarikçi **kör havuz**; fiyat **snapshot/PriceLock**; stok **ledger + rezervasyon**; sipariş Cart→Checkout→Order.
- Tenant = firma; client `firma_id` güvenilmez.
- Domain logic **servislerde**; view ince.
- Ürün UI hedefi: **Next.js App Router** (`frontend/` yalnız **B7 sonrası**).
- Mevcut Django HTML `/buyer/` ve `/ops/` **korunur**; **yeni Django HTML yok**.

Normatif: `AGENTS.md` → `docs/MASTER.md` §2 + §12 → ilgili ADR.

---

## 2. Kesinleşmiş kullanıcı kararları

| Karar | Durum |
|-------|--------|
| Next.js birincil UI; ADR-0016 Supersede | Sabit |
| ADR-0017 bütünü | **Taslak** (agent Kabul etmez) |
| NX-1 Session+CSRF (HttpOnly, SameSite=Lax, prod Secure) | **Kabul** |
| NX-2 `page`+`page_size`, max 100, ikincil `-pk` | **Kabul** |
| CORS | **Ertelendi** (aynı-origin) |
| NX-3…NX-12 | **Açık** — ürün sahibi onayı olmadan Kabul yok |
| Yeni Django HTML | Yok |
| Tam suite | Yalnız açık onay |
| Production migrate / secret commit | Yasak (onaysız) |
| Buyer iade oluşturma | Yok (`manage_return`) — bilinçli |

---

## 3. B0–B7 faz durumu (ürün sahibi kesin tablo)

| Faz | Durum |
|-----|--------|
| **B0** | Tamamlandı |
| **B1** | Kullanıcı tarafından **Kabul** |
| **B2** | Kullanıcı tarafından **Kabul** |
| **B2 concurrency** | PG TransactionTestCase **7 OK** — doğrulandı / Kabul |
| **B3** | Kullanıcı tarafından **Kabul** |
| **B4** | Sıradaki faz — **henüz başlatılmadı** |
| **B5** | Bekliyor |
| **B6** | Bekliyor |
| **B7** | Bekliyor |

> **Uyarı:** Önceki ajan turunda B4 HTTP WIP dosyaları yazılmış olabilir. Resmi faz **başlatılmadı**; WIP commit dışı bırakıldı. B4’e yalnızca ürün sahibi talimatıyla başla.

---

## 4. B1 / B2 / B3 teslimat özeti

### B1 — Kabul
Session login/csrf/logout · problem+json (`code`/`errors`/`request_id`) · 401 ayrımı · 429 Retry-After · `/me`+capabilities · no-store · Idempotency TTL · OpenAPI export+CI drift · CORS kaldırıldı.  
**Test:** `api.tests.test_api_b1_standards` (+ ilgili) **28 OK** odaklı.

### B2 — Kabul
Catalog · Quote · PriceLock · Cart · Checkout · Order from-checkout · Cancel · Reorder · Buyer presenters · maske · Decimal string · servis SM · yazmalarda Idempotency-Key.  
**Test:** `api.tests.test_api_b2_buyer_commerce` **11 OK** odaklı.

### B2 concurrency — Doğrulandı
`api.tests.test_api_b2_concurrency` — PG + `pg_advisory_lock` (firma+key).  
**7 OK:** aynı key/payload tek işlem; farklı body 409; checkout/from-checkout tek; cancel/reorder tek; quote/lock tek.

### B3 — Kabul
Buyer finance/cari/ledger · credit · payment intent · ops finance (+payments) · shipments+`allowed_actions` · returns list/detail + ops SM (submit/approve/reject/cancel) · tenant/RBAC · maske · idempotency.  
**Test:** `api.tests.test_api_b3_finance_ops` **10 OK** odaklı (+ sevkiyat/finans regresyonları önceki turda yeşil).

### TECH-OPENAPI-01 — UYGULANDI (bakım)
Çift `/api/v1/api/v1` önek düzeltildi: `api_urlpatterns` + `SchemaGenerator(url="/api/v1/")`. Canlı URL değişmedi. NX-4 hâlâ **Kabul değil**.

---

## 5. Test sonuçları

| Suit | Sonuç | Not |
|------|--------|-----|
| B1 odaklı | **28 OK** | Tam suite değil |
| B2 odaklı | **11 OK** | |
| B2 concurrency | **7 OK** | PostgreSQL zorunlu |
| B3 odaklı | **10 OK** | |
| Tam suite | **Çalıştırılmadı** (bu oturum) | Son kayıtlı: **555 OK** (2026-11-09, oturum öncesi) |
| SQLite concurrency | Kanıt sayılmaz | |

---

## 6. API endpoint envanteri (B1–B3, `/api/v1/`)

**Auth / keşif:** `auth/csrf|login|logout`, `me`, `health`, `schema`  
**Catalog:** `catalog/`, `catalog/<pk>/`  
**Pricing:** `quotes/`, `quotes/<pk>/`, `price-locks/`, `price-locks/<pk>/`  
**Cart / checkout / order:** `carts/me/`, `carts/me/lines/`, `carts/me/lines/<id>/`, `carts/<pk>/`, `checkouts/`, `bulk-orders/`, `orders/from-checkout/`, `orders/`, `orders/<pk>/`, `…/cancel/`, `…/reorder/`  
**Lojistik:** `shipments/`, `shipments/<pk>/`, `returns/` (+ submit/approve/reject/cancel)  
**Finans:** `credit/me|check`, `finance/me|cari|ledger`, `payments/intents/`, `payments/webhook/`  
**Ops:** `ops/finance/`, `…/cari|ledger|payments`, `ops/orders/summary/`  
**Supplier (mevcut):** `supplier/offers/`, `supplier/stock/`

OpenAPI: `docs/api/openapi-v1.json` · üret: `python scripts/export_openapi.py` · CI `--check`.

**B4 uçları (org/approvals/rfq) resmi envanterde yok.**

---

## 7. Domain servis durumu (özet)

| Alan | Servis | API |
|------|--------|-----|
| Quote/Lock | `fiyatlama.pricing_service` | B2 |
| Cart/Checkout/Order | `siparis.*` | B2 |
| Credit/Finance | `finans.credit_servisi`, `buyer_finans_servisi` | B3 |
| Payment | `finans.payment_servisi` | B3 intent |
| Ops finans | `ops_finans_servisi` | B3 |
| Shipment | `buyer_shipment_servisi` | B3 |
| Return | `return_servisi` (`manage_return`) | B3 HTTP |
| Org / Onay / RFQ | `org_servisi`, `onay_servisi`, `rfq_servisi` | **HTML var; REST = B4** |

Servisleri B4’te yeniden yazma; HTTP sarmala.

---

## 8. Açık teknik borçlar

| ID | Açıklama | Dosya/uç | Öncelik | Bağımlılık | Faz |
|----|----------|----------|---------|------------|-----|
| TECH-OPENAPI-01 | Çift önek — **düzeltildi**; NX-4 Kabul değil | `scripts/export_openapi.py`, `api/urls.py` | P2 | NX-4 | bakım / B7 |
| NX-3…12 | ADR maddeleri açık | ADR-0017 | P1 | ürün sahibi | ADR |
| ADR-0017 | Bütün **Taslak** | `docs/decisions/ADR-0017-*.md` | P1 | — | — |
| CORS | Erteli | — | — | ihtiyaç | ayrı karar |
| NX-7 | Rol serializer sınıfları eksik; presenter fn var | `api/presenters/` | P2 | NX-7 | B4+ |
| Idempotency kapsam | Tüm yazmaların matrisi ayrıca doğrulanmalı | `api/mixins.py` | P1 | NX-6 | B4–B6 |
| Buyer return create | Bilinçli yok | `return_servisi` | — | iş kuralı | genişletme yasak |
| Kova B F9 HTML | WIP uncommitted; silme/karıştırma yok | `templates/buyer/*`, `buyer_catalog_ui` | P2 | — | ayrı |
| Tam suite | Onaysız çalıştırılmadı | — | P1 | onay | handoff sonrası |
| B4 premature WIP | View/test dosyaları ağaçta kalabilir | `api/views/org|approvals|rfq.py` vb. | P1 | B4 talimatı | B4 |
| Match / supplier RFQ | Kod yok | F10-021/023 | P2 | — | B6+ |

---

## 9. ADR / NX

- **ADR-0016** Supersede → **0017**
- **ADR-0017 Taslak**; NX-1/NX-2 Kabul; CORS erteli; NX-3…12 açık
- Finans ADR-0012 Kabul; F10 ADR-0015 Kabul

---

## 10–11. Git / commit (DOĞRULANDI 2026-11-09)

| Alan | Değer |
|------|--------|
| Branch | `adim-1-ilerleme` |
| Commit | `b529e5ecc030590e169707e2757a67e5c8a93633` |
| Mesaj | `feat(api): B1–B3 kabul teslimatı, OpenAPI düzeltmesi ve oturum handoff` |
| Push | kapanış raporuna bak (origin) |

**Commit kapsamı:** B1–B3 API + testler + OpenAPI + ADR-0017 + docs + SESSION_HANDOFF.  
**Commit dışı (working tree’de kalır):** Kova B F9 HTML; B4 premature WIP (`org.py`/`approvals.py`/`rfq.py`/`enterprise.py`/`test_api_b4_enterprise.py`).

---

## 12. Sıradaki faz: API-B4

**Amaç:** Kurumsal HTTP — org birimi, onay akışı, RFQ (+revizyon/mesaj); `allowed_actions`; maske; idempotency.  
**Kaynak:** mevcut `org_servisi` / `onay_servisi` / `rfq_servisi` + selectors.  
**İcat etme:** org update/deactivate, üye silme, RFQ kapat/iptal fonksiyonu yoksa HTTP uydurma; firma CRUD / rol atama / limit HTTP / supplier RFQ yoksa raporla.

---

## 13. B4 kuralları (bağlayıcı)

- Yeni Django HTML yok; `/buyer/` `/ops/` dokunma (Kova B’ye karışma).
- `frontend/` yok; CORS yok; ADR-0017 Taslak; NX-3…12 Kabul etme.
- Servis yeniden yazma yok; yeni app yok (gerekçe+onay yoksa).
- Session+CSRF; Decimal string; tenant izolasyonu; kör havuz.
- Odaklı test; PG concurrency; tam suite / prod migrate / force push yok.
- B4 sonunda DUR — B5’e geçme.

---

## 14. Yeni oturum — B4 başlangıç promptu

Aşağıyı yeni sohbete yapıştır:

```text
Kuyumbank — docs/SESSION_HANDOFF.md oku. Branch adim-1-ilerleme.
Durum: B0 tamam; B1–B3 Kabul; B2 concurrency 7 OK; B4 henüz başlatılmadı.
ADR-0017 Taslak; NX-1/2 Kabul; NX-3…12 açık; CORS erteli.
Kurallar: yeni Django HTML yok; /buyer/ /ops/ koru; Kova B F9 HTML’e dokunma;
servis yeniden yazma yok; CORS yok; tam suite/prod migrate/commit yalnız açık onayla.

Görev: API-B4 Enterprise API (org / onay / RFQ).
Önce mevcut org_servisi, onay_servisi, rfq_servisi, selectors ve buyer HTML’i incele.
Eksik iş kuralını icat etme — raporla. Premature WIP dosyaları varsa incele; talimata göre entegre veya temizle.
Hedefli test + PG concurrency; OpenAPI güncelle; B4 sonunda DUR.
```

---

## Değişmez mimari (kısa)

Modular monolith · tenant izolasyonu · kör havuz · Session+CSRF · Token/Basic yalnız S2S · para/miktar JSON string · Quote/Lock/Order serviste · tam suite ve prod migrate onaysız yok.
