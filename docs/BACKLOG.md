# İş havuzu (kanonik)

<!-- AUTO:backlog_count -->
Toplam iş/karar kartı (`### [ID]` başlığı): **149**
<!-- /AUTO:backlog_count -->

Kodda UYGULANDI olanlar: [MASTER](MASTER.md) §12.2. Kart durumları faz bazlıdır; çelişirse MASTER ve kod kazanır.

### [F10-001] Org/şube modeli ADR (Account Hierarchy)

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 (stratejik) · **Tip:** Product
- **Bağımlılıklar:** **U-014**; ADR-0003 Kabul metni değişmeden uygulanamaz
- **Amaç:** Firma içi hiyerarşi; tenant sınırı `Firma` kalır
- **Kanıt:** [ADR-0015](decisions/ADR-0015-account-hierarchy.md) **Kabul** (2026-11-09, Qubit plan)
- **Not:** F4 Order’da şube zorunlu olmaz; nullable rezerv dolduruldu (OH-3)

### [F10-010] Şube / org birimi modeli

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-001 / U-014
- **Kanıt:** `OrgBirimi`/`OrgUyeligi`; `Order`/`Cart.sube`; mig `firmalar.0007`/`siparis.0004`; `test_org_f10_010`

### [F10-011] Satın alma yetki matrisi genişlemesi

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Security
- **Bağımlılıklar:** F10-010
- **Kanıt:** `require_org_scope`; `manage_org` RBAC; rol string switch yok

### [F10-012] Harcama limiti motoru

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F10-011, Order
- **Kanıt:** `HarcamaLimiti` + `assert_order_limit` order create; `test_limit_onay_f10_012`

### [F10-013] Onay iş akışı (çok adımlı)

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-012, F4-050 (Order), F10-010 (org)
- **Audit:** her onay kararı (AuditOlay)
- **Kanıt:** `OnayTalebi` SM `onay_servisi`; audit her geçiş

### [F10-014] Onay kuyruğu UI

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** (minimal `/buyer/approvals/`; zengin F9 portal değil) · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F10-013
- **Kanıt:** `buyer_approval_ui` + selector; `test_approval_ui_f10_014` **5 OK**; admin salt-okunur duruyor

### [F10-020] RFQ / RFQLine / RFQMessage modelleri

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Catalog, Pricing
- **Kanıt:** `rfq_servisi` SM; mig `siparis.0004`; `test_rfq_f10_020`

### [F10-021] Katalog dışı ürün talebi

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-020
- **Kabul kriterleri:** Platform aracılı eşleştirme
- **Kanıt:** `RFQEslestirme` + `rfq_eslestirme_servisi` (aday/öner/onay/red); mig `siparis.0006`; `test_rfq_eslestirme_f10_021` **7 OK**; create UI F10-023
- **Karar (uygulama):** kural tabanlı skor + platform `approve_eslestirme` onayı; otomatik/AI bağlama yok; kör (tedarikçi SKU yok)

### [F10-022] Özel üretim / tasarım talep akışı

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-020, F6 QC bağ opsiyonel
- **Kabul kriterleri:** Revizyon geçmişi
- **Kanıt:** `RFQ.talep_tipi` + `RFQRevizyon`; `revizyon_ekle`; mig `siparis.0005`; `test_rfq_ozel_f10_022` **3 OK**

### [F10-023] RFQ buyer/supplier UI (maskeli)

- **Faz:** Faz 10
- **Durum:** **UYGULANDI** (buyer minimal; supplier UI yok) · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F10-020, F7 APIs
- **Kabul kriterleri:** Kimlik sızıntısı yok
- **Kanıt:** `buyer_rfq_ui` + `selectors.rfq`; `test_rfq_ui_f10_023` **4 OK**

### [F11-001] Raporlama veri modeli / read-model kararı

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Product
- **Bağımlılıklar:** Order+Finance veri
- **Kabul kriterleri:** ADR veya teknik not
- **Kanıt:** [NOTE-F11-001](decisions/NOTE-F11-001-raporlama-v1.md) RM-1…6; P-RM-* Product erteli (DRF/Mahsup/FE)

### [F11-010] Ticari raporlar (sipariş/ciro tenant kesitli)

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F11-001
- **Kabul kriterleri:** Çapraz tenant yok
- **Kanıt:** `rapor_servisi.ticari_siparis_ozet`; `test_rapor_f11_010_021` (F11-010 kısmı)

### [F11-011] Fiyat analitiği (quote/lock geçmişi)

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** PriceQuote, PriceLock
- **Gizlilik:** alıcıya maliyet yok
- **Kabul kriterleri:** Platform finans rolü
- **Kanıt:** `fiyat_analitik_servisi`; `test_fiyat_analitik_f11_011` **3 OK**

### [F11-012] Stok tahmin / ATP görünümü (kural tabanlı v1)

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F4-012
- **Kapsam dışı:** ML zorunluluğu
- **Kabul kriterleri:** Deterministik formül dokümante
- **Kanıt:** `atp_servisi` — `ATP = on_hand − reserved − blocked`; kör alıcı boş; `test_atp_f11_012` **4 OK**

### [F11-013] Bildirim otomasyonu kuralları

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Notification outbox (F4-090)
- **Kabul kriterleri:** Sipariş/QC olayında bildirim
- **Kanıt:** `order.created` (mevcut) + `qc.passed`/`qc.failed` (`inspection_servisi`) + `return.approved` (`return_servisi`); `test_notify_f11_013` **3 OK**
- **Not:** Handler iskelet (F4-090 default log); canlı push/email yok (Celery yok)

### [F11-014] Anomali tespiti (basit eşik)

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F11-010
- **Kabul kriterleri:** Audit + ops uyarı
- **Kanıt:** `anomali_servisi.ciro_esik_tara`; `test_anomali_f11_014` **3 OK**

### [F11-015] AI ürün eşleştirme asistanı (opsiyonel)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** Eşleştirme servisi, veri politikası
- **Kapsam dışı:** Otomatik onay
- **Kabul kriterleri:** İnsan onayı zorunlu; kör havuz bozulmaz
- **Karar formu:** [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) AI-1…4

### [F11-020] Smart Replenishment (kural tabanlı)

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F4-012, F4-050, F11-012
- **Amaç:** Stok eşiği / hız → önerilen sipariş (otomatik checkout yok)
- **Kabul kriterleri:** Öneri audit’li; tenant scope; birim karışmaz
- **Kanıt:** `replenishment_servisi.oneri_uret`; `test_replenishment_f11_020` **2 OK**

### [F11-021] Buyer Behavior Analytics

- **Faz:** Faz 11
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F4-050, F11-001
- **Amaç:** Alıcı firma kesitli sipariş/quote davranış özeti
- **Kabul kriterleri:** Tedarikçi kimliği/kör alan sızıntısı yok
- **Kanıt:** `rapor_servisi.alici_davranis_ozet`; `test_rapor_f11_010_021` **5 OK** (010+021)

### [CAP-COMPARE] Multi-Variant Comparison

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend/API
- **Bağımlılıklar:** Catalog API / buyer_quote; PRE
- **Amaç:** Alıcıya varyant özellik+fiyat (maskeli) karşılaştırma
- **Kabul kriterleri:** Maliyet/tedarikçi yok; F4’ü bloklamaz

### [CAP-PIYASA] Canlı kur beslemesi + dayanıklı fiyat kaynağı

- **Faz:** Pricing / Kur (MASTER §12.3 öncelik 0)
- **Durum:** **UYGULANDI** · ADR-0018 **Kabul** (2026-11-10) · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** ADR-0008/0010; `manage_kur`
- **Amaç:** Binance anlık + TCMB EOD; ürün→ayar→politika `fiyat_kaynagi`; LKG+banner; batch canlı senkron + manuel freeze (dry-run, atomik publish); negatif marj guardrail; çapraz kur sanity; Decimal yuvarlama net
- **Kabul kriterleri:** Soft uydurma/`0` yok; PriceQuote/Lock/OrderLine dokunulmaz; partial batch yasak; kör havuz maliyet sızıntısı yok
- **Geçici ref:** `real_data/` (GoldXT) — **kaldırıldı** (2026-11-10); özet ADR-0018 §GoldXT
- **Kanıt:** mig `tanimlar.0004` / `urunler.0011` / `fiyatlama.0019`; `kaynak_resolve` / `feed_adapters` / `fiyat_batch_servisi` / `guardrail_servisi`; `test_cap_piyasa_adr0018` (**8 OK** odaklı, 2026-11-10)

### [CAP-ALERT] Live Gold Price Alert

- **Faz:** Faz 9+
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** kur_servisi, F4-090 (outbox)
- **Amaç:** Kur eşiği bildirimi
- **Kabul kriterleri:** Stale kurda alert yok; F4 checkout’u bozmaz
- **Kanıt:** `KurAlertKurali` + `kur_alert_servisi` + admin + `evaluate_kur_alerts` (+ `process_outbox`); mig `tanimlar.0005`; `test_kur_alert_cap` **4 OK**

### [CAP-DYNPRICE] Dynamic Pricing (koşullu)

- **Faz:** Faz 9+ (karar U-015)
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Product/Backend
- **Bağımlılıklar:** **U-015**, ADR-0008/0010
- **Amaç:** Kanal/hacim/süre koşullu fiyat — yalnızca **yeni** quote üretiminde
- **Kabul kriterleri:** Mevcut PriceQuote/PriceLock/OrderLine snapshot değişmez
- **Karar formu:** [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) DYN-1…3

### [F12-001] Dil/i18n strateji ADR

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** —
- **Kabul kriterleri:** Ürün sahibi
- **Karar formu:** [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) I18N-1…4

### [F12-010] Katalog/UI çeviri altyapısı

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Backend/Frontend
- **Bağımlılıklar:** F12-001
- **Kabul kriterleri:** En az 2 locale smoke

### [F12-011] TRY dışı yuvarlama muhasebe doğrulaması uygulama

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** U-009 (ADR-0008 §6)
- **Kabul kriterleri:** PB bazlı quantize testleri
- **Karar formu:** [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) FXQ-1…3

### [F12-012] Ülke bazlı ticari kural motoru (iskelet)

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F12-001, vergi U-*
- **Kabul kriterleri:** Ülke yoksa fail-closed veya TR varsayılan (karar)

### [F12-013] Bölgesel entegrasyon adaptör slotları

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Integration
- **Bağımlılıklar:** F7-E02
- **Kabul kriterleri:** Registry genişletilebilir

### [F12-014] Partner/developer API programı

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** F7-E01, OpenAPI
- **Kabul kriterleri:** Partner key + scope; kör havuz

### [F4-001] Faz 4 ADR taslağı (stok üçlüsü + sipariş SM + PriceLock bağ)

- **Faz:** Faz 4
- **Durum:** **Kabul** (ADR-0011)
- **Dokümantasyon:** §6.4

### [F4-002] Dual stock alan envanteri ve deprecation planı

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** · **Öncelik:** P0 · **Tip:** Backend
- **Kanıt:** `stok/services/dual_stock_envanter.py`; Varyant/Teklif help_text; mig `urunler.0008`, `fiyatlama.0013`
- **Not:** Legacy alanlar ADET; GRAM’a kör migrate yok
- **Kapsam dışı:** Ledger (F4-011)

### [F4-010] Warehouse modeli + tenant scope

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** · **Öncelik:** P0 · **Tip:** Backend
- **Kanıt:** `stok.Warehouse`, `warehouse_servisi`, selector, admin salt; mig `stok.0001`; test 9 OK
- **Perm:** `manage_warehouse` / `manage_own_warehouse`

### [F4-011] StockMovement immutable ledger

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** · mig `stok.0002`
- **Kanıt:** `StockMovement`, `ledger_servisi.kaydet_hareket`; app immutability

### [F4-012] StockBalance projeksiyonu

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** unique (warehouse, teklif, birim); `available = on_hand − reserved − blocked`

### [F4-013] Stok düzeltme servisi (adjustment)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `ledger_servisi.duzeltme` — neden ≥5; perm + audit

### [F4-020] StockReservation modeli + TTL

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `StockReservation`, `reservation_servisi`; mig `stok.0003`; create/cancel/expire reserved-only; consume SATIS; ADET/GRAM karışmaz
- **Test:** `stok.tests.test_reservation_f4_020` (TTL/`now` enjekte)

### [F4-021] Rezervasyon concurrency (select_for_update)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `get_or_create_balance_locked` + available kontrolü; PG `TransactionTestCase` paralel 4×6/10 → 1 ok / 3 fail

### [F4-022] Rezervasyon expire görevi (iskelet)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Infrastructure
- **Bağımlılıklar:** F4-020; Celery opsiyonel (F8)
- **Kanıt:** `expire_stale_reservations` servis + `stok/management/commands/expire_stale_reservations`; lazy sweep `olustur_rezervasyon`; order create öncesi TTL süpürme (rollback'ten bağımsız); `stok/tests/test_reservation_expire_f4_022`
- **Kapsam dışı:** Tam Celery prod kurulumu (F8)

### [F4-030] Cart / CartLine modelleri

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `siparis.Cart` (OneToOne `alici_firma`), `CartLine`; mig `siparis.0001`; selector `CartNotFound`
- **Kabul:** Başka firma sepeti DoesNotExist (`get_cart_for_actor`)

### [F4-031] Sepete satır ekleme (quote/varyant bağ)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `cart_servisi.satir_ekle` — PriceQuote ref; birim tekliften; stok movement yok; `present_cart_line` kör
- **Test:** `siparis.tests.test_cart_f4_030` **10 OK**

### [F4-040] Checkout servisi

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `checkout_servisi.checkout` → PriceLock + StockReservation; `CheckoutAttempt`; mig `siparis.0002`
- **Kapsam dışı:** Payment; Order SM (F4-050)
- **Idempotency:** `(alici_firma, idempotency_key)` unique

### [F4-041] Checkout fail audit durable

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `record_audit_durable` + TransactionTestCase `test_fail_audit_survives`
- **Test:** `siparis.tests.test_checkout_f4_040` (odak 5 OK; cart+checkout 15 OK)

### [F4-050] Order / OrderLine + durum makinesi

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `Order`/`OrderLine`; `order_servisi.olustur_from_checkout`; mig `siparis.0003`
- **Kapsam:** Durum `OLUSTURULDU`/`IPTAL` (`iptal_siparis`); şube FK yok
- **Audit:** `order.create` success + durable fail
- **Org rezervi:** Tenant = `alici_firma` (zorunlu). İleride `sube`/`org_birimi` **nullable** FK — U-014/F10 olmadan doldurulmaz.
- **Test:** `siparis.tests.test_order_f4_050` **6 OK**

### [F4-051] PriceLock → Order bağlama + satır fiyat snapshot

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `OrderLine.price_lock` OneToOne (L-11); snapshot alanları immutable
- **Bağımlılıklar:** F4-050, ADR-0010 L-11
- **Kabul:** Kur değişimi geçmiş satırı etkilemez (snapshot kopya)

### [F4-052] Rezervasyonun siparişe tüketilmesi

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `tuket_rezervasyon` order create içinde; SATIS movement; idempotent yeniden create çift tüketmez
- **Bağımlılıklar:** F4-051, F4-020

### [F4-053] Sipariş iptal (stok iade hareketi; finans yok)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI**
- **Kanıt:** `order_servisi.iptal_siparis` → `StockMovement.IADE` + on_hand; audit `order.cancel`
- **Bağımlılıklar:** F4-052; U-004 finans kısmı hâlâ Blocked (ödeme iadesi yok)
- **Kapsam:** Stok iade; ödeme/cari yok
- **Test:** `siparis.tests.test_order_f4_053` **4 OK**

### [F4-060] Buyer cart/order API (ince)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Kanıt:** `GET /carts/me/`, `/carts/<id>/`, `/orders/`, `/orders/<id>/`; `presenters` kör; tedarikçi **403**
- **Test:** `api.tests.test_order_api_f4_060`

### [F4-061] Platform ops sipariş listesi API/admin

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Kanıt:** `OrderListView` + `scope_order_queryset` (`view_all`); admin `OrderAdmin` aynı selector; client `firma_id` yok sayılır
- **Test:** ops list + PRE cross-tenant 404

### [F4-062] Minimal buyer sepet/sipariş ekranı

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Frontend (Django session templates)
- **Bağımlılıklar:** F4-060
- **Kanıt:** `/buyer/` login + sepet + checkout→order + sipariş liste/detay; `_require_buyer` (tedarikçi/ops 403); `present_cart`/`present_order` kör havuz
- **Test:** `siparis.tests.test_buyer_ui_f4_062` **3 OK**
- **Kapsam dışı:** Portal (Faz 9); Playwright E2E; ops UI

### [F4-070] Legacy stok alanlarını read-only / kaldırma dilimi

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend — yazma kilidi (tarihsel); kolon drop → **F4-070b**
- **Bağımlılıklar:** F4-012, F4-002
- **Kanıt (F4-070):** `editable=False` + save freeze (sonra drop edildi); mig `urunler.0009` / `fiyatlama.0014`
- **Devam:** F4-070b UYGULANDI

### [F4-070b] Legacy stok kolon drop

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F4-070; ürün sahibi **Kabul** (2026-11-09)
- **Kanıt:** `Varyant.stok` + `TedarikciTeklif.stok_adet` RemoveField; `varyant_benzersiz_parca_stok` constraint drop; `dual_stock_envanter` silindi; `teklif_servisi` kopya yolu temiz; mig `urunler.0010` / `fiyatlama.0016` (`lock_timeout=2s`)
- **Veri kaybı:** legacy ADET sayaç kolonları silinir — truth zaten ledger
- **Test:** `stok.tests.test_legacy_stock_f4_070b` + warehouse/admin regresyon


### [F4-080] Quick Reorder (önceki siparişten)

- **Faz:** Faz 4 (Order sonrası)
- **Durum:** **UYGULANDI**
- **Kanıt:** `reorder_servisi.sepete_aktar`; test `siparis.tests.test_reorder_f4_080` **4 OK**
- **Bağımlılıklar:** F4-050, F4-051, F4-030
- **Davranış:** Güncel quote; ATP fail-closed; birim eşleşmesi; varsayılan sepet replace
- **Kapsam dışı:** Eski lock yeniden kullanım; Dynamic Pricing; HTTP API

### [F4-081] Bulk Order / CSV import

- **Faz:** Faz 4 (Order sonrası)
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F4-040, PRE-005 (idempotency), F4-020
- **Kanıt:** `siparis/services/bulk_servisi.py` — CSV `sku,miktar[,birim]`; satır hataları kısmi; geçerli satırlar → cart → checkout → Order; aynı `idempotency_key` replay; birim uyumsuz → hata (dönüşüm yok); `POST /api/v1/bulk-orders/`
- **Test:** `siparis.tests.test_bulk_f4_081` **4 OK**


### [F4-090] Transactional Outbox iskeleti (bildirim/olay)

- **Faz:** Faz 4.5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Infrastructure
- **Bağımlılıklar:** F4-050; audit/`domain_atomic` deseni
- **Kanıt:** `OutboxMessage` + `outbox_servisi.enqueue` (yalnız `domain_atomic`); `order.create` → `order.created`; `manage.py process_outbox`; Celery yok
- **Test:** `firmalar.tests.test_outbox_f4_090` **5 OK** (rollback siler; process idempotent)
- **Kapsam dışı:** Celery/Redis (F8); gerçek e-posta/webhook ürünü (F7-020)

### [F5-001] Finans ADR (ledger + ödeme SM)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Product
- **Kanıt:** ADR-0012 **Kabul** (F5-K1…K10); paket `finans`
- **Kapsam dışı:** Provider seçimi; F4 Cart/Order kesmek

### [F5-010] FinancialLedger / hareket modeli (append-only)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-001
- **Kanıt:** `finans.LedgerEntry` + `ledger_servisi.kaydet_hareket` / `contra_hareket`; app+QuerySet+PG trigger immutability; `finans.post_ledger` (PLATFORM_FINANCE/SUPER/ADMIN); idempotency `(firma, key)`
- **Test:** `finans.tests.test_ledger_f5_010` **9 OK**
- **Migration:** `finans.0001_f5_010_ledger_entry` (**prod migrate kullanıcı onayı**)
- **Not:** `fiyatlama` ikinci ledger yok (F5-K1)

### [F5-011] Cari hesap (firma bakiyesi projeksiyonu)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-010, U-005 **Kabul** (platform↔alıcı)
- **Kanıt:** `finans.CariHesap` + `cari_servisi`; ledger post → bakiye; `kredi_limiti`; selector tenant; alıcı başkasını görmez
- **Test:** `finans.tests.test_cari_f5_011` **4 OK**
- **Migration:** `finans.0003` (CariHesap)

### [F5-012] Order ↔ PaymentIntent bağlama

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F4-050, F5-010
- **Kanıt:** `PaymentIntent` + `payment_servisi.olustur_intent` / `tahsil_et`; SATIS borç + TAHSILAT; partial unique BASARILI/order; idempotency
- **Test:** `finans.tests.test_payment_f5_012` **5 OK**
- **Migration:** `finans.0003` (PaymentIntent)

### [F5-013] Finansal audit zorunlu alanlar

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Security
- **Bağımlılıklar:** F5-010, AUD-001
- **Kanıt:** `finans.services.finans_audit` — `amount`/`currency`/`order_ref` + actor (başarılı) + success; ledger + payment yolları bağlı; AuditOlay şema değişmedi
- **Test:** `finans.tests.test_finans_audit_f5_013` **4 OK** (finans suite **28 OK**)

### [AUD-001] AuditOlay immutability + IP / changes sertleştirme

- **Faz:** Çapraz
- **Durum:** **UYGULANDI** (çekirdek + AUD-001b, 2026-11-09)
- **Kanıt:** `AuditOlay.save/delete` + `QuerySet.update/delete` + `bulk_update` → `ValidationError`; create/`record_audit*` OK
- **Test:** `firmalar.tests.test_audit_aud_001` **5 OK**
- **AUD-001b:** `ip_address` + `changes` kolonları; `client_ip(request)` + `TRUSTED_PROXY_COUNT`; sidecar INSERT kolon sync; mig `firmalar.0006`
- **Test (b):** `firmalar.tests.test_audit_aud_001b` **4 OK**

### [SEC-001] Ortam ve API sertleştirme (prod öncesi)

- **Durum:** **UYGULANDI** (2026-11-09) — throttle, proxy env, TokenAuthentication, `.env.example`
- **Kalan işletim:** DB şifre rotasyon prosedürü (kod dışı)

### [OPS-001] CI + docs kapısı

- **Durum:** **UYGULANDI** (2026-11-09) — CI + `scripts/docs_sync.py --check`

### [FX-001] Açık HAS pozisyon servisi (stateless)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-001 / ADR-0012 Kabul
- **Kanıt:** `finans.services.fx_servisi.open_has_position`; interim locked = AKTİF lock `quote.gram` (F5-K6); unpaid=0; `HAS_POSITION_LIMIT` settings
- **Test:** `finans.tests.test_fx_hedge_f5` (over_limit + hedge)
- **Kapsam dışı:** Checkout gate (F5-K8); `has_adet` alanı

### [HEDGE-001] HedgeEntry append-only

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** FX-001 / F5-001
- **Kanıt:** `finans.HedgeEntry` + `hedge_servisi`; grams≠0; audit `firmalar`
- **Migration:** `finans.0002_f5_hedge_entry` (**prod migrate kullanıcı onayı**)
- **Test:** `finans.tests.test_fx_hedge_f5` **6 OK** (ledger ile birlikte finans **15 OK**)

### [F5-020] Ödeme sağlayıcı adapter arayüzü

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Integration
- **Bağımlılıklar:** F5-012
- **Kanıt:** `finans.payments` — `PaymentProviderPort` + `FakePaymentAdapter` + `get_payment_adapter`; `tahsil_et` charge→ledger; bilinmeyen provider / `force_fail` → ValidationError; secret yok
- **Settings:** `PAYMENT_PROVIDER` (default `fake`), `PAYMENT_FAKE_FORCE_FAIL`
- **Test:** `finans.tests.test_payment_adapter_f5_020` **5 OK**
- **Kapsam dışı:** Canlı banka; webhook (F5-021)

### [F5-021] Tahsilat kaydı + webhook iskeleti

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-020, PRE-idempotency
- **Kanıt:** `PaymentWebhookEvent` + `webhook_servisi.isle_webhook`; `POST /api/v1/payments/webhook/` (secret header); `payment.succeeded` → `tahsil_et(skip_provider=True)`; aynı `event_id` tek satır
- **Settings:** `PAYMENT_WEBHOOK_SECRET` (boşsa 401)
- **Migration:** `finans.0004` / `0005`
- **Test:** `finans.tests.test_webhook_f5_021` **4 OK**

### [F5-022] Tedarikçi hak ediş iskeleti (politika sonrası)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** U-006 **Kabul**, F5-010, F6-010
- **Kanıt:** `TedarikciHakEdis`; `hak_edis_servisi.kaydet_qc_pass` (QC PASS hook); `SUPPLIER_ACCRUAL_VADE_GUN` (default 0 → HAKEDILDI); `fx_servisi.unpaid_supplier_has` bağ; mig `finans.0006`
- **RBAC:** `manage_hak_edis` → PLATFORM_FINANCE (+ SUPER/ADMIN)
- **Test:** `finans.tests.test_hak_edis_f5_022` **5 OK**
- **Kapsam dışı:** üretim oranı / tutar sabitleme (`tutar` null)

### [F5-023] İade / mahsup hareketleri

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** U-004 **Kabul**, F6-030
- **Kanıt:** `mahsup_servisi.iade_mahsup` → LedgerEntry MAHSUP ALACAK (platform↔alıcı); `odeme_iadesi_yap` fail-closed (U-004)
- **Test:** `finans.tests.test_mahsup_f5_023` **3 OK**
- **Politika:** v1 **ödeme iadesi yok**; mahsup isteğe bağlı (onay sonrası)

### [F5-030] Buyer finans özeti API (maskeli)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-011, PRE-001, F5-040
- **Kanıt:** `buyer_finans_servisi.ozet_for_actor`; `GET /api/v1/finance/me/`; credit + payment_intents; `assert_masked` (komisyon/marj/tedarikçi yok)
- **Test:** `finans.tests.test_buyer_finans_f5_030` **4 OK**
- **Gizlilik:** komisyon/marj/ledger_entry yok

### [F5-031] Platform finans ops ekranı/API

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-010, PRE-001
- **Kanıt:** `ops_finans_servisi` + `GET /api/v1/ops/finance/`, `/cari/`, `/ledger/`; `view_all` zorunlu; client `firma_id` yok sayılır; alıcı/tedarikçi 403
- **Test:** `finans.tests.test_ops_finans_f5_031` **3 OK**

### [F5-040] Real-Time Credit Visibility

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-011, U-005, F4-050
- **Kanıt:** `credit_servisi.ozet_for_actor` / `assert_musait`; `GET /api/v1/credit/me/`, `POST /api/v1/credit/check/`; maskeli DTO; tedarikçi 403; limit aşımı 400
- **Test:** `finans.tests.test_credit_f5_040` **5 OK**
- **Kapsam dışı:** Checkout’a zorunlu bağ (opsiyonel helper hazır)

### [F5-041] Contract Release Plan

- **Faz:** Faz 5+
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** `FiyatSozlesmesi`, F4-050, F5-001
- **Amaç:** Sözleşmeli miktarın dönemsel serbest bırakılması (release ≠ yeni PriceQuote)
- **Kanıt:** `ContractReleasePlan` / `ContractReleaseEvent` + `release_servisi` (`olustur_plan` / `aktif_et` / `serbest_birak` / `kapat`); yalnız AKTIF ALICI sözleşme; `manage_sozlesme`; Quote/Lock’a yazmaz; mig `fiyatlama.0015`
- **Test:** `fiyatlama.tests.test_contract_release_f5_041` **6 OK**
- **Tüketim:** → **F5-041b**

### [F5-041b] Contract Release sipariş tüketimi

- **Faz:** Faz 5+
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F5-041, F4-050/053
- **Amaç:** `kullanilabilir = serbest − (TUKETIM − IADE)`; order create tüketir, iptal iade eder; Quote/Lock yazılmaz
- **Kanıt:** `ContractReleaseConsumption` append-only; `tuket_order_line` / `iade_order_line`; `order_servisi` bağ; mig `fiyatlama.0018`
- **Test:** `siparis.tests.test_contract_release_consume_f5_041b` **4 OK** (+ F5-041 **6 OK**)

### [F5-032] Finans UI (RBAC finance)

- **Faz:** Faz 5
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Frontend (Django session templates)
- **Bağımlılıklar:** F5-010, F5-030, F5-031
- **Kanıt:** `GET /buyer/finance/` (`BuyerFinanceView` + `buyer_finans_servisi`, maskeli); `GET /ops/finance/` (`OpsFinanceView` + `ops_finans_servisi`, `view_all`); tedarikçi/alıcı ops 403
- **Test:** `finans.tests.test_finance_ui_f5_032` **4 OK**
- **Kapsam dışı:** Portal (F9); Playwright E2E

### [F6-001] QC ADR (tolerans, gram farkı)

- **Faz:** Faz 6
- **Durum:** **Kabul** (2026-11-09, ürün sahibi) · **Tip:** Product
- **Bağımlılıklar:** F4-050, U-008, U-002
- **Dokümantasyon:** [ADR-0013](decisions/ADR-0013-faz6-qc-lojistik.md) **Kabul** — F6-K1…K12 + soru cevapları
- **Kod kapısı:** F6-010+ açık

### [F6-010] QualityInspection modeli + SM

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-001 / ADR-0013 Kabul
- **Kanıt:** `kalite.QualityInspection` SM (`TASLAK→OLCUMDE→PASS|FAIL|IPTAL`); `shipment_blok` FAIL’de True; `order_shipment_blocked`; `manage_qc`/`view_qc`/`manage_qc_override` + PLATFORM_QUALITY seed; mig `kalite.0001`
- **Audit:** `kalite.qc.*` geçişleri
- **Test:** `kalite.tests.test_inspection_f6_010` **5 OK**
- **Kapsam dışı:** Ölçüm/tolerans motoru (F6-011); Shipment create gate (F6-020)

### [F6-011] Gram/ağırlık ölçüm kaydı

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-010, Decimal
- **Kanıt:** `QualityMeasurement` append-only; `tolerans_motoru` (bağıl ±% + abs taban); `olcum_servisi.kaydet_olcum` → sapma otomatik FAIL; override `manage_qc_override` + gerekçe≥10; settings `QC_GRAM_TOLERANCE_PCT/ABS`; mig `kalite.0002`
- **Test:** `kalite.tests.test_olcum_f6_011` **11 OK** (+ F6-010 güncel PASS ölçüm zorunlu)
- **Kabul kriterleri:** Tolerans dışı otomatik fail (konfig) — karşılandı

### [F6-012] Taş sertifika belge bağı (metadata)

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** Document domain iskelet (bu dilimde kuruldu)
- **Kanıt:** app `belgeler` — `Document` + `TasSertifikaBelgesi` (UrunTasi XOR TeklifTas); `document_servisi`; tenant selector; binary yok (`storage_key`); mig `belgeler.0001`
- **RBAC:** `manage_document` → PLATFORM_CATALOG + TEDARIKCI_SAHIP/YONETICI
- **Test:** `belgeler.tests.test_document_f6_012` **6 OK**
- **Kabul kriterleri:** Tenant’lı belge erişimi — karşılandı

### [F6-020] Shipment modeli + SM

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-010/011 (QC pass)
- **Kanıt:** app `lojistik` + `Shipment` SM (`TASLAK→HAZIR→YOLDA→TESLIM|IPTAL`); create gate `order_shipment_blocked`; `manage_shipment` + PLATFORM_LOGISTICS seed; mig `lojistik.0001`
- **Test:** `lojistik.tests.test_shipment_f6_020` **6 OK**
- **Kabul kriterleri:** QC fail/blok iken create ValidationError — karşılandı
- **Kör havuz:** alıcı/tedarikçi kimlik alanı yok (platform sevkiyat)

### [F6-021] Carrier adapter arayüzü + fake

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Integration
- **Bağımlılıklar:** F6-020
- **Kanıt:** `lojistik.carriers` port/fake/factory; `sevk_et` boş takip → fake label; settings `CARRIER_PROVIDER` / `CARRIER_FAKE_FORCE_FAIL`; bilinmeyen provider ValidationError
- **Test:** `lojistik.tests.test_carrier_f6_021` **5 OK**
- **Kabul kriterleri:** Fail-closed; secret yok kodda — karşılandı

### [F6-022] Teslimat kanıtı (POD) kaydı

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-020
- **Kanıt:** `ProofOfDelivery` append-only; `pod_servisi.kaydet_pod`; `SHIPMENT_POD_REQUIRED` (default False); `teslim_et` gate; mig `lojistik.0002`
- **Test:** `lojistik.tests.test_pod_f6_022` **4 OK**
- **Kabul kriterleri:** POD olmadan teslim opsiyonel politika — karşılandı

### [F6-023] Buyer sevkiyat takip API (maskeli)

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-020, PRE
- **Kanıt:** `GET /api/v1/shipments/` + detail; `buyer_shipment_servisi.present_shipment` (tedarikçi yok); tenant 404
- **Test:** `api.tests.test_shipment_api_f6_023` **3 OK**
- **Kabul kriterleri:** Tedarikçi kimliği yok — karşılandı

### [F6-030] Return/Dispute SM

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** U-004 **Kabul**, F6-020
- **Kanıt:** `ReturnRequest`/`ReturnLine` SM `TASLAK→INCELENIYOR→ONAYLANDI|REDDEDILDI|IPTAL`; TESLIM sevkiyat gate; `manage_return`; mig `lojistik.0003`
- **Test:** `lojistik.tests.test_return_f6_030` **5 OK** (F6-031 ile)
- **Politika:** v1 stok-only SM; mahsup F5-023 ayrı / isteğe bağlı

### [F6-031] İade stok hareketi

- **Faz:** Faz 6
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** F6-030, F4-011
- **Kanıt:** `return_servisi.onayla` → `StockMovement.IADE` + `on_hand` artışı; kısmi miktar
- **Test:** `test_return_f6_030` happy path

### [F6-032] Platform uyuşmazlık ops kuyruğu

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F6-030
- **Kabul kriterleri:** RBAC ops

### [SEC-OBJECT-DRF] Object-level DRF yetki matrisi

- **Faz:** API / Güvenlik
- **Durum:** **UYGULANDI** (ADR-0019 **Kabul** + OL-11) · **Öncelik:** P1 · **Tip:** Security/Product
- **Bağımlılıklar:** ADR-0003, API-B1…B7, F8-007
- **Amaç:** Rol × kaynak × işlem dondurma; IDOR/tenant/kör havuz
- **Kapsam dışı:** Rapor/anomali HTTP; Mahsup HTTP; FE; yeni endpoint
- **Kabul kriterleri:** [ADR-0019](decisions/ADR-0019-object-level-drf.md) OL-1…11 **A**
- **Kanıt:** `api.permissions` (`IsBuyerCommerceWrite` / `Has*ObjectAccess`); `test_object_level_adr0019` **6 OK** + F8-007 **5 OK**

### [PRE-001] DRF bağımlılık pin + INSTALLED_APPS

- **Faz:** PRE
- **Durum:** **UYGULANDI**
- **Kanıt:** `djangorestframework==3.18.3` requirements; `rest_framework` + `api` INSTALLED_APPS
- **Kapsam dışı:** Celery

### [PRE-002] `/api/v1/health` + auth iskeleti

- **Faz:** PRE
- **Durum:** **UYGULANDI**
- **Kanıt:** `GET /api/v1/health/` public; `GET /api/v1/me/` unauth **401**
- **Auth:** Basic (+ Session); AnonymousUser session 401 düzeltmesi `api.authentication`

### [PRE-003] API permission + tenant test iskeleti

- **Faz:** PRE
- **Durum:** **UYGULANDI**
- **Kanıt:** cart/order detay çapraz tenant **404**; `?firma_id=` yok sayılır
- **Test:** `api.tests.test_pre_api` tenant sınıfı

### [PRE-004] OpenAPI şema yayını (taslak)

- **Faz:** PRE
- **Durum:** **UYGULANDI**
- **Kanıt:** `GET /api/v1/schema/` public OpenAPI

### [PRE-005] Idempotency-Key sözleşme notu + middleware iskelet

- **Faz:** PRE
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Backend
- **Bağımlılıklar:** PRE-002
- **Kanıt:** `IdempotencyKeyMiddleware`; `IdempotencyRecord` (`api.0001`); mixin + `POST /api/v1/checkouts/` → `checkout_servisi`; replay aynı gövde; farklı gövde 409
- **Test:** `api.tests.test_pre_005_idempotency` **3 OK**


### [F7-010] Buyer API yüzey standardı

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003, F4-060
- **Kanıt:** `assert_masked` + `/api/v1/catalog/`; `present_order` maske; `test_f7_api_std`

### [F7-011] Supplier API yüzey standardı

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003
- **Kanıt:** `/api/v1/supplier/offers|stock/`; alıcı kimliği yok

### [F7-012] Admin/operations API

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003, view_all
- **Kanıt:** `/api/v1/ops/orders/summary/`; view_all zorunlu

### [F7-013] Rate limiting

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** PRE-002
- **Kanıt:** buyer/supplier/ops throttle scopes + mevcut 429 test

### [F7-014] Hata sözleşmesi (problem+json veya proje standardı)

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-002
- **Kanıt:** `problem_exception_handler` (`type`/`title`/`status`/`detail`)

### [F7-015] API versioning politikası

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Product
- **Bağımlılıklar:** PRE-004
- **Kanıt:** `/api/v1/` sabit; `settings.API_VERSION=v1` (yeni major yok)

### [F7-020] Webhook outbox modeli

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Order events
- **Kanıt:** `WebhookDelivery` + `webhook_delivery_servisi`; `test_webhook_f7_020`

### [F7-021] ERP adapter iskeleti (SAP hedefi)

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F7-020
- **Kapsam dışı:** Canlı SAP
- **Kanıt:** `integrations.erp.FakeERPAdapter` roundtrip

### [F7-022] Ödeme/lojistik connector kayıt defteri

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F5-020, F6-021
- **Kanıt:** `integrations.ConnectorRegistry` (payment+carrier+erp+crm)

### [F7-023] CRM sync iskeleti

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Integration
- **Bağımlılıklar:** F7-020
- **Kanıt:** `FakeCRMAdapter` + `CRM_SYNC_ENABLED` opt-in

### [F7-024] EDI / Punchout iskeleti

- **Faz:** Faz 7
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** PRE-*, F7-010, F4-050, kör havuz kuralları
- **Kapsam dışı:** Tam SAP sertifikasyonu
- **Kanıt:** `process_inbound_punchout` maske + idempotent; `test_integrations_f7_021`

### [F8-001] CI pipeline (lint + test PG)

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** —
- **Kabul kriterleri:** PR’da test koşar
- **Kanıt:** `.github/workflows/ci.yml` — docs_sync, `manage.py check`, makemigrations, PG suite (3.12/3.14)

### [F8-002] Structured logging standardı

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** —
- **Kabul kriterleri:** request_id; secret log yok
- **Kanıt:** `RequestIdMiddleware` + `config.logging_utils`; `test_logging_f8_002`

### [F8-003] Hata izleme (Sentry veya eşdeğer) bağlama planı

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** (kod) · staging event **DOĞRULANAMADI** · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** F8-002
- **Kabul kriterleri:** staging’de event görülür
- **Kanıt:** `sentry-sdk==2.69.1`; `config/sentry_init.py` + settings DSN opt-in; `test_sentry_f8_003` **3 OK**; RUNBOOK §11

### [F8-004] Backup/restore runbook

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** (şablon; prod prova **DOĞRULANAMADI**) · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** PostgreSQL
- **Kabul kriterleri:** Dokümanlı restore tatbikatı
- **Kanıt:** RUNBOOK §7

### [F8-005] Secret yönetimi kontrol listesi

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** —
- **Kabul kriterleri:** `.env` repo dışı; rotation notu
- **Kanıt:** RUNBOOK §9 + `.env.example`

### [F8-006] Performans smoke (quote/lock/order kritik yollar)

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F4-050
- **Kabul kriterleri:** Baseline raporu
- **Kanıt:** `api.services.perf_smoke` + `test_perf_smoke_f8_006` **1 OK** (quote/lock/cart_checkout soft ≤30s)

### [F8-007] Güvenlik test paketi (tenant/IDOR regresyon)

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** API yüzeyleri
- **Kabul kriterleri:** Checklist yeşil
- **Kanıt:** `api.tests.test_security_f8_007` **5 OK**

### [F8-008] Operasyon runbook (deploy/migrate)

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** (şablon) · **Öncelik:** P2 · **Tip:** Infrastructure
- **Bağımlılıklar:** F8-001
- **Kabul kriterleri:** Adım adım doküman
- **Kanıt:** RUNBOOK §10

### [F8-009] Rate limit prod konfig

- **Faz:** Faz 8
- **Durum:** **UYGULANDI** · **Öncelik:** P2 · **Tip:** Infrastructure
- **Bağımlılıklar:** F7-013
- **Kabul kriterleri:** Ortam bazlı ayar
- **Kanıt:** `DRF_THROTTLE_*` env + `.env.example`

### [F9-001] Frontend teknoloji ADR (Next.js vs alternatif)

- **Faz:** Faz 9
- **Durum:** **Supersede zinciri** — [ADR-0016](decisions/ADR-0016-faz9-frontend.md) Supersede → [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md) **Taslak** · **Öncelik:** P1 · **Tip:** Product
- **Bağımlılıklar:** PRE-001 / F7
- **Kabul kriterleri:** ADR-0017 ürün sahibi **Kabul** (NX-1…12)
- **Kanıt:** 0016 Kabul 2026-11-09 sonra aynı gün Supersede; 0017 Taslak (Next.js + API B0–B7)

### [API-B0] Next.js API boşluk analizi

- **Faz:** API readiness
- **Durum:** **UYGULANDI** · **Öncelik:** P0 · **Tip:** Analysis
- **Bağımlılıklar:** F7
- **Kanıt:** 11 madde puan + uç envanteri (oturum B0; kod yok)

### [API-B1] Çekirdek API standartları

- **Faz:** API readiness
- **Durum:** **Kabul** (ürün sahibi Qubit, 2026-11-09) · **Öncelik:** P0 · **Tip:** API
- **Bağımlılıklar:** API-B0, NX-1/NX-2
- **Kanıt:** 28 odaklı OK; CORS erteli; ADR-0017 Taslak (NX-1/2 madde Kabul)

### [API-B2] Alıcı ticaret HTTP

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P0 · **Tip:** API
- **Bağımlılıklar:** API-B1 Kabul
- **Kapsam:** katalog/sepet/quote/lock/checkout/sipariş/iptal/reorder + `allowed_actions` + sızıntı testleri
- **Kanıt:** `api.tests.test_api_b2_buyer_commerce` (+ order/pre005 regresyon) **11 OK** odaklı
- **Concurrency:** `api.tests.test_api_b2_concurrency` PG TransactionTestCase **7 OK** (Kabul)

### [API-B3] Alıcı finans/lojistik HTTP

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P1 · **Tip:** API
- **Bağımlılıklar:** API-B2 Kabul
- **Kapsam:** credit/finance/cari/ledger/payment intent + sevkiyat allowed_actions + iade HTTP + ops payments; maske; idempotency
- **Kanıt:** `api.tests.test_api_b3_finance_ops` **10 OK**
- **Not:** Buyer iade oluşturma yok (`manage_return` — bilinçli iş kuralı)

### [API-B4] Kurumsal HTTP

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P1 · **Tip:** API
- **Bağımlılıklar:** API-B3 Kabul, F10
- **Kapsam:** onay / RFQ (+revizyon) / org — mevcut F10 servisleri; icat yok
- **Kanıt:** `api.tests.test_api_b4_enterprise` **11 OK** ([MASTER](MASTER.md) §12.1b)

### [TECH-OPENAPI-01] OpenAPI path çift `/api/v1` önek

- **Faz:** API readiness · **Durum:** **UYGULANDI** (B3 sonrası bakım) · **Öncelik:** P2 · **Tip:** Docs/API
- **Kök neden:** `SchemaGenerator(url="/api/v1/")` + ROOT_URLCONF `path("api/v1/", …)` → çift önek
- **Çözüm:** `api_urlpatterns` + `url="/api/v1/"` (`scripts/export_openapi.py`, `api/urls.py` schema_view)
- **Kanıt:** export sonrası `double_prefix=0`; canlı `/api/v1/*` değişmedi
- **Not:** NX-4 madde **Kabul** (Qubit, 2026-11-09)

### [TECH-NX-CONTRACT-01] NX-3…12 kod kanıt matrisi + problem+json media type

- **Faz:** API readiness · **Durum:** **UYGULANDI** · **Öncelik:** P0 · **Tip:** API/Docs
- **Bağımlılıklar:** API-B7 Kabul; ADR-0017 Taslak
- **Kapsam:** Hata yanıtlarında `Content-Type: application/problem+json` (DRF `accepted_renderer`); ADR-0017 NX-3…12 satır satır kod kanıtı; odaklı smoke test
- **Kabul kriterleri (kod):** `test_api_nx_contract` **4 OK**; OpenAPI drift yok
- **Not:** NX-3…12 madde **Kabul** (Qubit, 2026-11-09); ADR bütünü **Taslak** kalır
- **Kanıt:** `api.exception_handler.ProblemJSONRenderer`; [ADR-0017](decisions/ADR-0017-nextjs-api-sozlesmesi.md)

### [API-B5] Ops API yüzeyi

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P1 · **Tip:** API
- **Bağımlılıklar:** API-B4 **Kabul**
- **Kapsam:** `/api/v1/ops/inspections/*` (QC SM + ölçüm) + `/api/v1/ops/shipments/*` (oluştur/geçiş/POD); `manage_qc` / `manage_shipment`; Idempotency-Key; NX-2
- **Kanıt:** `api.tests.test_api_b5_ops` **7 OK**
- **Not:** Finans/iade buyer+ops B3’te; buyer `GET /shipments/` B3’te kaldı

### [API-B6] Tedarikçi API yüzeyi

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P1 · **Tip:** API
- **Bağımlılıklar:** API-B5 **Kabul** ([MASTER](MASTER.md) §12.1b)
- **Kapsam:** `/supplier/offers/*` (submit/deactivate/versions) + `/supplier/stock/adjustments/` + `/supplier/rfqs/*` (ters kör; mesaj/revizyon); mevcut `teklif_servisi` / `ledger_servisi` / `rfq_servisi`
- **Kanıt:** `api.tests.test_api_b6_supplier` **3 OK**

### [API-B7] API dondurma / frontend-ready

- **Faz:** API readiness · **Durum:** **Kabul** (Qubit 2026-11-09) · **Öncelik:** P1 · **Tip:** Docs/API
- **Bağımlılıklar:** API-B2…B6 **Kabul**
- **Kapsam:** `docs/api/openapi-v1.json` (koddan üret + `--check`); [API_CONTRACT.md](API_CONTRACT.md) (yetki/sızıntı matrisi + frontend checklist); B1–B6 path dondurma
- **Kanıt:** `api.tests.test_api_b7_openapi` **1 OK**; `python scripts/export_openapi.py --check` (çift önek 0; 81 path)

### [NX-FE] Next.js `frontend/` iskeleti

- **Faz:** Faz 9 / Experience · **Durum:** **UYGULANDI** (2026-11-09) · **Öncelik:** P0 · **Tip:** Frontend
- **Bağımlılıklar:** API-B7 **Kabul**; NX-1…12 madde **Kabul**
- **Kapsam:** App Router + TS + Tailwind v4; `next.config` `/api/v1` → Django rewrite; `lib/api` session+CSRF; `/` health/me smoke; `/login`; tasarım dokümanları `frontend/docs`
- **Kapsam dışı:** shadcn tam kit, katalog/sepet portal, supplier UI
- **Kanıt:** `frontend/` · `npm run lint` + `npm run build` OK · [MASTER](MASTER.md) §12.2

### [NX-ARCH] Feature/domain frontend mimarisi

- **Faz:** Faz 9 / Experience · **Durum:** **UYGULANDI** (2026-11-09) · **Öncelik:** P0 · **Tip:** Frontend
- **Bağımlılıklar:** NX-FE
- **Kapsam:** `src/features/<app>` (components/types/services/hooks/schemas) + `src/app/(portal)/<domain>` (page/loading/error/_components); `auth` feature; `docs/FRONTEND_ARCHITECTURE.md`
- **Kanıt:** 10 domain route + lint/build OK

### [NX-SHELL] Application shell + shadcn temel

- **Faz:** Faz 9 / Experience · **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** NX-FE, NX-ARCH
- **Kabul kriterleri:** Nav shell; light/dark; Button/Input/Dialog temel; kör havuz UI kuralları

### [F9-010] Buyer dashboard iskeleti (Django HTML miras)

- **Faz:** Faz 9
- **Durum:** **UYGULANDI** (Django `/buyer/` miras; Next portal değil) · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F9-001, F7-010
- **Kabul kriterleri:** Auth + tenant context
- **Kanıt:** `buyer_dashboard_servisi` / `BuyerHomeView`; `test_buyer_dashboard_f9_010`
- **Not:** Next ürün portalı ayrı (FE kapısı)

### [F9-011] Katalog arama/browse UI

- **Faz:** Faz 9
- **Durum:** **UYGULANDI** (Django `/buyer/catalog/` miras; Next portal değil) · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F9-010, search API
- **Gizlilik:** kör
- **Kabul kriterleri:** Maliyet sızıntısı yok
- **Kanıt:** `urunler.services.buyer_katalog_servisi` / `siparis.views.buyer_catalog_ui`; `test_buyer_catalog_f9_011`

### [F9-012] Sepet/sipariş portal akışı

- **Faz:** Faz 9
- **Durum:** **Ertelendi / iptal yönü** (ADR-0016 Supersede; Next.js + API-B2) · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F4-062, F7-010
- **Not:** Yeni Django HTML polish yok; mevcut `/buyer/` kalır

### [F9-013] Supplier dashboard + teklif yönetimi UI

- **Faz:** Faz 9
- **Durum:** **Ertelendi** → Next.js / API-B6 · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F7-011
- **Kabul kriterleri:** Alıcı kimliği görünmez

### [F9-014] Stok/teslimat görünümü (rol bazlı)

- **Faz:** Faz 9
- **Durum:** **Ertelendi** → Next.js · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F4-012, F6-023
- **Kabul kriterleri:** Rol kesiti doğru

### [F9-015] Finansal self-service (alıcı)

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F5-030
- **Kabul kriterleri:** Maskeli özet

### [F9-016] Responsive + PWA temel

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F9-010
- **Kabul kriterleri:** Mobil smoke

### [F9-017] Self-service profil/adres

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** firmalar adres API
- **Kabul kriterleri:** Başka firma adresi IDOR yok

### [U-001] ADR-0010 PriceLock varsayımları (L-01…L-11)

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-08) — L-01…L-10; L-11 F4-051 **UYGULANDI**
- **Etkilenen:** PriceLock, OrderLine

### [U-002] Stok ölçü birimleri ve tolerans

- **Faz:** Karar
- **Durum:** **Kabul A** (2026-11-08)
- **Uygulama:** `stok.services.birim` — SABIT_PARCA→ADET; METAL/GRAM→GRAM; dönüşüm yok
- **Açık netlik:** Aynı depoda farklı birimler **ayrı balance** (sonraki dilim); legacy ADET alanları GRAM’a çevrilmez
- **QC tolerans:** Faz 6

### [U-003] KDV / vergi davranışı

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, ürün sahibi Emre; override — Onaylayacak: mali müşavir + ürün sahibi)
- **Konu:** Vergi hesaplama, saklama, gösterim
- **Etkilenen:** Pricing, Order, Finance (B-06 erteli)
- **Seçenekler:** Proforma devam / KDV motoru / dış e-fatura
- **Önerilen:** Faz 4’te vergi yok (mevcut B-06); ayrı ADR
- **Karar:** Önerilen — vergi yok / proforma; KDV motoru ayrı ADR; **B-06 erteli kalır**
- **Onaylayacak:** Mali müşavir + ürün sahibi

### [U-004] İade / iptal finansal kuralları

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: finans + hukuk)
- **Konu:** İade tutarı, stok, mahsup
- **Etkilenen:** Faz 5–6
- **Seçenekler:** Tam iade / kısmi / stok-only iptal
- **Önerilen:** Yok — uzman
- **Karar:** Önerilen “Yok” — seçenek sabitlenmedi; stok-only iptal (F4-053) bilinçli; ödeme iadesi uzman sonrası
- **Onaylayacak:** Finans + hukuk

### [U-005] Cari hesap ve muhasebe politikası

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: mali müşavir)
- **Konu:** Cari bakiyenin ticari anlamı; kapanış; kredi limiti tarafları
- **Etkilenen:** Faz 5 (F5-010/011); ADR-0012 Prompt 4
- **Seçenekler:** Basit cari / tam muhasebe entegrasyonu; **taraflar:** platform↔alıcı vs tedarikçi↔alıcı (Medusa supplier→buyer kopyası kör havuzda şüpheli)
- **Önerilen:** Basit cari v1 + ERP sonra; paket `finans` — `fiyatlama` içine ikinci ledger **yok**
- **Karar:** Önerilen — taraflar **platform↔alıcı**; tedarikçi↔alıcı sabitlenmez
- **Onaylayacak:** Mali müşavir
- **Firma alan uyarısı:** `Firma.ad` / `alici_mi`/`tedarikci_mi` — Medusa `isim`/`firma_tipi` yok (DOĞRULANDI)

### [U-013] FX / HAS pozisyon ve hedge politikası

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: ürün sahibi + finans)
- **Konu:** “Kilitli müşteri HAS” tanımı (PriceLock’ta `has_adet` yok); limit aşımında onay kapısı; hedge muhasebesi
- **Etkilenen:** FX-001, HEDGE-001, checkout gate (F4-040 sonrası), U-009
- **Seçenekler:** Quote.gram toplamı / metal net HAS / TRY÷kur türevi (türev yasak önerilmez)
- **Önerilen:** F5-001 ile birlikte; F4 Cart’ı bloklamaz
- **Karar:** Önerilen — `locked_customer` = AKTİF PriceLock → `quote.gram`; `has_adet` yok; checkout gate ayrı (F5-K8)
- **Onaylayacak:** Ürün sahibi + finans

### [U-006] Tedarikçi ödeme vadesi ve hak ediş

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: ürün sahibi + finans)
- **Konu:** Ne zaman / nasıl hak ediş
- **Etkilenen:** Faz 5
- **Seçenekler:** Teslim sonrası N gün / QC pass / peşin
- **Önerilen:** Yok
- **Karar:** Önerilen “Yok” — vade/hak ediş seçeneği sabitlenmedi; F5-022 kodu ayrı talimat + finans teyidi
- **Onaylayacak:** Ürün sahibi + finans

### [U-007] Platform komisyonu / servis bedeli (B-01)

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: hukuk + ürün sahibi)
- **Konu:** Görünür/gizli hizmet payı
- **Etkilenen:** Pricing, Finance, hukuk
- **Seçenekler:** Kodlama yok / görünür satır / gizli yedirme
- **Önerilen:** Hukuk öncesi **kodlama yok** (mevcut)
- **Karar:** Önerilen — **kodlama yok**; **B-01 açık kalır** (hukuk görüşü)
- **Onaylayacak:** Hukuk + ürün sahibi

### [U-008] Konsinye / emanet mülkiyet ve sorumluluk

- **Faz:** Karar
- **Durum:** **Kabul** — Faz 4 kapsam dışı (2026-11-08)
- **Uygulama:** Warehouse yalnız platform/tedarikçi sahibi

### [U-009] Metal/kur ticari referans ve TRY dışı yuvarlama

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: finans)
- **Konu:** Referans fiyat; quantize
- **Etkilenen:** Pricing, Finance
- **Seçenekler:** Mevcut 0.01 HALF_UP geçici / PB bazlı
- **Önerilen:** Muhasebe doğrulaması sonrası
- **Karar:** Önerilen — mevcut 0.01 HALF_UP geçici devam; PB bazlı yuvarlama muhasebe sonrası
- **Onaylayacak:** Finans

### [U-010] Hukuki belge ve sözleşme gereklilikleri

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: hukuk)
- **Konu:** Proforma, sipariş formu, mesafeli satış vb.
- **Etkilenen:** Checkout, Document
- **Seçenekler:** —
- **Önerilen:** Yok
- **Karar:** Önerilen “Yok” — belge seti hukuk listesi gelene kadar sabitlenmedi; checkout’ta ek zorunlu belge yok
- **Onaylayacak:** Hukuk

### [U-011] Alıcı fiyat kırılımı görünürlüğü (B-02 genişleme)

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: hukuk)
- **Konu:** Satır kırılımı hukuk onayı
- **Etkilenen:** Pricing UI/API
- **Seçenekler:** Toplam only (mevcut) / kısmi kırılım
- **Önerilen:** Mevcut A
- **Karar:** Önerilen A — alıcı yüzeyi yalnız toplam (+ gram başı); kırılım yok
- **Onaylayacak:** Hukuk

### [U-012] Faz 4 HTTP yüzeyi: yalnız servis+admin mi, PRE-API zorunlu mu?

- **Faz:** Karar
- **Durum:** **Kabul A** — ince PRE-API (2026-11-08); uygulama PRE diliminde

### [U-014] Account Hierarchy vs ADR-0003 (tek firma + tek rol)

- **Faz:** Karar (uygulama F10)
- **Durum:** **Kabul** (2026-11-09, ürün sahibi Emre) — seçenek **A**
- **Konu:** Şube/org üyeliği; kullanıcının birden fazla org birimine bağlanması; tenant sınırı
- **Etkilenen:** ADR-0003, F10-001/010, F4 Order nullable şube rezervi, Approval
- **Seçenekler:**  
  A) Tenant = Firma kalır; şube firma-içi scope (önerilen geriye uyum)  
  B) Kullanıcı çoklu firma (ADR-0003 kırılır — ağır migrate)  
  C) Şube ayrı tenant (kör havuz/finans karmaşası — önerilmez)
- **Önerilen:** **A** — F4’te şube zorunlu değil; F10’da model
- **Karar:** **A** — ADR-0003 metni değişmez; uygulama **ADR-0015** ile açıldı (2026-11-09 plan onayı = Kabul)
- **Onaylayacak:** Ürün sahibi (+ güvenlik)
- **Not:** Agent ADR-0003’ü sessizce değiştiremez

### [U-015] Dynamic Pricing vs PriceQuote/PriceLock immutability

- **Faz:** Karar
- **Durum:** **Kabul** (2026-11-09, Emre override — Onaylayacak: ürün sahibi + finans)
- **Konu:** Koşullu fiyatın snapshot kurallarıyla ilişkisi
- **Etkilenen:** CAP-DYNPRICE, ADR-0008/0010, OrderLine
- **Seçenekler:** Yalnız yeni quote’ta koşul / kilit sonrası yeniden fiyat (yasak öneri)
- **Önerilen:** Koşul yalnız **yeni** quote; kilit/order snapshot değişmez
- **Karar:** Önerilen — koşul yalnız yeni quote; kilit/order snapshot değişmez
- **Onaylayacak:** Ürün sahibi + finans

### [U-016] ADR-0001 doküman düzeni (her bilgi tek yerde)

- **Faz:** Karar (çapraz)
- **Durum:** **Kabul** (2026-11-09, ürün sahibi Emre)
- **Konu:** Tek master dosya vs bilgi kaynaklarının ayrılması
- **Etkilenen:** ADR-0001, MASTER, docs/
- **Seçenekler:** Tek dosya / her bilgi tek yerde
- **Önerilen:** Her bilgi tek yerde + `docs_sync.py`
- **Karar:** Önerilen — bağlayıcı; MASTER “geçici düzen” notu kalktı
- **Onaylayacak:** Ürün sahibi


### [F4-054] OrderLine tutar ↔ birim tutarlılık testi (ADET / GRAM)

- **Faz:** Faz 4
- **Durum:** **UYGULANDI** (2026-11-09) · **Tip:** Test / Doğrulama
- **Kanıt:** `siparis/tests/test_order_pricing_units` — GRAM: `birim=toplam/quote.gram`, satır=`birim×miktar`; ADET: `satır=toplam×miktar`. Düzeltme: `order_servisi._snapshot_from_lock` (şema değişikliği yok).
- **Not:** SABIT_PARCA = ADET yolu; METAL_BAZLI/GRAM_BIRIM stok birimi GRAM ile aynı ölçek.

---

## Ürün sahibi karar bekleyen konular (U-*)

Agent bu tabloyu Kabul etmez. Kart ayrıntıları yukarıda.

| ID | Konu | Not | Durum |
|----|------|-----|-------|
| U-001 | ADR-0010 | L-01…L-11 (L-11 kodda) | **Kabul** |
| U-002 | Birim A | dönüşümsüz ADET/GRAM | **Kabul** |
| U-008 | Konsinye | F4 dışı | **Kabul** |
| U-012 | İnce PRE-API | dilim 7 | **Kabul** |
| U-003 | KDV / vergi | Önerilen: vergi yok; B-06 erteli | **Kabul** (2026-11-09, Emre override) |
| U-004 | İade/iptal finans | Önerilen Yok — uzman | **Kabul** (2026-11-09, Emre override) |
| U-005 | Cari | Basit cari v1; platform↔alıcı | **Kabul** (2026-11-09, Emre override) |
| U-006 | Hak ediş vadesi | Önerilen Yok | **Kabul** (2026-11-09, Emre override) |
| U-007 | Platform komisyon (B-01) | Kodlama yok; B-01 hukuk açık | **Kabul** (2026-11-09, Emre override) |
| U-009 | Metal/kur yuvarlama | 0.01 HALF_UP geçici | **Kabul** (2026-11-09, Emre override) |
| U-010 | Hukuki belgeler | Önerilen Yok | **Kabul** (2026-11-09, Emre override) |
| U-011 | Fiyat kırılımı | Mevcut A (toplam only) | **Kabul** (2026-11-09, Emre override) |
| U-013 | FX/HAS + hedge | Quote.gram; checkout gate ayrı | **Kabul** (2026-11-09, Emre override) |
| U-014 | Account Hierarchy | Seçenek A; ADR-0003 değişmez | **Kabul** (2026-11-09, Emre) |
| U-015 | Dynamic Pricing | Koşul yalnız yeni quote | **Kabul** (2026-11-09, Emre override) |
| ADR-0012 | Medusa P0/P1 paket | Tasarım Kabul; kod ayrı talimat | **Kabul** (2026-11-09, Emre) |
| U-016 | ADR-0001 doküman düzeni | Her bilgi tek yerde | **Kabul** (2026-11-09, Emre) |
| B-01 | Servis payı | v1 kapalı (0); hukuk metni gelene kadar kalem yok | **Kabul** (2026-11-09, Qubit) |
| B-06 | KDV | KDV yok / proforma devam | **Kabul** (2026-11-09, Qubit) |
| ADR-0014 | Karlılık sim | Sim + KS-6 quote UYGULANDI | **Kabul** (2026-11-09, Qubit) |
| U-006 vade netliği | Hak ediş tetik | **QC PASS** | **Kabul** (2026-11-09, Qubit) |
| U-004 iade netliği | Return v1 | **stok-only**; ödeme iadesi yok | **Kabul** (2026-11-09, Qubit) |
| F4-070b | Legacy stok kolon drop | RemoveField UYGULANDI (`0010`/`0016`) | **Kabul** (2026-11-09, Qubit) |
