# KUYUMBANK — Ana Proje Dokümanı (Master)

**Dosya:** `docs/MASTER.md`
**Rol:** Ürün/mimari **canlı durum** kaynağı (kısa tutulur). Karar metinleri, iş havuzu, yol haritası ve tarihçe ayrı dosyalardadır.
**Güncelleme:** 2026-11-09 — doküman yeniden yapılandırma; kod↔docs senkronu `scripts/docs_sync.py` ile
**Dal:** `adim-1-ilerleme`

> Agent / geliştirici: önce `AGENTS.md`, sonra **bu dosya** (§2 + §12), gerekirse yalnız ilgili ADR. Kurulum: [RUNBOOK](RUNBOOK.md), kök `README.md`.

### Doküman düzeni (her bilgi tek yerde)

> ADR-0001 / **U-016 Kabul** (ürün sahibi Emre, 2026-11-09) — bağlayıcı düzen.

| Bilgi | Tek kaynak |
|-------|------------|
| Agent kuralları | `AGENTS.md` |
| Canlı durum, standartlar, sıradaki iş | **Bu dosya** |
| Kararlar (ADR) | [decisions/](decisions/README.md) |
| İş havuzu / U-* kararları | [BACKLOG](BACKLOG.md) |
| Hedef mimari, capability gap, yol haritası | [ROADMAP](ROADMAP.md) |
| Faz tarihçesi | [HISTORY](HISTORY.md) |
| Kurulum / işletim / prod öncesi | [RUNBOOK](RUNBOOK.md) |
| Veri sözlüğü (otomatik) | [DATA_DICTIONARY](DATA_DICTIONARY.md) |

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
| Celery / Redis / Next.js | requirements’ta yok (bilinçli) | PLANLANDI |
| HTTP yüzeyi | `admin/` + ince PRE API (yalnız GET) | KISMİ |

### 2.2 Uygulama / paketler (ADR-0004)

`INSTALLED_APPS` (DOĞRULANDI `config/settings.py` + AUTO §2.7): domain `tanimlar`…`kalite` + `api` (+ DRF).  
Domain app’ler: ADR-0004 `models/` / `services/` / `selectors/` / `admin/` / `tests/`.  
**Yok:** Celery. **Var:** `finans` (F5), `kalite`, `lojistik`, `belgeler` (F6-012).  
**HTTP:** `admin/` + `/api/v1/` + `/buyer/` + `/ops/finance/` (DOĞRULANDI).

<!-- AUTO:apps -->
`INSTALLED_APPS` (koddan): `django.contrib.*` (7), `import_export`, `rest_framework`, `rest_framework.authtoken`, `tanimlar`, `firmalar`, `fiyatlama`, `urunler`, `stok`, `siparis`, `finans`, `kalite`, `lojistik`, `belgeler`, `api`
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
| İnce PRE API | **Tamamlanmış** | PRE-001…005 (+ credit/finance/ops/webhook) |
| Ödeme provider / kargo / tam Prosperer API | **Uygulanmamış** | Fake payment adapter var; gerçek provider yok |

### 2.4 Veri modelleri

Alan düzeyinde ve otomatik: [DATA_DICTIONARY](DATA_DICTIONARY.md).

**Legacy stok:** `Varyant.stok` / `TedarikciTeklif.stok_adet` **kaldırıldı** (F4-070b); truth = ledger (`StockMovement` / `StockBalance`).

### 2.5 Servisler / selector’lar (DOĞRULANDI dizin listesi)

| Servis | Rol | Etiket |
|--------|-----|--------|
| `firmalar`: yetki / rol / audit / platform_kurulum | RBAC, durable fail audit | UYGULANDI |
| `urunler`: onay / eslestirme / kategori / gram_bandi / seo | katalog SM | UYGULANDI |
| `tanimlar`: kur_servisi / currency_conversion | kur + PB | UYGULANDI |
| `fiyatlama`: teklif / sozlesme / pricing / `release_servisi` | teklif+quote+lock+release | UYGULANDI |
| `fiyatlama.selectors.buyer_quote` | B-02 alıcı yüzeyi | UYGULANDI |
| `stok`: warehouse / ledger / reservation / birim | F4 stok | UYGULANDI |
| `siparis`: cart / checkout / order / reorder / bulk / buyer_ui | F4 sipariş + UI | UYGULANDI |
| `finans`: ledger / cari / payment / credit / webhook / buyer+ops | F5 finans | UYGULANDI |
| `kalite`: `inspection_servisi` / `olcum_servisi` / `tolerans_motoru` | F6-010 SM + F6-011 ölçüm | UYGULANDI |
| `lojistik`: `shipment`/`pod`/`buyer_shipment` + `carriers` | F6-020…023 | UYGULANDI |
| `fiyatlama.karlilik_simulasyonu` | Excel A/B P&L (ADR-0014); KS-6 `quote(hedef_toplam=)` | UYGULANDI |
| `belgeler`: `document_servisi` + tenant selector | F6-012 Document + taş sertifika | UYGULANDI |
| `api`: health / me / cart / order / credit / finance / ops / webhook | ince PRE HTTP | UYGULANDI |
| tenant selectors (`firmalar`/`urunler`/`stok`/`siparis`/…) | firma scope | UYGULANDI |

### 2.6 Güvenlik (kodda karşılığı olan)

- Tenant: selector + admin queryset; `view_all_tenants` yalnız platform+perm.  
- Superuser iş kuralı kısa yolu yok (servis perm).  
- Kör havuz: buyer_quote maske; IDOR → DoesNotExist.  
- Quote/Lock: app immutability + PG trigger (mig 0007 / 0010–0011).  
- PriceLock create: `lock_quote` / `lock_quote_on_behalf`; `view_all_tenants` create vermez.  
- Stok: movement immutable; reservation create/cancel/expire fiziksel movement yazmaz; consume → SATIS; iptal → IADE.  
- API: ince PRE tenant 404 (cart/order); client `firma_id` yok sayılır; Token + Basic + Session; throttle.  
- AuditOlay: create OK; instance/QuerySet UPDATE/DELETE yasak (AUD-001); `ip_address`/`changes` (AUD-001b).  
- **Yok (henüz):** tam Prosperer API / object-level DRF perm matrisi.

### 2.7 Test / migration / yüzey (otomatik + koşu sonucu)

<!-- AUTO:tests -->
Statik test sayısı (`def test_`): **530** — `api` 26 · `firmalar` 67 · `fiyatlama` 148 · `finans` 61 · `kalite` 16 · `lojistik` 20 · `belgeler` 6 · `siparis` 40 · `stok` 31 · `tanimlar` 20 · `urunler` 95
_Bu sayı koşu sonucu değildir; son suite koşusu aşağıda elle tutulur._
<!-- /AUTO:tests -->

**Son suite koşusu (elle):** birleşik **354 OK** (tarihsel 2026-11-09) — **bayat**; bu sync turunda full suite koşulmadı. Odaklı: F5 finans / F5-041 / AUD-001b / F5-032 / F6-010 yeşil.
`makemigrations --check`: temiz. **Yerel/dev migrate uygulandı** (2026-11-09: `firmalar.0006`, `urunler.0009`, `fiyatlama.0014–0015`, `kalite.0001–0002`, `lojistik.0001–0002`).

<!-- AUTO:migrations -->
| App | Migration sayısı | Son migration |
|-----|-----------------|---------------|
| `api` | 1 | `0001_pre_005_idempotency_record` |
| `firmalar` | 7 | `0007_f10_f7_org_rfq_webhook` |
| `fiyatlama` | 17 | `0017_ks6_hedef_toplam_kalem` |
| `finans` | 6 | `0006_f5_022_tedarikci_hak_edis` |
| `kalite` | 2 | `0002_f6_011_quality_measurement` |
| `lojistik` | 3 | `0003_f6_030_return_request` |
| `belgeler` | 1 | `0001_f6_012_document_tas_sertifika` |
| `siparis` | 4 | `0004_f10_f7_org_rfq_webhook` |
| `stok` | 3 | `0003_faz4_3_stock_reservation` |
| `tanimlar` | 3 | `0003_faz3_3_kur_index_rename` |
| `urunler` | 10 | `0010_f4_070b_drop_legacy_stock` |
<!-- /AUTO:migrations -->

> Not: `api.0001` yerel/dev `migrate` uygulandı; **üretim migrate ürün sahibi onayı olmadan yok.**

**HTTP yüzeyi** (`/admin/` + aşağıdaki ince PRE API; yazma endpoint'i yok):

<!-- AUTO:api_urls -->
| Yol | Ad |
|-----|----|
| `/api/v1/health/` | `api-health` |
| `/api/v1/me/` | `api-me` |
| `/api/v1/catalog/` | `api-buyer-catalog` |
| `/api/v1/carts/me/` | `api-cart-mine` |
| `/api/v1/carts/<int:pk>/` | `api-cart-detail` |
| `/api/v1/checkouts/` | `api-checkout-create` |
| `/api/v1/bulk-orders/` | `api-bulk-order-create` |
| `/api/v1/orders/` | `api-order-list` |
| `/api/v1/orders/<int:pk>/` | `api-order-detail` |
| `/api/v1/shipments/` | `api-shipment-list` |
| `/api/v1/shipments/<int:pk>/` | `api-shipment-detail` |
| `/api/v1/supplier/offers/` | `api-supplier-offers` |
| `/api/v1/supplier/stock/` | `api-supplier-stock` |
| `/api/v1/credit/me/` | `api-credit-mine` |
| `/api/v1/credit/check/` | `api-credit-check` |
| `/api/v1/finance/me/` | `api-finance-mine` |
| `/api/v1/ops/finance/` | `api-ops-finance` |
| `/api/v1/ops/finance/cari/` | `api-ops-finance-cari` |
| `/api/v1/ops/finance/ledger/` | `api-ops-finance-ledger` |
| `/api/v1/ops/orders/summary/` | `api-ops-orders-summary` |
| `/api/v1/payments/webhook/` | `api-payment-webhook` |
| `/api/v1/schema/` | `api-schema` |
<!-- /AUTO:api_urls -->

**Yönetim komutları:**

<!-- AUTO:commands -->
| Komut | Açıklama |
|-------|----------|
| `manage.py audit_user_assignments` (firmalar) | Kullanıcıların firma/rol atamalarını salt okunur biçimde denetler. |
| `manage.py bootstrap_platform` (firmalar) | Firmasız superuser/staff için atanacak platform rolü |
| `manage.py process_outbox` (firmalar) | PENDING transactional outbox mesajlarını işler (F4-090, at-least-once). |
| `manage.py seed_role_permissions` (firmalar) | Rol → permission matrisini idempotent şekilde Group |
| `manage.py expire_stale_reservations` (stok) | ISO-8601 an (test); yoksa timezone.now() |
| `manage.py seed_fiyat_gruplari` (tanimlar) | Varsayılan fiyat gruplarını ekler (tekrar çalıştırılabilir). Adları admin |
| `manage.py seed_tanimlar` (tanimlar) | Varsayılan metal, ayar/milyem ve satış kanalı kayıtlarını ekler (tekrar çalıştırılabilir). |
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
| Prosperer özellik parity | DOĞRULANAMADI (hedef kıyas) |
| U-003…007, 009…011, U-013…015 | **Kabul** (2026-11-09, Emre; dış onaylılarda ürün sahibi override) — [BACKLOG](BACKLOG.md) |
| U-014 / U-015 / U-016 | **Kabul** (2026-11-09) |
| ADR-0001 doküman düzeni (U-016) | **Kabul** |
| B-01 / B-06 | **Kabul** (Qubit 2026-11-09); kod bilinçli yok |
| ADR-0014 | **Kabul** — sim UYGULANDI; quote hedef ayrı dilim |

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
| API | İnce PRE (`/api/v1/`); tam Prosperer yok | PRE-001…004 UYGULANDI |
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
| Kur/metal zaman damgası + stale fail-closed | UYGULANDI |
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
| Faz | F4–F6 **UYGULANDI** · F7 API/entegrasyon iskelet **UYGULANDI** · F10 org/limit/onay/RFQ **UYGULANDI** (UI portal kısmi) |
| ADR | 0010–0015 **Kabul** — [indeks](decisions/README.md) |
| Test / migration / apps | Otomatik bloklar (§2.7); yerel migrate uygulandı (2026-11-09; `firmalar.0007`/`siparis.0004`) |

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
| F7-010…015 | API std | maske + catalog/supplier/ops; problem+json; throttle scopes; `/api/v1/` |
| F7-020…024 | Entegrasyon iskelet | `WebhookDelivery`; FakeERP/CRM; `ConnectorRegistry`; punchout stub; **22 OK** odaklı |

### 12.3 SIRADA (kodda yok — uygulama sırası)

| Öncelik | ID | Ne | Bağımlılık / not |
|---------|-----|-----|------------------|
| **1** | F8 / F9 | CI ops / buyer portal UI | ROADMAP; Celery yok |
| — | F10-014/021–023 | Onay/RFQ portal UI | F10 çekirdek UYGULANDI; admin salt-okunur |
| — | F6-032 | Platform uyuşmazlık ops kuyruğu UI | F6-030 sonrası; P2 |
| — | CAP-PIYASA | Canlı altın/döviz beslemesi | kod yok |

### 12.4 Bilinçli kapsam dışı (şimdi yok)

Celery/Redis · gerçek ödeme/kargo/SAP · zengin F10 onay/RFQ portal · Dynamic Pricing (U-015 kilitli).  
(Org/RFQ/F7 iskelet + QC/Shipment/return + KS-6 var; ödeme iadesi yok.)

### 12.5 Yeni session handoff

1. Oku: `AGENTS.md` → bu dosya **§2 + §12** → ADR-0013/0012/0014/0015 (Kabul).  
2. Sıradaki kod (açık talimat): F8/F9 veya F10 UI dilimleri.  
3. Yerel migrate güncel (`firmalar.0007`/`siparis.0004`); full suite bayat.  
4. B-01/B-06 Kabul (servis payı/KDV kapalı); K-014 storage yok.

*Son güncelleme: 2026-11-09 — F10 hierarchy + F7 API/entegrasyon iskeleti.*
