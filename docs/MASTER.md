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
**Yok:** Celery. **Var:** `finans` (F5), `kalite` (F6-010).  
**HTTP:** `admin/` + `/api/v1/` + `/buyer/` + `/ops/finance/` (DOĞRULANDI).

<!-- AUTO:apps -->
`INSTALLED_APPS` (koddan): `django.contrib.*` (7), `import_export`, `rest_framework`, `rest_framework.authtoken`, `tanimlar`, `firmalar`, `fiyatlama`, `urunler`, `stok`, `siparis`, `finans`, `kalite`, `api`
<!-- /AUTO:apps -->

### 2.3 Modül uygulama durumu (kod gerçeği)

| Alan | Kod durumu | Not |
|------|------------|-----|
| Firma / kullanıcı / RBAC / AuditOlay | **Tamamlanmış** | AUD-001 + AUD-001b (`ip_address`/`changes`) |
| Tanımlar / kur / kanal / PB | **Tamamlanmış** | |
| Katalog / eşleştirme / onay | **Tamamlanmış** | |
| Teklif SM / sözleşme K-007/008 | **Tamamlanmış** | |
| Fiyat motoru / PriceQuote / Lock | **Tamamlanmış** | Lock’ta `has_adet` yok |
| Warehouse / Movement / Balance | **Tamamlanmış** | F4 dilim 1–2 |
| StockReservation TTL/oversell | **Tamamlanmış** | F4-020/021/022 (lazy + command; §12.2) |
| Cart / CartLine | **Tamamlanmış** | F4-030/031 |
| Checkout (aday) | **Tamamlanmış** | F4-040/041 |
| Order / OrderLine | **Tamamlanmış** | F4-050…053 (iptal = stok IADE) |
| FX / hedge / cari / PI / credit / webhook | **Tamamlanmış (iskelet)** | ADR-0012; F5-010…032; F5-041; unpaid hak ediş=0 |
| QC QualityInspection SM | **KISMİ** | F6-010; ölçüm F6-011; shipment F6-020 |
| İnce PRE API | **Tamamlanmış** | PRE-001…005 (+ credit/finance/ops/webhook) |
| Ödeme provider / kargo / tam Prosperer API | **Uygulanmamış** | Fake payment adapter var; gerçek provider yok |

### 2.4 Veri modelleri

Alan düzeyinde ve otomatik: [DATA_DICTIONARY](DATA_DICTIONARY.md).

**Borç:** `Varyant.stok` / `TedarikciTeklif.stok_adet` kolonları duruyor ama **F4-070 yazma kapalı** (save freeze + admin readonly); truth = ledger. Kolon drop ayrı dilim.

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
| `kalite`: `inspection_servisi` | F6-010 QC SM | UYGULANDI |
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
Statik test sayısı (`def test_`): **453** — `api` 17 · `firmalar` 53 · `fiyatlama` 141 · `finans` 53 · `kalite` 5 · `siparis` 38 · `stok` 31 · `tanimlar` 20 · `urunler` 95
_Bu sayı koşu sonucu değildir; son suite koşusu aşağıda elle tutulur._
<!-- /AUTO:tests -->

**Son suite koşusu (elle):** birleşik **354 OK** (tarihsel 2026-11-09) — **bayat**; bu sync turunda full suite koşulmadı. Odaklı: F5 finans / F5-041 / AUD-001b / F5-032 / F6-010 yeşil.
`makemigrations --check`: temiz. **Yerel/dev migrate uygulandı** (2026-11-09: `firmalar.0006`, `urunler.0009`, `fiyatlama.0014–0015`, `kalite.0001`).

<!-- AUTO:migrations -->
| App | Migration sayısı | Son migration |
|-----|-----------------|---------------|
| `api` | 1 | `0001_pre_005_idempotency_record` |
| `firmalar` | 6 | `0006_aud_001b_ip_changes` |
| `fiyatlama` | 15 | `0015_f5_041_contract_release` |
| `finans` | 5 | `0005_f5_021_webhook_payload_blank` |
| `kalite` | 1 | `0001_f6_010_quality_inspection` |
| `siparis` | 3 | `0003_order_orderline` |
| `stok` | 3 | `0003_faz4_3_stock_reservation` |
| `tanimlar` | 3 | `0003_faz3_3_kur_index_rename` |
| `urunler` | 9 | `0009_f4_070_legacy_stock_readonly` |
<!-- /AUTO:migrations -->

> Not: `api.0001` yerel/dev `migrate` uygulandı; **üretim migrate ürün sahibi onayı olmadan yok.**

**HTTP yüzeyi** (`/admin/` + aşağıdaki ince PRE API; yazma endpoint'i yok):

<!-- AUTO:api_urls -->
| Yol | Ad |
|-----|----|
| `/api/v1/health/` | `api-health` |
| `/api/v1/me/` | `api-me` |
| `/api/v1/carts/me/` | `api-cart-mine` |
| `/api/v1/carts/<int:pk>/` | `api-cart-detail` |
| `/api/v1/checkouts/` | `api-checkout-create` |
| `/api/v1/bulk-orders/` | `api-bulk-order-create` |
| `/api/v1/orders/` | `api-order-list` |
| `/api/v1/orders/<int:pk>/` | `api-order-detail` |
| `/api/v1/credit/me/` | `api-credit-mine` |
| `/api/v1/credit/check/` | `api-credit-check` |
| `/api/v1/finance/me/` | `api-finance-mine` |
| `/api/v1/ops/finance/` | `api-ops-finance` |
| `/api/v1/ops/finance/cari/` | `api-ops-finance-cari` |
| `/api/v1/ops/finance/ledger/` | `api-ops-finance-ledger` |
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
| B-01 platform servis payı | KARAR BEKLİYOR (hukuk; kodlanmadı) |
| B-06 KDV | Ertelendi (proforma) |
| ADR-0012 (audit/FX/hedge/cari) | **Kabul** |
| PRE-005 Idempotency-Key + checkout POST | UYGULANDI · TEST EDİLDİ |
| Ödeme / tam Prosperer API | PLANLANDI |
| Prosperer özellik parity | DOĞRULANAMADI (hedef kıyas) |
| U-003…007, 009…011, U-013…015 | **Kabul** (2026-11-09, Emre; dış onaylılarda ürün sahibi override) — [BACKLOG](BACKLOG.md) |
| U-014 / U-015 / U-016 | **Kabul** (2026-11-09) |
| ADR-0001 doküman düzeni (U-016) | **Kabul** |
| B-01 / B-06 | Dokunulmadı (hukuk / ertelendi) |

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
| Sertifika kurum/no/dosya | PLANLANDI |
| Kur/metal zaman damgası + stale fail-closed | UYGULANDI |
| PriceQuote + PriceLock | UYGULANDI (sipariş bağ L-11 UYGULANDI) |
| Fiyat girdi izi (`hesap_girdisi`) | KISMİ (JSON var; UI yok) |
| Kör çoklu teklif pazaryeri | UYGULANDI |
| Seri/lot/batch, emanet/konsinye, depo transfer | PLANLANDI · U-008 |
| Üretim / özel sipariş / RFQ | PLANLANDI |
| Gram tolerans + QC | KISMİ — ADR-0013 Kabul; F6-010 SM; ölçüm F6-011 |
| Teslimat / uyuşmazlık | PLANLANDI |

---

## 12. Güncel proje durumu ve sıradaki adım

### 12.1 Özet

| Madde | Değer |
|-------|--------|
| Dal | `adim-1-ilerleme` |
| Faz | F4 ticaret **UYGULANDI** · F5 finans **KISMİ/UYGULANDI** · F6 QC **F6-010** |
| ADR | 0010–0013 **Kabul** — [indeks](decisions/README.md) |
| Test / migration / apps | Otomatik bloklar (§2.7); yerel migrate uygulandı (2026-11-09) |

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

### 12.3 SIRADA (kodda yok — uygulama sırası)

| Öncelik | ID | Ne | Bağımlılık / not |
|---------|-----|-----|------------------|
| **1** | F6-011 | Gram/ağırlık ölçüm + tolerans | F6-010; ADR-0013 F6-K3/K4 |
| **2** | F6-020 | Shipment + QC gate | F6-010; `lojistik` app |
| — | F5-022 | Tedarikçi hak ediş | U-006 (vade seçeneği hâlâ net değil) |
| — | F4-070b | Legacy stok kolon drop | Onaylandıysa ayrı dilim (RemoveField) |
| — | B-01 / B-06 | Platform pay / KDV | hukuk |
| — | U-014 / F10 | Account Hierarchy | **Kabul A**; uygulama ayrı ADR + talimat |
| — | CAP-PIYASA | Canlı altın/döviz beslemesi | kod yok; ADR-0008 B-04/B-05 |

### 12.4 Bilinçli kapsam dışı (şimdi yok)

Celery/Redis · gerçek ödeme provider · kargo carrier · tam Prosperer API · RFQ · EDI · org şube FK doldurma.  
(QC SM F6-010 var; ölçüm/shipment/kargo yok.)

### 12.5 Yeni session handoff

1. Oku: `AGENTS.md` → bu dosya **§2 + §12** → ADR-0013 (Kabul).  
2. Sıradaki kod: **F6-011** (gram ölçüm + tolerans motoru).  
3. Yerel migrate güncel; full suite bayat (istersen `--keepdb` suite).  
4. Açık ama kodlanmayan: F5-022 (vade kararı), F4-070b (RemoveField dilimi), B-01/B-06.

*Son güncelleme: 2026-11-09 — **handoff sync**: migrate uygulandı; docs_sync+DATA_DICTIONARY; CI suite’e finans/kalite; sıradaki **F6-011**.*
