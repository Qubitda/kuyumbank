# KUYUMBANK — Ana Proje Dokümanı (Master)

**Dosya:** `docs/MASTER.md`
**Rol:** Ürün/mimari **canlı durum** kaynağı (kısa tutulur). Karar metinleri, iş havuzu, yol haritası ve tarihçe ayrı dosyalardadır.
**Güncelleme:** 2026-11-10 — ops güvenlik dilimi (act-as audit AA-9, login throttle, idempotency purge); kapı **FRONTEND READY** (FE-SUITE kanıtı KISMİ)
**Dal:** `adim-1-ilerleme`

> Agent / geliştirici: önce `AGENTS.md`, sonra **bu dosya** (§2 + §12), gerekirse yalnız ilgili ADR. Kurulum: [RUNBOOK](RUNBOOK.md), kök `README.md`.

### Doküman düzeni (her bilgi tek yerde)

> ADR-0001 / **U-016 Kabul** (ürün sahibi Emre, 2026-11-09) — bağlayıcı düzen.

| Bilgi | Tek kaynak |
|-------|------------|
| Agent kuralları / yeni oturum | `AGENTS.md` → **bu dosya §2 + §12** |
| Canlı durum, B0–B7, sıradaki iş | **Bu dosya** (§12) |
| Kararlar (ADR) | [decisions/](decisions/README.md) |
| İş havuzu / U-* kararları | [BACKLOG](BACKLOG.md) |
| Hedef mimari, capability gap, yol haritası | [ROADMAP](ROADMAP.md) |
| Faz tarihçesi (append-only) | [HISTORY](HISTORY.md) |
| Kurulum / işletim / prod öncesi | [RUNBOOK](RUNBOOK.md) |
| Veri sözlüğü (otomatik) | [DATA_DICTIONARY](DATA_DICTIONARY.md) |
| API insan özeti (B7; OpenAPI normatif) | [API_CONTRACT](API_CONTRACT.md) |

**Yasak:** ikinci master, `SESSION_HANDOFF`, ayrı “durum raporu” veya paralel özet dosyası üretmek.

**Eski § numaraları:** §4 tablo/§4.1 → ROADMAP §2–3 · §6 → decisions/ · §7 → HISTORY · §8–9 → ROADMAP · §10–11 → BACKLOG. (§12 numarası korundu.)

**Durum etiketleri:** `UYGULANDI` · `TEST EDİLDİ` · `KISMİ` · `PLANLANDI` · `KARAR BEKLİYOR` · `DOĞRULANAMADI`

---

## 1. Proje tanımı ve vizyon

### 1.1 Nedir?

**Kuyumbank**, kuyumculuk sektörüne özel bir **Jewelry B2B Commerce & Trading Platform**’udur. Katalog, tedarikçi pazaryeri, dinamik fiyatlama, teklif, fiyat kilidi, stok, sipariş, finans, üretim, kalite kontrol, lojistik ve satış sonrasını **tek kapalı devre** platformda birleştirmeyi hedefler.

### 1.2 Problem

Açık pazaryerlerinde alıcı–tedarikçi kimlik sızıntısı, dağınık fiyat/kur, stok çift satışı ve denetimsiz sipariş riski yüksektir. Kuyumbank platform aracılığıyla **kör havuz** ticareti, **değişmez fiyat snapshot**’ı ve kontrollü operasyon sağlar.

### 1.3 Hedef kullanıcılar ve roller

| Rol | Görür | Görmez |
|-----|-------|--------|
| **Alıcı firma** | Platform kataloğu, kendine sunulan fiyat/koşul, kendi sipariş/belge | Tedarikçi kimliği, iç maliyet, iç SKU, platform marj kırılımı (hukuk onayı yoksa) |
| **Tedarikçi firma** | Kendi teklifleri, atanmış işler, kendi stok yüzeyi | Alıcı kimliği, diğer tedarikçi teklifleri |
| **Platform** | Yetki matrisindeki operasyon + audit | — |

Her kullanıcı **tek firmaya** bağlıdır; platform firması tekildir (ADR-0003).

### 1.4 Ticari model

Platform katalog sahibidir. Tedarikçiler varyanta teklif verir. Alıcı fiyatı platform quote’undan gelir (ham tedarikçi maliyeti değil). Siparişte fiyat kilitlenir/snapshot alınır; sonraki kur/sözleşme geçmişi değiştirmez.

### 1.5 Prosperer seviyesi

Hedef: **HYCOM Prosperer sınıfı** B2B Commerce yetenek seti (katalog, fiyat listesi, sepet/sipariş, stok, finans, portal, entegrasyon). Prosperer’ın tek tek özellikleri bu repoda **runtime ile DOĞRULANAMADI**; kıyas ürün sahibi hedef çerçevesidir.

**Ayrışma (kuyumculuk):** metal/ayar/milyem/gram, kur zaman damgası, quote TTL + PriceLock, kör çoklu teklif, taş maliyeti (K-011), ileride QC gram toleransı, konsinye/emanet, özel üretim/RFQ.

---

## 2. Mevcut sistemin gerçek durumu

**Kanıt önceliği:** kod/migration/test > kabul ADR > son faz raporu.  
**Kod kökü:** `backend/config/` · **Python** 3.12–3.14 (dev 3.14.6) · **Django** 6.1.2 · **PostgreSQL**.

### 2.1 Teknoloji yığını

| Bileşen | Durum | Etiket |
|---------|-------|--------|
| Django 6.1.2 modular monolith | `requirements.txt` pin | UYGULANDI |
| PostgreSQL + psycopg | varsayılan DB | UYGULANDI |
| django-environ, import-export, Pillow, **DRF 3.18.3** | requirements | UYGULANDI |
| Celery / Redis | requirements’ta yok (bilinçli) | PLANLANDI |
| Next.js `frontend/` | **NX-FE UYGULANDI** (iskelet; App Router + session/CSRF rewrite); uyum denetimi [FRONTEND_ARCHITECTURE §9](../frontend/docs/FRONTEND_ARCHITECTURE.md) | ADR-0017 **Taslak** |
| HTTP yüzeyi | `admin/` + `/api/v1/` (**B1–B7 Kabul**) + `/buyer/` + `/ops/finance/` | KISMİ (Prosperer portal yok) |

### 2.2 Uygulama / paketler (ADR-0004)

`INSTALLED_APPS` (DOĞRULANDI `config/settings.py` + AUTO §2.7): domain `tanimlar`…`kalite` + `api` (+ DRF).  
Domain app’ler: ADR-0004 `models/` / `services/` / `selectors/` / `admin/` / `tests/`.  
**Yok:** Celery. **Var:** `finans` (F5), `kalite`, `lojistik`, `belgeler` (F6-012).  
**HTTP:** `admin/` + `/api/v1/` + `/buyer/` + `/ops/finance/` (DOĞRULANDI).

<!-- AUTO:apps -->
`INSTALLED_APPS` (koddan): `django.contrib.*` (7), `import_export`, `rest_framework`, `rest_framework.authtoken`, `drf_spectacular`, `tanimlar`, `firmalar`, `fiyatlama`, `urunler`, `stok`, `siparis`, `finans`, `kalite`, `lojistik`, `belgeler`, `piyasa`, `api`
<!-- /AUTO:apps -->

### 2.3 Modül uygulama durumu (kod gerçeği)

| Alan | Kod durumu | Not |
|------|------------|-----|
| Firma / kullanıcı / RBAC / AuditOlay | **Tamamlanmış** | AUD-001 + AUD-001b (`ip_address`/`changes`) |
| Tanımlar / kur / kanal / PB | **Tamamlanmış** | |
| Katalog / eşleştirme / onay | **Tamamlanmış** | |
| Teklif SM / sözleşme K-007/008 | **Tamamlanmış** | |
| Fiyat motoru / PriceQuote / Lock | **Tamamlanmış** | Lock’ta `has_adet` yok |
| Warehouse / Movement / Balance | **Tamamlanmış** | F4 dilim 1–2; legacy kolon drop F4-070b |
| StockReservation TTL/oversell | **Tamamlanmış** | F4-020/021/022 (lazy + command; §12.2) |
| Cart / CartLine | **Tamamlanmış** | F4-030/031 |
| Checkout (aday) | **Tamamlanmış** | F4-040/041 |
| Order / OrderLine | **Tamamlanmış** | F4-050…053 (iptal = stok IADE) |
| FX / hedge / cari / PI / credit / webhook | **Tamamlanmış (iskelet)** | ADR-0012; F5-010…032; F5-041; F5-022 hak ediş; F5-023 mahsup |
| QC QualityInspection SM | **UYGULANDI** | F6-010+011 |
| Shipment / lojistik | **UYGULANDI** | F6-020…023 + F6-030/031 return SM + stok IADE |
| İnce PRE API | **Tamamlanmış** | PRE-001…005 (+ credit/finance/ops/webhook/catalog/supplier) |
| Org / limit / onay / RFQ | **Tamamlanmış (çekirdek)** | F10-010…014/020/022/023; F10-021 eşleştirme UYGULANDI |
| Ops readiness (F8) | **Kısmi** | 001–009 çekirdek var; F8-003 SDK UYGULANDI (staging event DOĞRULANAMADI); F8-006 baseline UYGULANDI |
| Ödeme provider / kargo / tam Prosperer API | **Uygulanmamış** | Fake payment adapter var; gerçek provider yok |

### 2.4 Veri modelleri

Alan düzeyinde ve otomatik: [DATA_DICTIONARY](DATA_DICTIONARY.md).

**Legacy stok:** `Varyant.stok` / `TedarikciTeklif.stok_adet` **kaldırıldı** (F4-070b); truth = ledger (`StockMovement` / `StockBalance`).

### 2.5 Servisler / selector’lar (DOĞRULANDI dizin listesi)

| Servis | Rol | Etiket |
|--------|-----|--------|
| `firmalar`: yetki / rol / audit / org / limit / onay + buyer approval UI | RBAC, F10, durable fail audit | UYGULANDI |
| `urunler`: onay / eslestirme / kategori / gram_bandi / seo | katalog SM | UYGULANDI |
| `tanimlar`: kur_servisi / currency_conversion | kur + PB | UYGULANDI |
| `fiyatlama`: teklif / sozlesme / pricing / `release_servisi` | teklif+quote+lock+release | UYGULANDI |
| `fiyatlama.selectors.buyer_quote` | B-02 alıcı yüzeyi | UYGULANDI |
| `stok`: warehouse / ledger / reservation / birim | F4 stok | UYGULANDI |
| `siparis`: cart / checkout / order / reorder / bulk / buyer_ui / rfq_ui | F4 + F10-023 RFQ UI | UYGULANDI |
| `finans`: ledger / cari / payment / credit / webhook / buyer+ops | F5 finans | UYGULANDI |
| `kalite`: `inspection_servisi` / `olcum_servisi` / `tolerans_motoru` | F6-010 SM + F6-011 ölçüm | UYGULANDI |
| `lojistik`: `shipment`/`pod`/`buyer_shipment` + `carriers` | F6-020…023 | UYGULANDI |
| `fiyatlama.karlilik_simulasyonu` | Excel A/B P&L (ADR-0014); KS-6 `quote(hedef_toplam=)` | UYGULANDI |
| `belgeler`: `document_servisi` + tenant selector | F6-012 Document + taş sertifika | UYGULANDI |
| `api`: `/api/v1/` PRE + B1–B7 (buyer/supplier/ops/org/RFQ/QC…) | HTTP + OpenAPI/API_CONTRACT | UYGULANDI |
| tenant selectors (`firmalar`/`urunler`/`stok`/`siparis`/…) | firma scope | UYGULANDI |

### 2.6 Güvenlik (kodda karşılığı olan)

- Tenant: selector + admin queryset; `view_all_tenants` yalnız platform+perm.  
- Superuser iş kuralı kısa yolu yok (servis perm).  
- Kör havuz: buyer_quote maske; IDOR → DoesNotExist.  
- Quote/Lock: app immutability + PG trigger (mig 0007 / 0010–0011).  
- PriceLock create: `lock_quote` / `lock_quote_on_behalf`; `view_all_tenants` create vermez.  
- Stok: movement immutable; reservation create/cancel/expire fiziksel movement yazmaz; consume → SATIS; iptal → IADE.  
- API: B1–B7 tenant 404/403 + maske; client `firma_id` yok sayılır; Token + Basic + Session; throttle; OpenAPI `--check`.  
- AuditOlay: create OK; instance/QuerySet UPDATE/DELETE yasak (AUD-001); `ip_address`/`changes` (AUD-001b).  
- F8-002: `X-Request-ID` + structured log; secret scrub (`logging_utils`). F8-007 IDOR smoke paketi.  
- **Yok (henüz):** tam Prosperer API / object-level DRF perm matrisi; Next.js ürün portalı (katalog/sepet). **Var:** Sentry SDK (DSN opt-in); `frontend/` NX-FE iskelet. Django `/buyer/` `/ops/` HTML miras kalır.

### 2.7 Test / migration / yüzey (otomatik + koşu sonucu)

<!-- AUTO:tests -->
Statik test sayısı (`def test_`): **677** — `api` 107 · `firmalar` 72 · `fiyatlama` 152 · `finans` 61 · `kalite` 19 · `lojistik` 20 · `belgeler` 6 · `siparis` 76 · `stok` 37 · `tanimlar` 32 · `urunler` 95
_(git-tracked `test_*.py`; WIP untracked sayılmaz). Koşu sonucu değildir; son suite aşağıda elle._
<!-- /AUTO:tests -->

**Statik sayım ≠ suite sonucu:** üstteki AUTO blok koşulmuş test değildir.  
**Son kaydedilen suite (elle):** **597 OK** (2026-11-09, PG `--keepdb`) — tarihsel.  
**Ara kayıt:** tam suite **713** hedef / **4 migration ERROR** (keepdb/eski mig; DOĞRULANAMADI bu oturumda yeniden koşulmadıysa).  
`makemigrations --check` / migrate pending: üretim migrate onaysız yok. Yerel dilim: `firmalar.0010` (audit `on_behalf_of`) bekleyebilir.

<!-- AUTO:migrations -->
| App | Migration sayısı | Son migration |
|-----|-----------------|---------------|
| `api` | 1 | `0001_pre_005_idempotency_record` |
| `firmalar` | 10 | `0010_audit_on_behalf_of` |
| `fiyatlama` | 19 | `0019_cap_piyasa_adr0018` |
| `finans` | 6 | `0006_f5_022_tedarikci_hak_edis` |
| `kalite` | 2 | `0002_f6_011_quality_measurement` |
| `lojistik` | 3 | `0003_f6_030_return_request` |
| `belgeler` | 1 | `0001_f6_012_document_tas_sertifika` |
| `siparis` | 6 | `0006_f10_021_rfq_eslestirme` |
| `stok` | 3 | `0003_faz4_3_stock_reservation` |
| `tanimlar` | 5 | `0005_cap_alert_kur_alert` |
| `urunler` | 11 | `0011_cap_piyasa_adr0018` |
<!-- /AUTO:migrations -->

> Not: `api.0001` yerel/dev `migrate` uygulandı; **üretim migrate ürün sahibi onayı olmadan yok.**

**HTTP yüzeyi** (`/admin/` + `/buyer/` + `/ops/finance/` + aşağıdaki `/api/v1/`; yazma: checkout/bulk/webhook POST):

<!-- AUTO:api_urls -->
| Yol | Ad |
|-----|----|
| `/api/v1/health/` | `api-health` |
| `/api/v1/auth/csrf/` | `api-auth-csrf` |
| `/api/v1/auth/login/` | `api-auth-login` |
| `/api/v1/auth/logout/` | `api-auth-logout` |
| `/api/v1/me/` | `api-me` |
| `/api/v1/catalog/` | `api-buyer-catalog` |
| `/api/v1/catalog/<int:pk>/` | `api-buyer-catalog-detail` |
| `/api/v1/quotes/` | `api-quote-create` |
| `/api/v1/quotes/<int:pk>/` | `api-quote-detail` |
| `/api/v1/price-locks/` | `api-price-lock-create` |
| `/api/v1/price-locks/<int:pk>/` | `api-price-lock-detail` |
| `/api/v1/carts/me/` | `api-cart-mine` |
| `/api/v1/carts/me/lines/` | `api-cart-line-create` |
| `/api/v1/carts/me/lines/<int:line_id>/` | `api-cart-line-detail` |
| `/api/v1/carts/<int:pk>/` | `api-cart-detail` |
| `/api/v1/checkouts/` | `api-checkout-create` |
| `/api/v1/bulk-orders/` | `api-bulk-order-create` |
| `/api/v1/orders/from-checkout/` | `api-order-from-checkout` |
| `/api/v1/orders/` | `api-order-list` |
| `/api/v1/orders/<int:pk>/` | `api-order-detail` |
| `/api/v1/orders/<int:pk>/cancel/` | `api-order-cancel` |
| `/api/v1/orders/<int:pk>/reorder/` | `api-order-reorder` |
| `/api/v1/shipments/` | `api-shipment-list` |
| `/api/v1/shipments/<int:pk>/` | `api-shipment-detail` |
| `/api/v1/returns/` | `api-return-list` |
| `/api/v1/returns/<int:pk>/` | `api-return-detail` |
| `/api/v1/returns/<int:pk>/submit/` | `api-return-submit` |
| `/api/v1/returns/<int:pk>/approve/` | `api-return-approve` |
| `/api/v1/returns/<int:pk>/reject/` | `api-return-reject` |
| `/api/v1/returns/<int:pk>/cancel/` | `api-return-cancel` |
| `/api/v1/returns/<int:pk>/mahsup/` | `api-return-mahsup` |
| `/api/v1/supplier/offers/` | `api-supplier-offers` |
| `/api/v1/supplier/offers/<int:pk>/` | `api-supplier-offer-detail` |
| `/api/v1/supplier/offers/<int:pk>/submit/` | `api-supplier-offer-submit` |
| `/api/v1/supplier/offers/<int:pk>/deactivate/` | `api-supplier-offer-deactivate` |
| `/api/v1/supplier/offers/<int:pk>/versions/` | `api-supplier-offer-versions` |
| `/api/v1/supplier/stock/` | `api-supplier-stock` |
| `/api/v1/supplier/stock/adjustments/` | `api-supplier-stock-adjust` |
| `/api/v1/supplier/rfqs/` | `api-supplier-rfq-list` |
| `/api/v1/supplier/rfqs/<int:pk>/` | `api-supplier-rfq-detail` |
| `/api/v1/supplier/rfqs/<int:pk>/messages/` | `api-supplier-rfq-message` |
| `/api/v1/supplier/rfqs/<int:pk>/revisions/` | `api-supplier-rfq-revision` |
| `/api/v1/credit/me/` | `api-credit-mine` |
| `/api/v1/credit/check/` | `api-credit-check` |
| `/api/v1/finance/me/` | `api-finance-mine` |
| `/api/v1/finance/cari/` | `api-finance-cari` |
| `/api/v1/finance/cari/<int:pk>/` | `api-finance-cari-detail` |
| `/api/v1/finance/ledger/` | `api-finance-ledger` |
| `/api/v1/reports/orders/` | `api-reports-orders` |
| `/api/v1/reports/buyer-behavior/` | `api-reports-buyer-behavior` |
| `/api/v1/payments/intents/` | `api-payment-intent-create` |
| `/api/v1/ops/finance/` | `api-ops-finance` |
| `/api/v1/ops/finance/cari/` | `api-ops-finance-cari` |
| `/api/v1/ops/finance/ledger/` | `api-ops-finance-ledger` |
| `/api/v1/ops/finance/payments/` | `api-ops-finance-payments` |
| `/api/v1/ops/anomalies/ciro/` | `api-ops-anomalies-ciro` |
| `/api/v1/ops/orders/summary/` | `api-ops-orders-summary` |
| `/api/v1/ops/inspections/` | `api-ops-inspection-list` |
| `/api/v1/ops/inspections/<int:pk>/` | `api-ops-inspection-detail` |
| `/api/v1/ops/inspections/<int:pk>/start/` | `api-ops-inspection-start` |
| `/api/v1/ops/inspections/<int:pk>/pass/` | `api-ops-inspection-pass` |
| `/api/v1/ops/inspections/<int:pk>/fail/` | `api-ops-inspection-fail` |
| `/api/v1/ops/inspections/<int:pk>/cancel/` | `api-ops-inspection-cancel` |
| `/api/v1/ops/inspections/<int:pk>/measurements/` | `api-ops-inspection-measurement` |
| `/api/v1/ops/shipments/` | `api-ops-shipment-list` |
| `/api/v1/ops/shipments/<int:pk>/` | `api-ops-shipment-detail` |
| `/api/v1/ops/shipments/<int:pk>/prepare/` | `api-ops-shipment-prepare` |
| `/api/v1/ops/shipments/<int:pk>/dispatch/` | `api-ops-shipment-dispatch` |
| `/api/v1/ops/shipments/<int:pk>/deliver/` | `api-ops-shipment-deliver` |
| `/api/v1/ops/shipments/<int:pk>/cancel/` | `api-ops-shipment-cancel` |
| `/api/v1/ops/shipments/<int:pk>/pod/` | `api-ops-shipment-pod` |
| `/api/v1/payments/webhook/` | `api-payment-webhook` |
| `/api/v1/org-units/` | `api-org-list` |
| `/api/v1/org-units/<int:pk>/` | `api-org-detail` |
| `/api/v1/org-units/<int:pk>/members/` | `api-org-members` |
| `/api/v1/approvals/` | `api-approval-list` |
| `/api/v1/approvals/<int:pk>/` | `api-approval-detail` |
| `/api/v1/approvals/<int:pk>/submit/` | `api-approval-submit` |
| `/api/v1/approvals/<int:pk>/approve/` | `api-approval-approve` |
| `/api/v1/approvals/<int:pk>/reject/` | `api-approval-reject` |
| `/api/v1/rfqs/` | `api-rfq-list` |
| `/api/v1/rfqs/<int:pk>/` | `api-rfq-detail` |
| `/api/v1/rfqs/<int:pk>/send/` | `api-rfq-send` |
| `/api/v1/rfqs/<int:pk>/messages/` | `api-rfq-message` |
| `/api/v1/rfqs/<int:pk>/revisions/` | `api-rfq-revision` |
| `/api/v1/schema/` | `api-schema` |
<!-- /AUTO:api_urls -->

**Yönetim komutları:**

<!-- AUTO:commands -->
| Komut | Açıklama |
|-------|----------|
| `manage.py purge_idempotency_records` (api) | En fazla kaç kayıt silinsin |
| `manage.py audit_user_assignments` (firmalar) | Kullanıcıların firma/rol atamalarını salt okunur biçimde denetler. |
| `manage.py bootstrap_platform` (firmalar) | Firmasız superuser/staff için atanacak platform rolü |
| `manage.py process_outbox` (firmalar) | PENDING transactional outbox mesajlarını işler (F4-090, at-least-once). |
| `manage.py seed_demo_portals` (firmalar) | DEMO_ALICI / DEMO_TEDARIKCI + portal kullanıcıları (idempotent). |
| `manage.py seed_role_permissions` (firmalar) | Rol → permission matrisini idempotent şekilde Group |
| `manage.py expire_stale_reservations` (stok) | ISO-8601 an (test); yoksa timezone.now() |
| `manage.py evaluate_kur_alerts` (tanimlar) | Kur alert kurallarını tara; stale’de tetik yok. |
| `manage.py seed_fiyat_gruplari` (tanimlar) | Varsayılan fiyat gruplarını ekler (tekrar çalıştırılabilir). Adları admin |
| `manage.py seed_tanimlar` (tanimlar) | Varsayılan metal, ayar/milyem ve satış kanalı kayıtlarını ekler (tekrar çalıştırılabilir). |
| `manage.py sync_binance_kur` (tanimlar) | Binance XAUUSDT×USDTTRY → gram TRY metal kuru (manage_kur actor). |
| `manage.py sync_tcmb_kur` (tanimlar) | TCMB EOD döviz gözlemi (kaynak=tcmb). |
| `manage.py seed_urunler` (urunler) | Ürün formundaki seçim listelerini ve ana kategorileri ekler (tekrar çalıştırılabilir). |
<!-- /AUTO:commands -->

### 2.8 Açık / bekleyen durumlar (özet)

| Konu | Durum |
|------|-------|
| B-01 platform servis payı | **Kabul** (2026-11-09) — v1 kapalı/0; kod yok |
| B-06 KDV | **Kabul** (2026-11-09) — KDV yok / proforma devam |
| ADR-0012 (audit/FX/hedge/cari) | **Kabul** |
| PRE-005 Idempotency-Key + checkout POST | UYGULANDI · TEST EDİLDİ |
| Ödeme / tam Prosperer API | PLANLANDI |
| Prosperer özellik parity | **DOĞRULANAMADI** — ayrı ürün/kaynak kıyası gerekir; bu repoda runtime kanıt yok |
| U-003…007, 009…011, U-013…015 | **Kabul** (2026-11-09, Emre; dış onaylılarda ürün sahibi override) — [BACKLOG](BACKLOG.md) |
| U-014 / U-015 / U-016 | **Kabul** (2026-11-09) |
| ADR-0001 doküman düzeni (U-016) | **Kabul** |
| B-01 / B-06 | **Kabul** (Qubit 2026-11-09); kod bilinçli yok |
| ADR-0014 | **Kabul** — sim + KS-6 `quote(hedef_toplam=)` **UYGULANDI** |
| F8-003 Sentry SDK / F8-006 perf | **UYGULANDI** (SDK + baseline); staging event **DOĞRULANAMADI** |
| F9 / API readiness | ADR-0016 Supersede · ADR-0017 **Taslak** (NX-1…12 madde Kabul) · **API-B1…B7 Kabul** |
| F10-021 eşleştirme | **UYGULANDI** — `RFQEslestirme` + `rfq_eslestirme_servisi` (platform onay) |
| F10-022 özel üretim | **UYGULANDI** (`siparis.0005`) |
| F10-023 supplier UI | **UYGULANDI** (ADR-0021 `/supplier/` okuma; yazma API) |
| CAP-PIYASA / ADR-0018 | **UYGULANDI** — LKG+banner, batch, guardrail, Binance/TCMB adaptör |
| CAP-PANO / ADR-0020 | **UYGULANDI** (çekirdek v1) — baz fiyat + admin + kar yardımcısı + PANO/MANUEL |
| CAP-PANO-v2 / ADR-0022 | **UYGULANDI** — grup/darphane/global marj/birimli kesinti (ONS/KG v2.1) |
| CAP-MAHSUP-HTTP / ADR-0023 | **UYGULANDI** — `POST returns/{id}/mahsup/` + approve `mahsup` |
| CAP-PANO-PP9 / ADR-0024 | **UYGULANDI** — PANO\|MANUEL → PriceQuote (`quote_baglama`) |
| CAP-PANO-v2.1 / ADR-0025 | **UYGULANDI** — ONS/KG + TRY/USD pano satırları |
| CAP-RAPOR-HTTP / ADR-0026 | **UYGULANDI** — reports + ciro anomali HTTP |
| API_READINESS | **FRONTEND READY** (2026-11-10, Qubit) |
| CAP-ACTAS / ADR-0021 | **UYGULANDI** — act-as + `/supplier/` HTML + `seed_demo_portals` |

Karar tablosu ve ADR durumları: [decisions/README](decisions/README.md).

---

## 3. Mimari ve teknik standartlar

### 3.1 Bağlayıcı (Kabul ADR özeti)

| Konu | Kural | Kaynak |
|------|-------|--------|
| Monolith | Erken mikroservis yok; ADR-0004 paket düzeni | ADR-0004 **Kabul** |
| Runtime | Django 6.1.x pin, PG, requirements yalnız kullanılan paket | ADR-0002 **Kabul** |
| Kimlik | Tek firma + tek rol; full_clean tüm kullanıcılar | ADR-0003 **Kabul** |
| Yetki | `has_perm` / matris; superuser bypass yok | ADR-0003 |
| Tenant | Selector zorunlu; client `firma_id` güvenilmez | ADR-0003-05 |
| Katalog | Platform ownership; `olusturan_firma` | ADR-0005 **Kabul** |
| Teklif | Durum yalnız servis; eşleşme kapısı | ADR-0007 **Kabul** |
| Sözleşme | NULL-safe unique / exclusion | ADR-0007 |
| Fiyat | Üç model; quote immutable; TTL kanal; kör B-02 | ADR-0008 **Kabul** |
| Admin sertleştirme | H1–H5 | ADR-0009 **Kabul** |
| PriceLock L-01…L-10; L-11 OrderLine bağ | Servis+DB+test | ADR-0010 **Kabul**; L-11 **UYGULANDI** (F4-051) |
| Para | `Decimal`; float yasak | standart |
| Yazım | `domain_atomic`; fail audit durable dışı | audit_servisi |
| Concurrency | `select_for_update` + DB kısıt | standart |
| Migration | Üretim migrate onaysız yok; satır silerek NOT NULL yok | AGENTS |
| API | `/api/v1/` PRE + B1–B7 HTTP + sözleşme; tam Prosperer yok | PRE + B1–B7 Kabul — §12.1b |
| Test | Risk bazlı; PG constraint SQLite ile “geçti” sayılmaz | AGENTS Ek C |

### 3.2 Doküman ve agent kuralı

Her bilgi **tek yerde** (üstteki tablo). Durum etiketi yalnız bu dosyada; diğer dosyalar link verir.
`DATA_DICTIONARY.md` ve `<!-- AUTO -->` blokları elle düzenlenmez: geliştirme bitince `python scripts/docs_sync.py`;
CI `--check` bayat doküman ve kırık bağlantıyı reddeder. Yeni faz raporu / ikinci yol haritası / ayrı rapor dosyası **açılmaz**.
Büyük kararlar `docs/decisions/` altına ADR olarak eklenir; ADR'yi yalnız ürün sahibi Kabul eder.

---

## 4. Ürün domainleri ve işleyiş

Domain bazlı durum/eksik tablosu, B2B capability alanları ve Prosperer gap: [ROADMAP](ROADMAP.md) §2–§3.

**İş kuralları (çekirdek):** kör havuz; quote fail-closed; stok üçlüsü ayrı; ADET↔GRAM dönüşüm yok; **Cart → CheckoutAttempt → Order** (lock+rezerv+tüket+iptal/IADE; finans yok).

---

## 5. Kuyumculuk sektörü gereksinimleri

| Gereksinim | Durum |
|------------|-------|
| Altın/gümüş/metal + ayar/milyem | UYGULANDI |
| Gram / adet / sabit parça modelleri | UYGULANDI |
| İşçilik + kanal marj | UYGULANDI |
| Taş maliyeti (teklif vs katalog ayrımı K-011) | UYGULANDI |
| Sertifika kurum/no/dosya | KISMİ — metadata+tenant belge F6-012; object storage K-014 yok |
| Kur/metal zaman damgası + stale fail-closed | UYGULANDI (CAP-PIYASA LKG/banner = ADR-0018 **Kabul**) |
| PriceQuote + PriceLock | UYGULANDI (sipariş bağ L-11 UYGULANDI) |
| Fiyat girdi izi (`hesap_girdisi`) | KISMİ (JSON var; UI yok) |
| Kör çoklu teklif pazaryeri | UYGULANDI |
| Seri/lot/batch, emanet/konsinye, depo transfer | PLANLANDI · U-008 |
| Üretim / özel sipariş / RFQ | PLANLANDI |
| Gram tolerans + QC | UYGULANDI — F6-010 SM + F6-011 ölçüm |
| Teslimat / uyuşmazlık | UYGULANDI — F6-020…023 + F6-030/031 stok-only iade (U-004); ödeme iadesi yok |

---

## 12. Güncel proje durumu ve sıradaki adım

### 12.1 Özet

| Madde | Değer |
|-------|--------|
| Dal | `adim-1-ilerleme` |
| Faz | F4–F8 **UYGULANDI** · F9 HTML miras · **NX-FE UYGULANDI** · **API-B1…B7 Kabul** · F10 **UYGULANDI** |
| ADR | 0010–0015 **Kabul** · 0016 **Supersede** · 0017 **Taslak** · **0018 Kabul** · **0019 Kabul** |
| Test / migration / apps | Otomatik bloklar (§2.7); yerel migrate (`fiyatlama.0019` / `tanimlar.0004` CAP-PIYASA) |

### 12.1b API-B0…B7 (ürün sahibi kesin tablo)

| Faz | Durum |
|-----|--------|
| **B0** | Tamamlandı |
| **B1** | Kullanıcı tarafından **Kabul** |
| **B2** | Kullanıcı tarafından **Kabul** |
| **B2 concurrency** | PG TransactionTestCase **7 OK** — doğrulandı / Kabul |
| **B3** | Kullanıcı tarafından **Kabul** |
| **B4** | Kullanıcı tarafından **Kabul** |
| **B5** | Kullanıcı tarafından **Kabul** |
| **B6** | Kullanıcı tarafından **Kabul** |
| **B7** | Kullanıcı tarafından **Kabul** |

Sabit kararlar (özet): ADR-0017 **Taslak**; NX-1…12 **madde Kabul** (Qubit, 2026-11-09); NX-3…12 **kod UYGULANDI/KISMİ** (TECH-NX-CONTRACT-01); CORS erteli; yeni Django HTML yok; **NX-FE** `frontend/` iskelet **UYGULANDI**; tam suite / prod migrate yalnız açık onay. Ayrıntı: [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md).

### 12.2 YAPILDI (kodda var)

Faz bazlı tarihçe: [HISTORY](HISTORY.md); kart bazlı: [BACKLOG](BACKLOG.md) (`UYGULANDI` kartları, PRE-001…004 dahil).

| ID | Ne | Kanıt (özet) |
|----|-----|----------------|
| F4-022 | Reservation expire: lazy sweep + `expire_stale_reservations` + order ön-süpürme | `stok/tests/test_reservation_expire_f4_022` |
| F4-054 | OrderLine GRAM/ADET snapshot tutarlılığı (`toplam/quote.gram × miktar`) | `siparis/tests/test_order_pricing_units` |
| PRE-005 | Idempotency-Key middleware + `POST /api/v1/checkouts/` | `api.0001` + `api.tests.test_pre_005_idempotency` **3 OK** |
| F4-081 | Bulk Order / CSV: kısmi hata + idempotent Order | `bulk_servisi` + `siparis.tests.test_bulk_f4_081` **4 OK**; `POST /api/v1/bulk-orders/` |
| F4-070 | Legacy `stok`/`stok_adet` güncelleme yazımı kapalı (kolon drop yok) | `urunler.0009` / `fiyatlama.0014` + `stok.tests.test_legacy_stock_f4_070` **4 OK** |
| SEC-001 | `.env` ignore + example; throttle; proxy SSL env; **TokenAuthentication** (+ Basic 401) | `settings` + `api.tests.test_throttle` / `test_token_auth` |
| OPS-001 | CI (PG, Py 3.12/3.14, migrate check, suite) + `scripts/docs_sync.py --check` | `.github/workflows/ci.yml` |
| AUD-001 (çekirdek) | AuditOlay UPDATE/DELETE/QuerySet engeli | `firmalar.tests.test_audit_aud_001` **5 OK** |
| F4-090 | Transactional outbox (`order.created` + `process_outbox`) | `firmalar.0005` + `firmalar.tests.test_outbox_f4_090` **5 OK** |
| F4-060/061 | Buyer cart/order API + ops liste (`view_all`); tedarikçi 403 | `api.tests.test_order_api_f4_060` **4 OK** |
| F4-062 | Minimal alıcı sepet/sipariş UI (`/buyer/`) | `siparis.views.buyer_ui` + `siparis.tests.test_buyer_ui_f4_062` **3 OK** |
| F5-001 | Finans ADR paketi | ADR-0012 **Kabul** (2026-11-09) |
| F5-010 | `finans.LedgerEntry` append-only + contra + PG trigger | `finans.0001` + `finans.tests.test_ledger_f5_010` **9 OK** |
| FX-001 / HEDGE-001 | HAS `open_has` + `HedgeEntry` | `fx_servisi` / `hedge_servisi` + `finans.0002` + `test_fx_hedge_f5` **6 OK** |
| F5-011 | CariHesap projeksiyon (platform↔alıcı) | `cari_servisi` + `test_cari_f5_011` **4 OK** |
| F5-012 | PaymentIntent ↔ Order tahsilat | `payment_servisi` + `test_payment_f5_012` **5 OK**; mig `finans.0003` |
| F5-013 | Finans audit zorunlu alanlar | `finans_audit` + `test_finans_audit_f5_013` **4 OK** |
| F5-020 | Ödeme adapter port + fake (fail-closed) | `finans.payments` + `test_payment_adapter_f5_020` **5 OK** |
| F5-040 | Credit visibility (maskeli API) | `credit_servisi` + `test_credit_f5_040` **5 OK**; `/api/v1/credit/*` |
| F5-021 | Ödeme webhook iskeleti (idempotent) | `PaymentWebhookEvent` + `test_webhook_f5_021` **4 OK**; mig `0004/0005` |
| F5-030 | Buyer finans özeti API (maskeli) | `buyer_finans_servisi` + `test_buyer_finans_f5_030` **4 OK**; `/api/v1/finance/me/` |
| F5-031 | Platform finans ops API | `ops_finans_servisi` + `test_ops_finans_f5_031` **3 OK**; `/api/v1/ops/finance/*` |
| F5-041 | Contract Release Plan | `release_servisi` + `ContractReleasePlan/Event`; mig `fiyatlama.0015`; `test_contract_release_f5_041` **6 OK** |
| F5-041b | Release → sipariş tüketimi | `ContractReleaseConsumption`; order create/iptal; mig `0018`; `test_contract_release_consume_f5_041b` **4 OK** |
| AUD-001b | AuditOlay `ip_address` / `changes` | `firmalar.0006` + sidecar sync; `client_ip`; `test_audit_aud_001b` **4 OK** |
| F5-032 | Finans UI (RBAC) | `/buyer/finance/` + `/ops/finance/`; `test_finance_ui_f5_032` **4 OK** |
| F6-001 | QC ADR | [ADR-0013](decisions/ADR-0013-faz6-qc-lojistik.md) **Kabul** (2026-11-09) |
| F6-010 | QualityInspection + SM | `kalite` app + `inspection_servisi`; mig `0001`; `test_inspection_f6_010` **5 OK** |
| F6-011 | Gram/ağırlık ölçüm + tolerans | `QualityMeasurement` + `olcum_servisi` / `tolerans_motoru`; mig `0002`; `test_olcum_f6_011` **11 OK** |
| F6-020 | Shipment + QC gate | `lojistik.Shipment` + `shipment_servisi`; mig `0001`; `test_shipment_f6_020` **6 OK** |
| F6-021 | Carrier adapter + fake | `lojistik.carriers` + `sevk_et` label; `test_carrier_f6_021` **5 OK** |
| F6-022 | POD kaydı | `ProofOfDelivery` + `pod_servisi`; mig `0002`; `test_pod_f6_022` **4 OK** |
| F6-023 | Buyer sevkiyat API | `/api/v1/shipments/`; `test_shipment_api_f6_023` **3 OK** |
| KS | Karlılık sim + KS-6 | `karlilik_simulasyonu` + `quote(hedef_toplam=)` |
| F6-012 | Taş sertifika belge | `belgeler` Document + TasSertifikaBelgesi; mig `0001`; **6 OK** |
| F6-030 | Return/Dispute SM (stok-only) | `ReturnRequest`/`ReturnLine` + `return_servisi`; mig `lojistik.0003`; **5 OK** |
| F6-031 | İade stok IADE | ONAYLANDI → `StockMovement.IADE` + on_hand; F6-030 ile | 
| F5-022 | Tedarikçi hak ediş iskeleti | `TedarikciHakEdis`; QC PASS tetik; `unpaid_supplier_has`; mig `finans.0006`; **5 OK** |
| F5-023 | İade mahsup (ödeme iadesi yok) | `mahsup_servisi`; MAHSUP ALACAK; `odeme_iadesi_yap` fail-closed; **3 OK** |
| F4-070b | Legacy stok kolon drop | `urunler.0010` / `fiyatlama.0016`; `dual_stock_envanter` silindi |
| KS-6 | Hedef toplam → quote | `quote(hedef_toplam=)`; `HEDEF_TOPLAM` kalem; mig `fiyatlama.0017` |
| F10-001/010 | Account Hierarchy | ADR-0015 **Kabul**; `OrgBirimi`/`OrgUyeligi`; `Order`/`Cart.sube`; `test_org_f10_010` |
| F10-011…013 | Org scope + limit + onay | `require_org_scope`; `HarcamaLimiti`; `OnayTalebi` SM; `test_limit_onay_f10_012` |
| F10-020 | RFQ modelleri | `RFQ`/`RFQLine`/`RFQMessage` + `rfq_servisi`; `test_rfq_f10_020` |
| F10-014 | Onay kuyruğu UI | `/buyer/approvals/`; `test_approval_ui_f10_014` **5 OK** |
| F10-023 | RFQ buyer UI | `/buyer/rfq/`; kör mesaj; `test_rfq_ui_f10_023` **4 OK** |
| F10-021 | Katalog dışı eşleştirme | `RFQEslestirme` + aday/öner/onay/red; mig `siparis.0006`; `test_rfq_eslestirme_f10_021` **7 OK** |
| F10-022 | Özel üretim + revizyon | `talep_tipi` + `RFQRevizyon`; mig `siparis.0005`; `test_rfq_ozel_f10_022` **3 OK** |
| F7-010…015 | API std | maske + catalog/supplier/ops; problem+json; throttle scopes; `/api/v1/` |
| F7-020…024 | Entegrasyon iskelet | `WebhookDelivery`; FakeERP/CRM; `ConnectorRegistry`; punchout stub; **22 OK** odaklı |
| F8-001 | CI pipeline | `ci.yml` + `manage.py check`; PG 3.12/3.14 |
| F8-002 | Structured logging | `RequestIdMiddleware` + `logging_utils`; `test_logging_f8_002` |
| F8-004/005/008/009 | Ops/secret/deploy/throttle | RUNBOOK §7–§10; `DRF_THROTTLE_*` env |
| F8-007 | IDOR güvenlik smoke | `test_security_f8_007` **5 OK** |
| F8-003 | Sentry SDK | `sentry-sdk==2.69.1` + `sentry_init`; DSN boş no-op; `test_sentry_f8_003` **3 OK**; staging event DOĞRULANAMADI |
| F8-006 | Perf smoke | `api.services.perf_smoke` + `test_perf_smoke_f8_006` **1 OK** (quote/lock/checkout baseline) |
| F11-013 | Bildirim outbox kuralları | `qc.passed`/`qc.failed`/`return.approved` (+ `order.created`); `test_notify_f11_013` **3 OK** |
| CAP-PIYASA | Kur dayanıklılık (ADR-0018) | `fiyat_kaynagi` + LKG/banner + batch + guardrail + Binance/TCMB; mig `tanimlar.0004`/`urunler.0011`/`fiyatlama.0019`; `test_cap_piyasa_adr0018` **8 OK** (+ kur/quote regresyon tarihsel) |
| CAP-PANO | Piyasa panosu baz fiyat (ADR-0020) | `piyasa` app; `baz_fiyat` / `cozumle_islem_birim_fiyati` / kar yardımcısı; mig `0001`/`0002` |
| CAP-PANO-v2 | Pano domain GoldXT hizası (ADR-0022) | grup/varyant; global marj; Darphane; birimli kesinti; metal+ayar sim; mig `0003`; `piyasa.tests`+karlilik **21 OK** |
| CAP-MAHSUP-HTTP | İade mahsup REST (ADR-0023) | `POST /api/v1/returns/{id}/mahsup/`; approve `mahsup`; B3+OpenAPI **13 OK** odaklı |
| CAP-PANO-PP9 | Pano→Quote (ADR-0024) | `quote_from_islem_fiyati` → KS-6; `test_quote_baglama` **4 OK** |
| CAP-PANO-v2.1 | ONS/KG çapraz (ADR-0025) | `olcek`/`cikti_pb`; mig `0004`; hesap+fiyat **22 OK** |
| CAP-ACTAS | Act-as + tedarikçi portal (ADR-0021) | `act_as_servisi` + middleware; `/supplier/`; `seed_demo_portals`; `test_act_as_adr0021` **6 OK** |
| CAP-ALERT | Canlı kur eşik alert | `KurAlertKurali` + admin + `evaluate_kur_alerts` + outbox; stale’de yok; `test_kur_alert_cap` **4 OK** |
| F11-011 | Quote/Lock analitik | `fiyat_analitik_servisi`; **3 OK** |
| F11-012 | ATP görünümü | `atp_servisi` formül; **4 OK** |
| F11-020 | Smart replenishment | `replenishment_servisi`; **2 OK** |
| F11-001 | Raporlama read-model v1 | [NOTE-F11-001](decisions/NOTE-F11-001-raporlama-v1.md) RM-1…6; P-RM-* erteli |
| F11-010 | Ticari sipariş/ciro özet | `rapor_servisi.ticari_siparis_ozet` |
| F11-021 | Buyer behavior | `rapor_servisi.alici_davranis_ozet`; `test_rapor_f11_010_021` **6 OK** (010+021+tenant) |
| F11-014 | Ciro eşik anomali | `anomali_servisi.ciro_esik_tara`; `test_anomali_f11_014` **3 OK** |
| ADR-0019 | Object-level DRF | OL-1…11 **Kabul**; `api.permissions` commerce SoD + object access; `test_object_level_adr0019` **6 OK** |
| F9-001 | Frontend ADR | [ADR-0016](decisions/ADR-0016-faz9-frontend.md) **Supersede** → [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md) **Taslak** (NX-1…12 madde Kabul) |
| F9-010 | Buyer dashboard (Django HTML miras) | `/buyer/` home + `buyer_dashboard_servisi`; Next portal değil |
| F9-011 | Katalog browse (Django HTML miras) | `/buyer/catalog/` + `urunler.services.buyer_katalog_servisi`; Next portal değil |
| API-B0 | Next.js API boşluk analizi | **Tamamlandı** |
| API-B1 | Çekirdek API standartları | **Kabul** (Qubit 2026-11-09); odaklı **28 OK**; CORS erteli |
| API-B2 | Buyer commerce HTTP | **Kabul** (Qubit 2026-11-09); odaklı **11 OK** |
| API-B2 concurrency | Idempotency PG | **Doğrulandı** — TransactionTestCase **7 OK** |
| API-B3 | Finans/sevkiyat/iade HTTP | **Kabul** (Qubit 2026-11-09); odaklı **10 OK** |
| API-B4 | Kurumsal HTTP (org/onay/RFQ) | **Kabul** (Qubit 2026-11-09); odaklı **11 OK** |
| API-B5 | Ops QC / sevkiyat yazma | **Kabul** (Qubit 2026-11-09); odaklı **7 OK** |
| API-B6 | Tedarikçi teklif/stok + ters kör RFQ | **Kabul** (Qubit 2026-11-09); odaklı **3 OK** |
| API-B7 | API dondurma / frontend-ready | **Kabul** (Qubit 2026-11-09); OpenAPI + [API_CONTRACT](API_CONTRACT.md); odaklı **1 OK** |
| TECH-OPENAPI-01 | OpenAPI çift önek | **UYGULANDI** (B3 sonrası bakım; NX-4 madde **Kabul**) |
| TECH-NX-CONTRACT-01 | NX-3…12 kod kanıt + `application/problem+json` | **UYGULANDI**; `test_api_nx_contract` **4 OK**; NX-3…12 madde **Kabul** (Qubit) |
| NX-FE | Next.js `frontend/` iskelet | App Router + TS + Tailwind v4; `/api/v1` rewrite; session/CSRF client; `/` + `/login`; `npm run build` OK |
| NX-ARCH | Feature/domain FE mimarisi | `features/*` ↔ Django apps; `app/(portal)/*` page/loading/error; `FRONTEND_ARCHITECTURE.md`; Zod |

### 12.3 SIRADA (kodda yok — uygulama sırası)

> **FRONTEND READY** (2026-11-10). Next dilimleri ayrı açık talimatla.

| Öncelik | ID | Ne | Bağımlılık / not |
|---------|-----|-----|------------------|
| P1 | NX / F9 Next portal dilimleri | [API_READINESS](API_READINESS.md) **READY**; ürün sahibi dilim talimatı |
| P2 | F6-032 | Platform uyuşmazlık ops kuyruğu UI | P2 FE |
| — | F12-011 / DYN / I18N / AI | NOTE-PENDING **Kabul** (A seçimleri → kod yok) |

### 12.4 Bilinçli kapsam dışı (şimdi yok)

Celery/Redis · gerçek ödeme/kargo/SAP · Dynamic Pricing (U-015 kilitli) · GraphQL/websocket · yeni Django app yağmuru.  
Next.js ürün portalı (katalog+): NX-SHELL sonrası ayrı dilimler. Mevcut `/buyer/` `/ops/` HTML **silinmez**.

### 12.5 Yeni oturum başlangıcı

Tek giriş: **`AGENTS.md` → bu dosya (§2 + §12)** → görev ADR’si.  
**Üretilmez:** `SESSION_HANDOFF`, ayrı durum raporu, paralel yol haritası / özet dosyası.

1. Oku: `AGENTS.md` → **§2** (gerçek durum) + **§12** → görev ADR.  
2. Sıradaki: PG tam suite yeşil (FE-SUITE kanıtı) → Ready yeniden kilitle; Next dilimleri ayrı talimat / F6-032.
3. Ops dilim: act-as AA-9 (`firmalar.0010`), login throttle, idempotency purge, CI `piyasa.tests`.
4. **P0 kullanıcı:** zip/`.env` sızıntısı varsa `SECRET_KEY` + `DB_PASSWORD` rotasyonu (değerler repoda yok; gitignore OK).
5. ADR-0018…0026 **Kabul**; ADR-0021 AA-9; NOTE-PENDING **Kabul** (A); **FRONTEND READY** (FE-SUITE KISMİ).

*Son güncelleme: 2026-11-10 — ops güvenlik + doküman drift.*