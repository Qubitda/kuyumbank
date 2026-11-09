# Hedef mimari, capability gap ve yol haritası

> Planlama dokümanıdır; **kod/canlı durum için [MASTER](MASTER.md) §2 + §12 kazanır.**  
> Faz kodu = ilgili ADR **Kabul** + açık talimat. Prosperer/SAP sütunları hedef kıyastır (**DOĞRULANAMADI**).  
> Canlı durum / B0–B7: [MASTER](MASTER.md) §12. (Bu dosyada sabit “son senkron” tarihi tutulmaz.)

## 1. Hedef mimari ve capability gap

### 1.1 Hedef mimari katmanlar (modular monolith — erken mikroservis yok)

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Experience & API     admin · /api/v1 · /buyer · /ops     │
│                         (birincil FE: Next.js; HTML miras)  │
├─────────────────────────────────────────────────────────────┤
│ 2. B2B Capabilities     reorder · bulk · approval · EDI ·   │
│                         credit view · (compare/alerts P2)   │
├─────────────────────────────────────────────────────────────┤
│ 3. Core Domains         firmalar · urunler · fiyatlama ·    │
│                         stok · siparis · finans · kalite ·  │
│                         lojistik · belgeler · api           │
├─────────────────────────────────────────────────────────────┤
│ 4. Shared Infrastructure audit · outbox · idempotency ·     │
│                         RBAC/tenant · kur · request_id log  │
├─────────────────────────────────────────────────────────────┤
│ 5. Data & Runtime       PostgreSQL · Django 6.1 · env       │
│                         secrets · (Celery hâlâ yok)         │
└─────────────────────────────────────────────────────────────┘
```

- Capability’ler **yeni Django app yağmuru** değil; domain app’lere servis olarak iner.
- Tenant sınırı: **`Firma`** (ADR-0003). Org/şube firma içi scope’tur (ADR-0015); tenant’ı bölmez.
- `Order`/`Cart.sube` nullable FK → `OrgBirimi` (**UYGULANDI**, F10-010).

### 1.2 Mimari çakışmalar (özet — çözülmüş / açık)

| Konu | Durum (MASTER) | Not |
|------|----------------|-----|
| Account Hierarchy | **UYGULANDI** (ADR-0015) | OrgBirimi + OrgUyeligi; tenant=Firma |
| Approval / limit | **UYGULANDI** (F10-012/013) + UI F10-014 | Zengin F9 portal ayrı |
| Quick/Bulk Reorder | **UYGULANDI** (F4-080/081) | — |
| Outbox | **UYGULANDI** iskelet (F4-090) | Celery yok; `process_outbox` |
| PRE-005 Idempotency | **UYGULANDI** | checkout POST |
| Credit Visibility | **UYGULANDI** iskelet (F5-040) | — |
| EDI/Punchout | **UYGULANDI** stub (F7-024) | Canlı ERP yok |
| Celery/Redis | **Yok** (bilinçli) | F8-003/006 açık; Celery hâlâ opsiyonel |
| Dynamic Pricing | **Kilitli** (U-015) | Snapshot bozulmaz |
| Contract Release tüketim | **KISMİ** | F5-041 iskelet; sipariş consume yok |

### 1.3 Prosperer / kritik gap tablosu (Mevcut = kod iddiası; MASTER doğrular)

| # | Yetenek | Mevcut | Hedef eksik (özet) | Öncelik |
|---|---------|--------|--------------------|---------|
| 1 | B2B katalog | KISMİ | Search API; F9-011 browse **WIP commit dışı** | P1 |
| 2 | Firma/şube org | **UYGULANDI** çekirdek | Zengin org UI | P2 |
| 3 | Fiyat listesi/koşul | UYGULANDI | Liste UI | P2 |
| 4 | Teklif/RFQ | **UYGULANDI** SM+buyer UI | Eşleştirme motoru; supplier UI | P1 |
| 5 | Sepet/checkout | **UYGULANDI** (+ HTTP POST) | F9-012 polish | P2 |
| 6 | Sipariş | **UYGULANDI** | SM genişleme | P2 |
| 7 | Stok/WH | **UYGULANDI** | Ops UI | P2 |
| 8 | Rezervasyon/ATP | **UYGULANDI** (F4-022 dahil) | — | — |
| 9 | Ödeme/cari/kredi | **KISMİ** iskelet | Gerçek provider; oran | P1 |
| 10 | Sevkiyat | **UYGULANDI** fake carrier | Canlı carrier | P2 |
| 11 | İade | **UYGULANDI** stok-only | Ödeme iadesi yok (U-004); F6-032 UI | P2 |
| 12 | Portallar | **KISMİ** `/buyer` F4-062 (+ F9-010 WIP) | F9-011…015 erteli; `/supplier` Next | **P1** |
| 13 | Onay workflow | **UYGULANDI** + minimal UI | Escalation zinciri | P2 |
| 14 | Raporlama | Yok | F11 | P2 |
| 15 | Entegrasyon/EDI | **KISMİ** stub | Canlı ERP/SAP | P2 |
| 16 | API/headless | **UYGULANDI** ince PRE (+POST) | Object-level DRF; Prosperer | P1 |
| 17 | i18n/FX | KISMİ | F12 / U-009 | P3 |
| 18 | Bildirim/outbox | **UYGULANDI** iskelet | Worker ölçek; S3 belge | P2 |
| 19 | Güvenlik/audit | **UYGULANDI** + F8-007 | Sentry SDK | P1 |
| 20 | Quick/Bulk | **UYGULANDI** | — | — |
| 21 | Dynamic pricing | Yok (kilitli) | U-015 açılmadan yok | — |

**Güncel gap sırası (MASTER §12.3 ile hizalı):** Next.js `frontend/` → F8-003/006 → F10-021 → CAP-PIYASA. (B0–B7 Kabul; F9 HTML büyütme yok; ADR-0017 Taslak.)

---

## 2. Ürün domainleri ve işleyiş

| Domain | Durum | Eksik (kısa) |
|--------|-------|--------------|
| Identity & RBAC | UYGULANDI | — |
| Product Catalog | KISMİ | Search; F9-011 WIP commit dışı |
| Supplier Mgmt | UYGULANDI | Supplier portal |
| Pricing Engine | UYGULANDI | B-01/B-06 bilinçli kapalı |
| PriceLock | UYGULANDI (L-11) | — |
| RFQ & Quotation | **UYGULANDI** (+ F10-022) | Match motoru; supplier UI |
| Cart & Checkout | UYGULANDI | — |
| Order Mgmt | UYGULANDI | — |
| Inventory & WH | UYGULANDI | — |
| Payments & Finance | **KISMİ** (F5 iskelet) | Gerçek ödeme |
| Quality | UYGULANDI | — |
| Shipping | UYGULANDI | Canlı carrier |
| Returns | UYGULANDI (stok-only) | F6-032; ödeme iadesi yok |
| Customer & Org | **UYGULANDI** (F10) | Zengin UI |
| Notification | UYGULANDI iskelet | Ölçek |
| Documents | KISMİ | K-014 storage |
| Workflow | **UYGULANDI** onay SM | Escalation |
| Audit | UYGULANDI (+ AUD-001b) | — |
| Reporting | PLANLANDI | F11 |
| Integration Hub | **KISMİ** stub | Canlı bağ |
| Search | PLANLANDI | F9-011 WIP / Next.js sonrası |

## 3. B2B capability alanları

| Capability | Kod durumu | Faz |
|------------|------------|-----|
| Account Hierarchy | **UYGULANDI** | F10 |
| Quick Reorder | **UYGULANDI** | F4-080 |
| Bulk Order / CSV | **UYGULANDI** | F4-081 |
| Approval Workflow | **UYGULANDI** (+ UI) | F10-013/014 |
| Contract Release Plan | **UYGULANDI** iskelet | F5-041 |
| Credit Visibility | **UYGULANDI** iskelet | F5-040 |
| Notification Outbox | **UYGULANDI** iskelet | F4-090 |
| EDI / Punchout | **UYGULANDI** stub | F7-024 |
| Live Gold / Compare / Dynamic Pricing | PLANLANDI / kilitli | F9+ / U-015 |
| Smart Replenishment / Buyer Analytics | PLANLANDI | F11 |

---

## 4. Ana geliştirme yol haritası

**Kural:** Faz kodu = ilgili ADR **Kabul** + açık talimat.

### Gate (tarihsel — kapalı)
G0–G4 kapandı (3.7 + ADR-0010/0011 + U-002 + ince PRE).

### PRE — İnce API
**UYGULANDI:** PRE-001…005 (Idempotency-Key dahil).

### Faz 4 — Ticari çekirdek
**UYGULANDI** (stok→cart→checkout→order→reorder/bulk→outbox→buyer UI). Legacy stok drop F4-070b.

### Faz 4.5 — Outbox
**UYGULANDI** iskelet (`OutboxMessage` + `process_outbox`). Celery yok.

### Faz 5 — Finans
**KISMİ UYGULANDI** (ledger/cari/PI/credit/webhook/hak ediş/mahsup/UI). Gerçek payment provider yok.

### Faz 6 — QC & lojistik
**UYGULANDI** (F6-010…031 + F6-012). F6-032 ops UI backlog.

### Faz 7 — API & entegrasyon
**UYGULANDI** iskelet (maske, catalog/supplier/ops, throttle, FakeERP/CRM, punchout stub).

### Faz 8 — Prod readiness
**KISMİ UYGULANDI** (CI, log/request_id, secret/runbook, IDOR smoke, throttle env). **Açık:** Sentry SDK (F8-003), perf baseline (F8-006), Celery/Redis, hosting/yedek prova.

### Faz 9 — Portal / API readiness
**ADR-0016 Supersede** → **ADR-0017 Taslak** (NX-1/NX-2 madde Kabul; CORS erteli). **HTML miras** (F4-062 + F10 UI; F9-010/011 WIP commit dışı). **API-B1…B7 Kabul.** **Sırada:** Next.js `frontend/` (ayrı talimat) — [MASTER](MASTER.md) §12.1b.

### Faz 10 — Kurumsal & RFQ
**UYGULANDI** çekirdek (org/limit/onay/RFQ/özel üretim + buyer UI). **Açık:** F10-021 eşleştirme; F10-023 supplier UI.

### Faz 11 — Analitik · Faz 12 — i18n
PLANLANDI.

### Stratejik öncelik (ürün sahibi 2026-11-08 — tarihsel; güncel sıra MASTER §12.3)

1. ~~Sipariş çekirdeği~~ **bitti**  
2. ~~Org geriye uyumlu~~ **bitti** (F10)  
3. ~~Quick/Bulk~~ **bitti**  
4. ~~Onay + outbox~~ **bitti** (minimal)  
5. Finans/entegrasyon olgunlaştırma + **portal (F9)** + ops (Sentry/perf)

**Bağımlılık (güncel):**  
`… → finance/QC/ship → API/EDI → F8 ops → F9 portal → (F10 kalan UI/match) → analytics → i18n`.
