# BACKEND API READINESS

**Tarih:** 2026-11-10  
**Karar:** **FRONTEND NOT READY**  
**Bağlam:** API-B1…B7 **Kabul** · ADR-0019 **Kabul** (OL-7/8 HTTP kapalı) · ADR-0017 **Taslak**  
**Normatif teknik sözleşme:** [API_CONTRACT](API_CONTRACT.md) · [openapi-v1.json](api/openapi-v1.json)  
**Kanıt ilkesi:** kod + test; doküman “UYGULANDI” tek başına yeterli değil.

> Next.js ürün geliştirmesi bu kapı **FRONTEND READY** olmadan ve ürün sahibi onayı olmadan başlamaz.

---

## 1. Karar özeti

| Kapı şartı | Durum |
|------------|--------|
| Hedef ürün akışlarının API karşılığı | **KISMİ** — çekirdek commerce/finans/ops/supplier HTTP var; §4 P1/P2 imza veya kod bekliyor |
| API sözleşmeleri (response) | **TAMAM** — 81 path / 89 op; 2xx `$ref` DTO; Problem+JSON; `lint_openapi` weak=0 |
| API sözleşmeleri (request) | **TAMAM** — tüm POST/PUT/PATCH `requestBody` `$ref` (`openapi_requests.py`; A payload + B Empty/Reason) |
| Yetki + tenant test | **KISMİ TAMAM** — B1–B6 + F8-007 + ADR-0019 odaklı |
| OpenAPI + docs UI | **TAMAM** — `/api/schema|docs|redoc`; export+lint CI |
| TS client üretimi | **Erteli** — FE öncesi `openapi-typescript` (çakışma önleme) |
| Backend test paketi | Odaklı yeşil; **tam suite onaysız READY sayılmaz** |
| FE geliştirme borcu | **Kısmi** — §4 imza/kod; TS client; örnek payload metinleri |

### Verdict

# FRONTEND NOT READY

Gerekçe (2026-11-10 güncel): (1) §4 P1/P2 ürün yüzeyi imzasız; (2) TS client erteli; (3) tam suite onaysız yeşil kanıt yok; (4) ADR-0019 kapalı HTTP + NOTE-PENDING ayrı tur.  
**Değil:** “~70+ path response stub” — bu ifade **eski**; response DTO’lar bağlı, request body’ler bu dilimde kapatıldı.

---

## 2. API hazır olma matrisi

| Domain | Servis | API | DTO | Permission | Tenant | OpenAPI | Tests |
|--------|--------|-----|-----|------------|--------|---------|-------|
| Auth / me | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Firmalar / org / onay | TAMAM | KISMİ¹ | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM (B4) |
| Ürün / katalog (buyer) | TAMAM | TAMAM | TAMAM | TAMAM | UYGULANAMAZ² | TAMAM | TAMAM |
| Fiyatlama quote/lock | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Sepet / checkout / bulk | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Sipariş | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| RFQ (buyer/supplier) | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| RFQ eşleştirme (F10-021) | TAMAM | **EKSİK** | — | Servis | Servis | — | Servis |
| Tedarikçi teklif | TAMAM | KISMİ³ | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Stok / ATP | TAMAM | KISMİ⁴ | TAMAM | TAMAM | TAMAM | TAMAM | Servis+B6 |
| Kalite / inspection | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| İade / return | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Lojistik / shipment | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Finans / credit / payment | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM | TAMAM |
| Mahsup | TAMAM | **KAPALI** OL-8 | — | — | — | — | Servis |
| Rapor / anomali | TAMAM | **KAPALI** OL-7 | — | Servis | Servis | — | Servis |
| Bildirim (outbox) | TAMAM | UYGULANAMAZ⁵ | — | — | — | — | TAMAM |
| Belgeler | TAMAM | **EKSİK** | — | Servis | Servis | — | Servis |
| Tanımlar / kur | TAMAM | UYGULANAMAZ⁶ | — | Admin/cmd | — | — | Servis |
| Contract release | TAMAM | **EKSİK** | — | Servis | Servis | — | Servis |
| Harcama limiti CRUD | TAMAM | **EKSİK** | — | Servis | Servis | — | Servis |

¹ Org update/deactivate / üye silme HTTP yok (B4 bilinçli).  
² Katalog platform vitrin.  
³ Teklif create HTTP yok.  
⁴ Supplier stock API var; alıcı ATP HTTP kör → UYGULANAMAZ.  
⁵ Outbox cmd/worker.  
⁶ Kur sync admin/cmd; alıcı fiyat quote üzerinden.

---

## 3. KAPALI / KARAR GEREKİYOR (ADR — kendiliğinden açılmaz)

| Konu | Kaynak |
|------|--------|
| Rapor / anomali HTTP | ADR-0019 OL-7 |
| Mahsup HTTP | ADR-0019 OL-8 |
| Ops order iptal HTTP | ADR-0019 OL-2 |
| FXQ / DYN / I18N / AI | [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) |
| CORS cross-origin | ADR-0017 erteli |
| Dynamic pricing | U-015 kilitli |

---

## 4. FE v1 kapsam — imza bekleyen (P1/P2)

> Ürün sahibi her satırı **FE v1 dahil** veya **FE v1 dışı** diye imzalar. İmzasız → READY yok.

| ID | Konu | Öncelik | Öneri | İmza |
|----|------|---------|-------|------|
| FE-P1-RFQ | RFQ eşleştirme HTTP (F10-021 platform) | P1 | FE v1 **dışı** (platform HTML/admin; ayrı dilim) | ☐ |
| FE-P1-DOC | Belge / taş sertifika okuma HTTP | P1 | FE v1 **dışı** (admin/servis yeter) | ☐ |
| FE-P2-LIM | Harcama limiti CRUD HTTP | P2 | FE v1 **dışı** (B4 bilinçli) | ☐ |
| FE-P2-REL | Contract release HTTP | P2 | FE v1 **dışı** (servis+sipariş tüketimi yeter) | ☐ |
| FE-P2-ORG | Org update/deactivate + üye silme HTTP | P2 | FE v1 **dışı** (B4 bilinçli) | ☐ |
| FE-TS | openapi-typescript client pipeline | P0 docs | FE başlangıcında zorunlu | ☐ |
| FE-SUITE | Tam test suite yeşil kanıt | P0 | READY öncesi onaylı koşu | ☐ |

---

## 5. OpenAPI request kapanışı (bu dilim)

| Grup | Sayı | Yöntem |
|------|------|--------|
| A — gerçek payload | ~26 | View `request.data` → `openapi_requests.py` |
| B — action | ~21 | `EmptyRequest` / `ReasonRequest` / `TakipNoRequest` / `ReorderRequest` |
| Lint | 89 write op | `POST/PUT/PATCH` → `requestBody.$ref` zorunlu |

Webhook: `PaymentWebhookRequest` — `{event_id, event_type, provider?, payload?, intent_id?}`; header `X-Payment-Webhook-Secret`.

Kanıt: `python scripts/lint_openapi.py` → weak=0; requestBody eksik=0.

---

## 6. Docs UI

| URL | Not |
|-----|-----|
| `/api/schema/` | Enrich JSON |
| `/api/docs/` | Swagger |
| `/api/redoc/` | ReDoc |

Erişim: `DEBUG` / `API_DOCS_PUBLIC` / staff|platform. Try it out RBAC atlamaz.

---

## 7. FRONTEND READY checklist

1. §4 satırlarını imzala (veya kodla).  
2. TS client pipeline.  
3. Onaylı tam suite yeşil.  
4. Bu belgede **FRONTEND READY** + Next talimatı (ürün sahibi).

**Önerilen sıra (ürün sahibi):** request (bitti) → §4 imza → suite → READY. Mahsup/rapor/NOTE-PENDING ayrı tur.
