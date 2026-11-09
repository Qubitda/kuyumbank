# Hedef mimari, capability gap ve yol haritası

> Planlama dokümanıdır; **kod durumu için [MASTER](MASTER.md) kazanır.** Faz kodu = ilgili ADR **Kabul** + açık talimat.
> Prosperer / SAP B2B sütunları hedef kıyastır (**DOĞRULANAMADI** — harici runtime yok).

## 1. Hedef mimari ve capability gap

### 8.1 Hedef mimari katmanlar (modular monolith — erken mikroservis yok)

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Experience & API     admin (şimdi) · PRE/DRF · portallar │
├─────────────────────────────────────────────────────────────┤
│ 2. B2B Capabilities     reorder · bulk · approval · EDI ·   │
│                         credit view · compare · alerts      │
├─────────────────────────────────────────────────────────────┤
│ 3. Core Domains         firmalar · urunler · fiyatlama ·    │
│                         stok · (siparis) · (finans) · QC     │
├─────────────────────────────────────────────────────────────┤
│ 4. Shared Infrastructure audit · outbox · idempotency ·     │
│                         RBAC/tenant selectors · kur         │
├─────────────────────────────────────────────────────────────┤
│ 5. Data & Runtime       PostgreSQL · Django 6.1 · (Celery   │
│                         F8+) · env secrets                  │
└─────────────────────────────────────────────────────────────┘
```

- Capability’ler **yeni Django app yağmuru** değil; mevcut/planlı domain app’lere servis olarak iner.
- Tenant sınırı: **`Firma`** (ADR-0003). Şube, tenant’ı bölmez — üyelik/scope genişlemesi **U-014** sonrası.
- F4 Order tasarım rezervi: `Order.alici_firma` zorunlu tenant; ileride `sube` / org birimi **nullable** FK (yokken null) — şube tablosu F10’da gelir; F4’te zorunlu şube yok.

### 8.2 Mimari çakışmalar (özet)

| Konu | Mevcut (DOĞRULANDI) | Risk | Çözüm yönü |
|------|---------------------|------|------------|
| Account Hierarchy | `Kullanici.firma` tek FK + tek `rol` | Şube üyeliği ADR-0003’ü kırabilir | **U-014**; F10-001; F4’te yalnız nullable rezerv alan |
| Approval | Ürün/teklif SM var; genel motor yok | Order/limit/org yokken erken motor | F10-012/013; Order + org sonrası |
| Quick/Bulk Reorder | Quick Reorder UYGULANDI; bulk yok | — | F4-081 (+ PRE-005) |
| Bulk idempotency | PRE-005 iskelet plan | Çift sipariş | Idempotency-Key + satır hash; PG unique |
| Outbox | Yok; audit durable ayrı bağlantı | Aynı atomic’te mail = kayıp | F4-090: domain tx içinde outbox satırı; worker sonra |
| Celery/Redis | requirements’ta yok | Erken altyapı maliyeti | F4-022/F4-090 management command veya sync; **Celery ≥ F8** |
| Contract Release | `ContractReleasePlan/Event` (F5-041) | Tüketim siparişe bağlanmadı | Release ≠ quote; consume iskelet |
| Dynamic Pricing | Quote/Lock immutable | Canlı fiyat geçmişi bozar | Lock sonrası yeniden fiyat yok; U-015 |
| Credit Visibility | Cari yok | Sahte limit | F5-010/011 + U-005 sonra F5-040 |
| EDI | API yok | Punchout kör havuz ihlali | F7 + tenant maske; F7-024 |

### 8.3 Prosperer / klasik gap tablosu

| # | Yetenek | Mevcut | Hedef | Eksik BE | Eksik FE | Güvenlik | Öncelik | Bağımlılık | Kabul |
|---|---------|--------|-------|----------|----------|----------|---------|------------|-------|
| 1 | B2B katalog | KISMİ | Zengin katalog+arama | Search, import | Buyer browse | Tenant; olusturan gizli | P1 | Faz2 | Alıcı yalnız yayınlı |
| 2 | Firma/şube org | KISMİ (tek firma) | Şube/hiyerarşi | Org model | Org UI | Org scope ≠ tenant split | **P1 stratejik** | U-014, F10 | İzolasyon |
| 3 | Fiyat listesi/koşul | KISMİ→güçlü | Sözleşme+liste UI | Liste API | Finans UI | Maske | P0 koru | ADR-0008 | Quote fail-closed |
| 4 | Teklif/RFQ | KISMİ | RFQ+müzakere | RFQ SM | Buyer/sup UI | Kör | P1 | Teklif | Audit SM |
| 5 | Sepet/checkout | UYGULANDI (servis; HTTP yazma yok) | Cart+checkout | Cart svc | Buyer sepet | IDOR | P0 | Lock, rezerv | Lock olmadan sipariş yok |
| 6 | Sipariş | Order+snapshot+iptal UYGULANDI | SM genişleme / API | Order | Ops/buyer | Kör+audit | P0 | Cart | Fiyat değişmez |
| 7 | Çok depo/stok | UYGULANDI (WH+ledger; dual yazma F4-070 kapalı) | Ledger+WH | F4-070b kolon drop opsiyonel | Ops | Tedarikçi scope | P0 | F4 ADR | Count edit yok |
| 8 | Rezervasyon/ATP | KISMİ (F4-020/021) | TTL+ATP + expire | F4-022 | Ops | Oversell yok | P0 | Ledger | PG concurrent |
| 9 | Ödeme/cari/kredi | Yok | Payment+cari+credit UI | F5-* | Buyer/finans | Audit | P0 | Order, U-005 | State tutarlı |
| 10 | Sevkiyat | Yok | Shipment+carrier | lojistik | Takip | Adres tenant | P1 | QC | QC fail blok |
| 11 | İade/SH | Yok | RMA | after-sales | Buyer | U-004 | P1 | Ship | SM+ledger |
| 12 | Portallar | Yok (admin) | Buyer/sup portal | API | Next/PWA | Aynı RBAC | P1 | API | Admin’siz akış |
| 13 | Onay workflow | KISMİ | Limit+zincir | F10-013 | Kuyruk | Escalation | P1 (org sonrası) | Order, org | Limit blok |
| 14 | Raporlama/analitik | Yok | Raporlar + davranış | F11 | Dashboard | Rol kesit | P2 | Order data | Sızıntı yok |
| 15 | Entegrasyon/EDI | Yok | ERP/ödeme/kargo/EDI | F7-021/024 | Mapping | Secret+kör | P1 | API | Fail-closed |
| 16 | API/headless | KISMİ (ince PRE; yalnız GET) | /api/v1 + PWA | DRF | Client | Object perm | P0 PRE | ADR-0002 | Tenant test |
| 17 | i18n/FX | KISMİ | Locale+PB | i18n | Dil | — | P3 | U-009 | PB karışmaz |
| 18 | Bildirim/outbox | Yok | Outbox+S3 | F4-090 | Inbox | Belge tenant | P1 | Events | Audit |
| 19 | Güvenlik/audit | KISMİ→güçlü | API+ops sert | AUD-001 | — | P0 sürekli | — | Isolation yeşil |
| 20 | Quick/Bulk reorder | KISMİ (Quick Reorder UYGULANDI; bulk yok) | Tekrar + CSV | F4-080/081 | Buyer | Idempotency | P1 | Order | Çift sipariş yok |
| 21 | Dynamic pricing | Yok (snapshot kuralı var) | Koşullu fiyat | U-015 | — | Lock bütünlüğü | P2 | Pricing | Snapshot bozulmaz |

**En kritik gap sırası (güncel):** F4-022 rezervasyon expire (doğruluk) → PRE-005 Idempotency → Bulk (F4-081) → Outbox → Finance → EDI → Org. (Cart…Reorder + PRE-001…004 UYGULANDI.)

---

## 2. Ürün domainleri ve işleyiş

| Domain | Sorumluluk | Veri (şimdi/hedef) | Durum | Eksik | Bağımlılık |
|--------|------------|-------------------|-------|-------|------------|
| Identity & RBAC | Firma, kullanıcı, rol, audit | `firmalar` | UYGULANDI | Org/şube | — |
| Product Catalog | Ürün, varyant, onay, medya | `urunler` | KISMİ | Search API, zengin medya UI | Identity |
| Supplier Mgmt | Teklif SM, eşleşme | `TedarikciTeklif` | UYGULANDI | Portal UI | Catalog |
| Pricing Engine | Sözleşme, kur, hesap, quote | `fiyatlama`+`tanimlar` | UYGULANDI | B-01, vergi | Supplier |
| PriceLock | Kilit TTL; sipariş bağ | `PriceLock` + `OrderLine.price_lock` | UYGULANDI (L-11) | — | Pricing |
| RFQ & Quotation | RFQ müzakere | — | PLANLANDI | Tümü | Pricing |
| Cart & Checkout | Sepet, checkout | Cart + CheckoutAttempt | UYGULANDI | — | Lock, Inventory |
| Order Mgmt | SM, snapshot | Order + OrderLine + iptal + reorder | UYGULANDI (SM dar) | F4-081 bulk | Cart |
| Inventory & WH | WH + ledger + rezervasyon | `stok` (+ dual kolon, yazma kapalı) | UYGULANDI (F4.1–4.3 + F4-070) | F4-070b drop opsiyonel | Supplier |
| Payments & Finance | Ödeme, cari | — | PLANLANDI | U-* | Order |
| Quality | QC, gram | ADR-0013 **Kabul**; F6-010 UYGULANDI | KISMİ | Tümü | Order |
| Shipping | Sevkiyat, carrier | ADR-0013 **Kabul** | PLANLANDI | Tümü | QC |
| Returns | İade, uyuşmazlık | — | PLANLANDI | U-004 | Ship, Finance |
| Customer & Org | Şube, limit | — | PLANLANDI | Faz 10 + **U-014** (ADR-0003) | Identity |
| Notification | Outbox | `OutboxMessage` + process command | UYGULANDI (iskelet) | F7-020 webhook | Events |
| Documents | Sertifika, POD | — | PLANLANDI | S3 | |
| Workflow | Onay zinciri | kısmi (ürün/teklif SM) | KISMİ | Genel motor → F10-013 | Order, Org |
| Audit | AuditOlay | var | KISMİ | API yüzeyi; AUD-001 | Tümü |
| Reporting | Rapor | — | PLANLANDI | | Order+ |
| Integration Hub | Adapter / EDI | — | PLANLANDI | F7 | API |
| Search | Katalog arama | — | PLANLANDI | | Catalog |

## 3. B2B capability alanları (hedef — kod durumu ayrı)

| Capability | İş değeri (Kuyumbank) | Kod durumu | Hedef domain | Önerilen faz |
|------------|----------------------|------------|--------------|--------------|
| Account Hierarchy | Kurumsal alıcı şube/yetki; tenant’ı yeniden yazmamak | PLANLANDI | Identity / Org | **F10** (+ U-014); F4’te yalnız geriye uyumlu rezerv |
| Quick Reorder | Tekrar sipariş hızı | UYGULANDI (svc) | Order | F4-081 bulk / API |
| Bulk Order / CSV | Toplu alım operasyonu | UYGULANDI | Order / Cart | F4-081 |
| Approval Workflow | Limit üstü onay | KISMİ (katalog/teklif SM) | Workflow + Org | F10 (F10-012/013) |
| Contract Release Plan | Sözleşmeli miktar serbest bırakma | UYGULANDI (iskelet; tüketim yok) | Pricing + Order | F5-041; FiyatSozlesmesi üzerine |
| Credit Visibility | Vadeli satış limiti görünürlüğü | PLANLANDI | Finance | F5 (F5-040); U-005 |
| Notification Outbox | Güvenilir olay/bildirim | UYGULANDI (iskelet) | Shared infra | F4-090; Celery F8 |
| Live Gold Price Alert | Kur fırsat bildirimi | PLANLANDI | Pricing / Notify | F9+ (CAP-ALERT); F4 bloklamaz |
| Multi-Variant Comparison | Alıcı karar desteği | PLANLANDI | Catalog / Portal | F9 (CAP-COMPARE) |
| Dynamic Pricing | Koşullu fiyat | PLANLANDI | Pricing | U-015 + F9; **snapshot bozulmaz** |
| EDI / Punchout | Kurumsal ERP alış | PLANLANDI | Integration | F7 (F7-024) |
| Smart Replenishment | Stok yenileme önerisi | PLANLANDI | Analytics / Inventory | F11 (F11-020) |
| Buyer Behavior Analytics | Alıcı davranış içgörüsü | PLANLANDI | Analytics | F11 (F11-021) |

> Sektör/SAP “var” iddiaları **DOĞRULANAMADI** (harici ürün runtime yok). Öncelik Kuyumbank bağımlılık + müşteri değerine göre.

## 4. Ana geliştirme yol haritası

**Kural:** Faz kodu = ilgili ADR **Kabul** + açık talimat. Bu bölüm planlamadır.

### Gate (Faz 4 öncesi)
G0 3.7 commit **kapandı** (`2979e25`) · G1 ADR-0010 Kabul · G2 ADR-0011 Kabul · G3 U-002 (+ U-008 kapsam dışı teyit) · G4 U-012 ince PRE-API.

### PRE — İnce API iskeleti
Amaç: DRF pin, `/api/v1/health`, auth, tenant 404, OpenAPI, Idempotency.  
Kapsam dışı: Tam Prosperer API.  
**UYGULANDI:** PRE-001…004 (`api` app).  
**Backlog:** PRE-005 Idempotency-Key.

### Faz 4 — Ticari işlem çekirdeği
Amaç: Ledger → rezervasyon → cart → checkout/lock → order+snapshot.  
Kapsam dışı: Ödeme, QC, kargo, RFQ, B-01/B-06, Account Hierarchy uygulaması, Dynamic Pricing.  
Önkoşul: G0–G2.  
Alt: F4-001…070 (+ F4-080/081 Order sonrası; F4-090 outbox iskelet).  
Kabul: Oversell yok; expired lock checkout fail; sipariş fiyatı kurdan etkilenmez.  
Durum: **KISMİ** — dilim 1–8 + **PRE-001…004** UYGULANDI; **devam eden F4-022**, sıradaki PRE-005 / F4-081.  
**Org rezervi:** Order tenant = `alici_firma`; nullable şube FK U-014/F10 — F4’ü bloklamaz.

### Faz 4.5 — Outbox / bildirim iskeleti (Order sonrası)
Amaç: Transactional outbox (F4-090); sync veya management command.  
Kapsam dışı: Tam Celery/Redis prod (F8).  
Durum: PLANLANDI.

### Faz 5 — Finans
Amaç: Ledger, cari, payment intent, credit visibility, contract release (F5-040/041).  
Gate: U-003…U-007, U-005.  
Durum: **KISMİ UYGULANDI** (F5-010…032, 040, 041); F5-022 Blocked (U-006 vade); F5-023 Blocked (U-004).

### Faz 6 — QC & lojistik
QC gram, shipment, POD, return. QC fail → ship blok.  
Gate: **ADR-0013 Kabul** (2026-11-09). F6-010 UYGULANDI → sırada F6-011 / F6-020.

### Faz 7 — API & entegrasyon
Buyer/Supplier/Admin API olgunluk, rate limit, webhook outbox, ERP, **EDI/Punchout (F7-024)**. PRE’yi büyütür.

### Faz 8 — Prod readiness
CI, log, Sentry, backup, secret, perf, güvenlik; **Celery/Redis** burada (veya gerekçeli erken).

### Faz 9 — Portal bütünleşme
Deneyim kalitesi; variant compare (CAP-COMPARE); gold alert (CAP-ALERT) — F4 bloklamaz.

### Faz 10 — Kurumsal & RFQ
**Account Hierarchy (U-014 + F10-001/010)** → limit → **Approval Workflow** → RFQ / özel üretim.  
Öncelik stratejik yüksek; **uygulama F4’ten sonra ve ADR kararıyla**.

### Faz 11 — Analitik
Rapor, fiyat/stok, buyer behavior (F11-021), smart replenishment (F11-020), bildirim otomasyonu.

### Faz 12 — i18n & ekosistem
Dil, PB yuvarlama U-009, ülke kuralları, partner API.

### Stratejik ürün önceliği (ürün sahibi 2026-11-08)

1. Sipariş ticari çekirdeği (F4 cart→checkout→order)  
2. Şube/org için **geriye dönük uyumlu tasarım** (U-014; kod F10)  
3. Quick Reorder + Bulk Order (F4-080/081)  
4. Onay + bildirim altyapısı (F10-013; F4-090)  
5. Finans, entegrasyon, analitik  

**Bağımlılık özeti:** `ledger+reservation → cart → checkout/lock → order → (outbox) → reorder/bulk → finance/credit → QC/ship → API/EDI → ops → portal → org/approval → analytics → i18n`.
