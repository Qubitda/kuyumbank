# Faz tarihçesi

> **Append-only.** Eski maddeler silinmez / “güncel gibi” yeniden yazılmaz.  
> Bir satırdaki “açık / sıradaki / Bekliyor” ifadesi **o tarihin anısıdır**; güncel durum yalnız [MASTER](MASTER.md) §2 + §12 (+ [BACKLOG](BACKLOG.md)).  
> Yapı: üstte faz özetleri (F0–F4), sonra tarih damgalı dilim kayıtları (yeniler alta).

### Faz 0 — Standartlar / denetim
- Amaç: Secret, requirements, tenant denetim, agent kuralları.  
- Çıktı: ADR-0001/0002, denetim raporları (içerik bu master’a özetlendi).  
- Devir: Faz 1 kimlik.

### Faz 1 — Kimlik / RBAC
- `Firma` NOT NULL, roller, perm matrisi, `AuditOlay`, platform bootstrap.  
- ADR-0003 (+ addendum). Testler yeşil (tarihsel raporlar).  
- Devir: katalog ownership.

### Faz 2 / 2.1 — Katalog
- `olusturan_firma`; onay SM; eşleştirme B1–B3; admin kilidi. ADR-0005/0006.  
- Devir: teklif fiyatlama.

### Faz 3.1 — Teklif yaşam döngüsü (ADR-0007)
- Durum makinesi, versiyon swap, PROTECT, predicate. Migration 0005.  
- Sonra ADR-0009 admin H1–H5.

### Faz 3.2 — K-007 / K-008
- Sözleşme unique/exclusion, `cozumle`. Migration 0006.

### Faz 3.3 — Kur politikası
- Tek aktif provider, KurPolitikasi, stale fail-closed, quote_ttl alanı. Migration tanimlar 0002/0003.

### Faz 3.4 — Üç model + CurrencyConversion
- `hesapla_metal_bazli` / `gram_birim` / `sabit_parca`; TRY 0.01 HALF_UP; PB dönüşüm. Commit zinciri `b516893` içinde.

### Faz 3.5 — PriceQuote
- `pricing_service.quote`; Line; app+DB immutability (`0007`). Test 14+ OK (tarihsel).

### Faz 3.6 — Kör havuz + K-011
- `TeklifTasMaliyeti`; `buyer_quote`; admin maske. Commit **`7802eb4`**. Suite 254 OK (tarihsel handoff).

### Faz 3.7 — PriceLock
- Model + `lock_quote` + expire + concurrency; migrations `0010` (model/guard), `0011` (L-04 TTL INSERT), `0012` (L-07 perms).  
- L-07/L-10: dedicated permission; on-behalf gerekçe; audit.  
- Test: PriceLock **34 OK**; suite **288 OK**.  
- ADR-0010 **Kabul** (ürün sahibi 2026-11-08).  

### Faz 4.1 — Warehouse + dual-stock
- `Warehouse`, birim constants, dual-stock envanter yardımı; mig `stok.0001` (+ help_text `urunler.0008` / `fiyatlama.0013`).

### Faz 4.2 — StockMovement / StockBalance / düzeltme
- Immutable movement + balance projeksiyon; `ledger_servisi`; mig `stok.0002`.

### Faz 4.3 — StockReservation (F4-020/021)
- Hold+TTL; create/cancel/expire reserved-only; consume → SATIS; idempotency; `select_for_update` oversell.  
- mig `stok.0003`; test `stok.tests.test_reservation_f4_020` **9 OK**.

### Faz 4.4 — Cart (F4-030/031)
- `siparis` app: `Cart` / `CartLine`; stok düşmez.  
- mig `siparis.0001`; test cart **10 OK**.

### Faz 4 checkout dilimi (F4-040/041)
- `CheckoutAttempt` sipariş adayı; satır başına `lock_quote` + `olustur_rezervasyon`; idempotency; fail durable.  
- mig `siparis.0002`; test checkout **5 OK**.

### Faz 4 order dilimi (F4-050/051/052)
- `Order` / `OrderLine`: CheckoutAttempt → sipariş; L-11 `price_lock` OneToOne; satır snapshot; `tuket_rezervasyon` (SATIS).  
- Idempotency: checkout_attempt OneToOne + `(alici_firma, idempotency_key)`.  
- Şube FK yok (U-014 Bekliyor).  
- mig `siparis.0003`; test order create **6 OK**.

### Faz 4 iptal dilimi (F4-053)
- `order_servisi.iptal_siparis`: OLUSTURULDU→IPTAL; satır başına `StockMovement.IADE` (+on_hand); ödeme iadesi yok (U-004).  
- Idempotent yeniden iptal; tenant fail durable audit.  
- Test cancel **4 OK**.

### Faz 4 reorder (F4-080)
- `reorder_servisi.sepete_aktar`: Order satırları → güncel `pricing_service.quote` → Cart; eski lock yeniden kullanılmaz.  
- ATP fail-closed; birim uyumu; tenant IDOR; `replace_cart` varsayılan True.  
- Test reorder **4 OK**; `siparis` suite **29 OK**.  
- Devir: **PRE** veya F4-081. (F4.5 outbox F4-090 ayrı.)

### Açık temalar (tarihsel anı — F4 reorder dilimi sırası; güncel değil)
> O dönem notu: B-01/B-06; dual stock; DRF; U-*.  
> **2026-11-09 itibarıyla (MASTER):** B-01/B-06 Kabul (kod bilinçli yok); F4-070b drop; DRF+PRE UYGULANDI; U-014/F10 UYGULANDI. Güncel açıklar → MASTER §12.3.

### PRE-001…004 — İnce API iskeleti
| PRE-001 | DRF 3.18.3 pin + INSTALLED_APPS | `requirements.txt` |
| PRE-002 | health public; me 401 | `/api/v1/health/`, `/me/` |
| PRE-003 | cart/order tenant 404; `firma_id` query yok sayılır | `api.tests` |
| PRE-004 | OpenAPI schema | `/api/v1/schema/` |

### 2026-11-09 — Dokümantasyon yeniden yapılandırma
- Tek master dosyası yaşam döngüsüne göre bölündü: MASTER / decisions / BACKLOG / ROADMAP / HISTORY (+ RUNBOOK, otomatik DATA_DICTIONARY).
- `scripts/docs_sync.py`: test sayısı, migration, app, API, komut listeleri ve veri sözlüğü koddan üretilir; `--check` CI kapısı.
- Düzeltilen drift: §5 "PriceLock sipariş bağ PLANLANDI" → UYGULANDI (L-11); ADR-0011 indeks satırı "Dilim 1–3" → F4 dilim 1–8; gap tablosunda Sepet/checkout, API, Quick Reorder satırları; iş havuzu kart sayısı 124 → koddan sayılan değer.

### 2026-11-09 — F4-062 minimal alıcı UI
- Session `/buyer/`: login, sepet, checkout→order, sipariş liste/detay; alıcı-only; kör presenter.
- Test: `siparis.tests.test_buyer_ui_f4_062` **3 OK** (full suite istenmedi).

### 2026-11-09 — Faz 5 başlangıç (ADR-0012 Kabul)
- Ürün sahibi ADR-0012 **Kabul** (F5-K1…K10).
- `finans` app: `LedgerEntry` append-only + contra + PG trigger; `post_ledger` RBAC.
- FX-001 / HEDGE-001: `open_has` + `HedgeEntry` (mig `0001`/`0002`).
- U-005 / U-013 **Kabul** (platform↔alıcı; Quote.gram HAS).
- F5-011 `CariHesap` + F5-012 `PaymentIntent` (mig `0003`).
- Test: `finans.tests` **24 OK**; prod migrate `finans.0001–0003` uygulandı.

### 2026-11-09 — Ürün sahibi karar kaydı (yalnız docs; Emre)
- **U-016** + ADR-0001 doküman düzeni **Kabul**; MASTER “geçici düzen” notu kaldırıldı.
- **ADR-0012** Kabul checklist: tasarım; kod/migration ayrı açık talimat.
- **U-003…007, 009…011, U-013…015** → **Kabul** (Önerilen; dış onaylılarda ürün sahibi override). U-005/U-013 Seçenekler–Onaylayacak alanları geri yazıldı.
- **B-01 / B-06** dokunulmadı.

### 2026-11-09 — F5-013 finans audit zorunlu alanlar
- `finans_audit.record_finans_audit*`: actor (başarılı), amount, currency, order_ref, success.
- Ledger + PaymentIntent audit yolları bağlandı; migration yok.
- Test: `test_finans_audit_f5_013` **4 OK**; finans **28 OK**.

### 2026-11-09 — F5-020 ödeme adapter
- `finans.payments`: Port + FakePaymentAdapter; `tahsil_et` charge fail-closed; bilinemeyen provider ValidationError.
- Settings: `PAYMENT_PROVIDER` / `PAYMENT_FAKE_FORCE_FAIL` (secret yok).
- Test: `test_payment_adapter_f5_020` **5 OK**; finans suite **33 OK**.

### 2026-11-09 — F5-040 credit visibility
- `credit_servisi` + `GET/POST /api/v1/credit/me|check/`; maskeli bakiye/limit; tedarikçi 403; limit aşımı net hata.
- Test: `test_credit_f5_040` **5 OK**; finans suite **38 OK**.

### 2026-11-09 — F5-021 payment webhook
- `PaymentWebhookEvent` + `isle_webhook`; HTTP `/payments/webhook/` secret; tekrarlayan event tek sonuç.
- Mig `finans.0004`/`0005`; `tahsil_et(skip_provider=True)`.
- Test: `test_webhook_f5_021` **4 OK**; finans suite **42 OK**.

### 2026-11-09 — F5-030 buyer finans özeti
- `buyer_finans_servisi` + `GET /api/v1/finance/me/`; credit + PI listesi; kör assert (komisyon/marj yok).
- Test: `test_buyer_finans_f5_030` **4 OK**; finans suite **46 OK**.

### 2026-11-09 — F5-031 platform finans ops API
- `ops_finans_servisi` + `/api/v1/ops/finance/` (özet, cari, ledger); view_all zorunlu.
- Test: `test_ops_finans_f5_031` **3 OK**; finans suite **49 OK**.

### 2026-11-09 — F5-041 Contract Release Plan
- `ContractReleasePlan` / `ContractReleaseEvent` (append-only event); `release_servisi`; Quote/Lock’a yazmaz.
- Mig `fiyatlama.0015`; admin salt okunur + tenant scope.
- Test: `test_contract_release_f5_041` **6 OK**.

### 2026-11-09 — AUD-001b AuditOlay ip / changes
- `ip_address` + `changes`; `client_ip` + `TRUSTED_PROXY_COUNT`; durable sidecar kolon sync.
- Mig `firmalar.0006`. F5-022 atlandı (Blocked / U-006 ayrı talimat).
- Test: `test_audit_aud_001b` **4 OK**; audit çekirdek+b+o3 **12 OK**.

### 2026-11-09 — F5-032 finans UI
- `/buyer/finance/` (maskeli) + `/ops/finance/` (`view_all`); F5-030/031 servisleri.
- Test: `test_finance_ui_f5_032` **4 OK**; mig yok.

### 2026-11-09 — F6-001 / ADR-0013 QC Taslak
- `docs/decisions/ADR-0013-faz6-qc-lojistik.md` **Taslak** (F6-K1…K12); agent Kabul etmedi.
- F6-010+ kod yok; açık sorular: tolerans tipi, inspection birimi, rework, POD.

### 2026-11-09 — ADR-0013 Kabul + F6-010 QualityInspection
- Ürün sahibi Kabul; soru cevapları: %±abs tolerans; sipariş bazlı QC; rework=yeni inspection; POD opsiyonel.
- App `kalite`: SM + `shipment_blok` + `manage_qc` seed; mig `kalite.0001`.
- Test: `test_inspection_f6_010` **5 OK**.

### 2026-11-09 — Handoff sync (yeni session öncesi)
- **Migrate (yerel):** `firmalar.0006`, `urunler.0009`, `fiyatlama.0014`/`0015`, `kalite.0001` uygulandı.
- **docs_sync:** `kalite` APPS’e eklendi; `DATA_DICTIONARY.md` yeniden üretiliyor (`scripts/gen_data_dictionary.py`); `--check` OK.
- **RBAC:** `fiyatlama.view/change_uruntasi` → `tekliftasmaliyeti` (K-011); `seed_role_permissions` (QC perms OK).
- **CI:** test listesine `finans.tests` + `kalite.tests` eklendi.
- **Kabul işaretleri:** ADR-0013 Kabul; F4-070b ürün sahibi onayı (kod yok); F5-022 genel onay ama U-006 vade hâlâ net değil.
- **Sıradaki:** F6-011 → F6-020.

### 2026-11-09 — F6-011 Gram ölçüm + tolerans
- `QualityMeasurement` append-only; `tolerans_motoru` (bağıl ±% + abs taban; ADET tam eşitlik).
- `olcum_servisi.kaydet_olcum`: sapma → otomatik FAIL; override `manage_qc_override` + gerekçe≥10.
- Settings: `QC_GRAM_TOLERANCE_PCT` / `QC_GRAM_TOLERANCE_ABS`; mig `kalite.0002`.
- PASS için uygun/override ölçüm zorunlu (F6-010 happy path güncellendi).
- Test: `kalite.tests` **16 OK** (`test_olcum_f6_011` 11 + `test_inspection_f6_010` 5).
- **Sıradaki:** F6-020 (`lojistik` Shipment + QC gate).

### 2026-11-09 — F6-020 Shipment + QC gate
- App `lojistik`: `Shipment` SM (`TASLAK→HAZIR→YOLDA→TESLIM|IPTAL`); create `order_shipment_blocked` (F6-K6).
- `manage_shipment` + PLATFORM_LOGISTICS seed; mig `lojistik.0001`; CI’ye `lojistik.tests`.
- Test: `test_shipment_f6_020` **6 OK** (+ kalite 16 = 22 OK).
- **Sıradaki:** F6-021 carrier fake → F6-022 POD → F6-023 buyer track.

### 2026-11-09 — F6-021 Carrier fake port
- `lojistik.carriers` (port/fake/factory); bilinmeyen provider fail-closed; secret yok.
- `sevk_et` takip boşsa fake label (`FAKE-ship-{id}`); force_fail audit + ValidationError.
- Test: `test_carrier_f6_021` **5 OK** (lojistik toplam 11 OK).
- **Sıradaki:** F6-022 POD → F6-023 buyer track.

### 2026-11-09 — F6-022/023 + karlılık sim
- POD: `ProofOfDelivery`; `SHIPMENT_POD_REQUIRED` (default off); mig `lojistik.0002`.
- Buyer API: `GET /api/v1/shipments/` (+ detail); maskeli; tedarikçi 403 / çapraz 404.
- `karlilik_simulasyonu` Excel A/B (saf Decimal); ADR-0014 **Taslak** — quote’a bağlanmadı.
- Test: lojistik+api shipment+karlilik odaklı **20 OK**.
- **Sıradaki:** F6-012 / F6-030(U-004) / ADR-0014 Kabul kararı.

### 2026-11-09 — F6-012 Document + taş sertifika
- App `belgeler`: `Document` (tenant + storage_key) + `TasSertifikaBelgesi` (UrunTasi XOR TeklifTas).
- RBAC `manage_document`; tenant selector; binary/S3 yok (K-014).
- Mig `belgeler.0001`; test **6 OK**.
- **Sıradaki:** politika (F6-030 / F5-022) veya ADR-0014 Kabul.

### 2026-11-09 — Ürün sahibi: bekleyen kararlar Kabul + F6 sync commit
- Qubit: ADR-0014, B-01 (v1=0), B-06 (KDV yok), U-006 vade=**QC PASS**, U-004 iade=**stok-only**, F4-070b drop onayı.
- F5-022 / F5-023 / F6-030 **Blocked → Backlog** (kod ayrı talimat).
- Kod bu commit’te: F6-011…023, F6-012, karlılık sim.

### 2026-11-09 — F6-030/031 + F5-022/023 (kalan politika dilimleri)
- **F6-030/031:** `ReturnRequest`/`ReturnLine` SM; TESLIM gate; ONAYLANDI → stok IADE; `manage_return`; mig `lojistik.0003`.
- **F5-022:** `TedarikciHakEdis`; QC PASS hook; `SUPPLIER_ACCRUAL_VADE_GUN`; `unpaid_supplier_has`; mig `finans.0006`.
- **F5-023:** `mahsup_servisi` MAHSUP ALACAK; `odeme_iadesi_yap` fail-closed (U-004).
- Odaklı test: return 5 + hak ediş 5 + mahsup 3 + QC/FX regresyon = **24 OK**.
- **Sıradaki:** F4-070b kolon drop veya ADR-0014 KS-6 (açık talimat).

### 2026-11-09 — F4-070b Legacy stok kolon drop
- `Varyant.stok` + `TedarikciTeklif.stok_adet` RemoveField; `varyant_benzersiz_parca_stok` drop.
- `dual_stock_envanter` + F4-070 yazma-kilidi testleri silindi; `teklif_servisi` kopya yolu temiz.
- Mig `urunler.0010` / `fiyatlama.0016` (`lock_timeout=2s`); **veri kaybı bilinçli** (legacy sayaç).
- **Sıradaki:** ADR-0014 KS-6 (quote bağ) veya F7/F10.

### 2026-11-09 — KS-6 hedef toplam quote + eski alias temizliği
- `quote(hedef_toplam=)` → `HEDEF_TOPLAM` kalem; platform `manage_sozlesme`; banka/GV yok (KS-4).
- Kaldırıldı: `fiyatlama.models.UrunTasi` alias, `FiyatlamaUrunTasiAdmin` alias.
- Mig: tümü uygulandı (onaylı; pending yok). Test odaklı **28 OK**.
- **Sıradaki:** U-014/F10 org ADR veya F7.

### 2026-11-09 — F10 Account Hierarchy + F7 API/entegrasyon iskeleti
- **ADR-0015** Account Hierarchy **Kabul** (plan onayı = ürün sahibi).
- F10-010…013/020: `OrgBirimi`/`OrgUyeligi`, `HarcamaLimiti`, `OnayTalebi`, RFQ SM; `Order`/`Cart.sube` nullable.
- F7-010…015: maske, buyer/supplier/ops API, problem+json, throttle scopes, `/api/v1/` sabit.
- F7-020…024: `WebhookDelivery`, FakeERP/CRM, `ConnectorRegistry`, punchout stub.
- Mig: `firmalar.0007`, `siparis.0004`, `fiyatlama.0017` (KS-6 kalem); odaklı test **22 OK**.
- **Sıradaki:** F10-014/021–023 UI veya F8 CI/ops; Celery yok.

### 2026-11-09 — F10-014 onay UI + F10-023 RFQ buyer UI
- `/buyer/approvals/` (manage_approval; tenant 404); `/buyer/rfq/` liste/create/detail/send/message.
- F10-021 KISMİ: katalog dışı = varyantsız RFQ satırı; eşleştirme motoru yok.
- Selector: `firmalar.selectors.onay`, `siparis.selectors.rfq`.
- Test: `test_approval_ui_f10_014` **5 OK** + `test_rfq_ui_f10_023` **4 OK**.
- **Sıradaki:** F8 ops veya F9-001 ADR; F10-022 / F10-021 eşleştirme; F10-023 supplier UI.

### 2026-11-09 — F8 ops çekirdek
- F8-001 CI: `manage.py check` adımı; F8-002 `RequestIdMiddleware` + JSON/secret-aware logging.
- F8-004/005/008 RUNBOOK §7–§10; F8-003 Sentry plan §11 (SDK yok); F8-009 throttle env.
- F8-007 IDOR smoke: `test_security_f8_007` **5 OK**; logging **5 OK** birleşik **10 OK**.
- **Sıradaki:** F9-001 ADR; F8-006 perf; Sentry SDK; F10-022.

### 2026-11-09 — ADR-0016 Taslak + F10-022 özel üretim
- **ADR-0016** frontend stack **Taslak** (öneri C→A Django önce); F9 kodu Kabul şart.
- F10-022: `RFQ.talep_tipi` + `RFQRevizyon` append-only; `revizyon_ekle`; buyer UI.
- Mig `siparis.0005`; test `test_rfq_ozel_f10_022` **3 OK** (+ RFQ regresyon yeşil).
- **Sıradaki:** ADR-0016 **Kabul** (ürün sahibi) → F9-010; veya F8-006 / F10-023 supplier.

### 2026-11-09 — ADR-0016 Kabul + F9-010 dashboard
- Ürün sahibi Qubit: ADR-0016 **Kabul** (FE-1 C→A, FE-2 `/supplier/` Django, FE-3 Session, FE-4 PWA sonra, FE-5 minimal CSS).
- F9-010: `/buyer/` panel (`BuyerHomeView` + `buyer_dashboard_servisi`); sepet → `/buyer/cart/`.
- Test `test_buyer_dashboard_f9_010` **3 OK** (+ F4-062 regresyon).
- **Sıradaki:** F9-011 katalog browse; F9-013 supplier iskelet; F8-006.
- > **Dipnot (2026-11-09 docs temizlik):** F9-010 kaynakları şu an **commit dışı** (Kova B WIP); canlı durum MASTER §12.3.

### 2026-11-09 — Doküman drift onarımı (ROADMAP/HISTORY/RUNBOOK)
- Dış inceleme: ROADMAP bayat/çelişkili (5/10); HISTORY yapı; RUNBOOK test/env geride.
- ROADMAP §1–4 MASTER §12 ile yeniden hizalandı (F4–F10/F8/F9 durumları).
- HISTORY: append-only kuralı + “Açık temalar” tarihsel anı işareti.
- RUNBOOK: CI ile aynı test komutu + env satırları.

### 2026-11-09 — Full suite koşusu
- `manage.py check` + `makemigrations --check` temiz.
- Suite (CI listesi, `--keepdb`): **555 OK** in 826s.
- MASTER §2.7 elle güncellendi.

### 2026-11-09 — F9-011 katalog browse UI
- `/buyer/catalog/` liste+arama+detay; `buyer_katalog_servisi` (yayınlı; kör; `tedarikci_sku`/maliyet yok).
- Test `test_buyer_catalog_f9_011` **5 OK**.
- **Sıradaki (o an):** F9-012 sepet/sipariş polish; F9-013 supplier; F8-006.
- > **Dipnot (2026-11-09 docs temizlik):** F9-011 kaynakları şu an **commit dışı** (Kova B WIP); canlı durum MASTER §12.3.

### 2026-11-09 — ADR-0016 Supersede + ADR-0017 Taslak + API-B0
- Ürün sahibi: birincil tüketici Next.js App Router; Django HTML ürün büyütmesi yok; `/buyer/` `/ops/` kalır.
- **ADR-0016** → **Supersede** (eski FE-1 C→A yürürlükte değil).
- **ADR-0017** → **Taslak** (NX-1 session+CSRF; NX-2 page sayfalama; OpenAPI drift; B0–B7).
- API-B0 boşluk analizi (kod yok): 11 madde puan + uç envanteri.
- **Sıradaki (o an):** ADR-0017 **Kabul** → API-B1.

### 2026-11-09 — API-B1 (koşullu)
- NX-1/NX-2 ürün sahibi kararı; ADR-0017 **Taslak** kaldı; CORS B1’den çıkarıldı (aynı-origin).
- Session login/csrf/logout; problem+json (`code`/`errors`/`request_id`); page sayfalama + `-pk`; `/me` capabilities; OpenAPI drift CI; no-store.
- Kova B F9 HTML WIP dokunulmadı (B1 dışı).
- **Sıradaki (o an):** B1 raporu onayı → B2 talimatı.

### 2026-11-09 — API-B1 Kabul + B2 başlat
- Ürün sahibi: B1 **Kabul** (28 odaklı OK; tam suite iddiası yok).
- ADR-0017 **Taslak**; NX-1/NX-2 madde **Kabul**; CORS erteli; NX-3…12 açık.
- B2: buyer catalog/cart/quote/lock/order HTTP (servis yeniden yazılmaz).

### 2026-11-09 — API-B2 buyer commerce
- Uçlar: quotes, price-locks, carts/me/lines, orders/from-checkout, cancel, reorder; catalog detail.
- Buyer* presenters: Decimal string, expires_at/server_now, allowed_actions, maske.
- Test `test_api_b2_buyer_commerce` + order/pre005 regresyon **11 OK** odaklı.
- **Sıradaki (o an):** B3 talimatı.

### 2026-11-09 — API-B2 Kabul + concurrency + B3
- Ürün sahibi B2 **Kabul**.
- Idempotency: PG `pg_advisory_lock` (firma+key); `test_api_b2_concurrency` **7 OK**.
- API-B3 UYGULANDI: finance/cari/ledger, payments/intents, ops/finance/payments, shipments `allowed_actions`, returns CRUD+SM; `test_api_b3_finance_ops` **10 OK**.
- OpenAPI `docs/api/openapi-v1.json` güncellendi. ADR-0017 **Taslak**.

### 2026-11-09 — API-B3 Kabul + OpenAPI bakım + oturum kapanışı
- Ürün sahibi B3 **Kabul**; B2 concurrency **7 OK** Kabul.
- TECH-OPENAPI-01 **UYGULANDI**: `api_urlpatterns` + `url=/api/v1/` → çift önek **0**; canlı URL aynı.
- **API-B4 resmi olarak başlatılmadı** (ürün sahibi faz tablosu). Erken ajan WIP (`org`/`approvals`/`rfq` view dosyaları) commit dışı bırakıldı; UYGULANDI sayılmaz.
- Kova B F9 HTML WIP commit dışı (silinmedi).
- Devir (tarihsel): ayrı `SESSION_HANDOFF.md` kullanılıyordu — sonradan kaldırıldı; tek giriş `AGENTS.md` → [MASTER](MASTER.md) §12. ADR-0017 **Taslak**. Tam suite bu oturumda **yok**.

### 2026-11-09 — API-B4 kurumsal HTTP
- Org / onay / RFQ REST: mevcut `org_servisi` / `onay_servisi` / `rfq_servisi` HTTP sarmalı; WIP entegre.
- Uçlar: `org-units`, `approvals` (+submit/approve/reject), `rfqs` (+send/messages/revisions).
- Düzeltmeler: RFQ `varyant_id` B2 catalog görünürlük kuralı; 401/403/404 tek kural; presenter private `_TRANSITIONS` yok.
- Kapsam dışı (servis yok / rapor): org update/deactivate, üye silme, RFQ kapat/iptal, limit CRUD, firma CRUD, rol atama HTTP, supplier RFQ/match.
- Test `api.tests.test_api_b4_enterprise` odaklı **11 OK** (idempotency + PG concurrency dahil).
- OpenAPI güncellendi (çift önek yok). ADR-0017 **Taslak**; B4 **Kabul değil** — ürün sahibi incelemesi bekliyor.
- Kova B F9 HTML’e dokunulmadı. Sıradaki: B5 yalnız ayrı talimat.

### 2026-11-09 — Docs bayat metin temizliği + docs_sync lint
- Canlı docs: suite 555→597; F9-010/011 UYGULANDI→WIP commit dışı; ROADMAP/ADR indeks B4 hizası; API_CONTRACT ölü ref kaldırıldı.
- `scripts/docs_sync.py`: git-tracked test sayımı; `--lint-docs` / `--lint-docs-strict` (CI soft `continue-on-error`).
- Tek kaynak (o an): B0–B7 → SESSION_HANDOFF §3 *(tarihsel)*; canlı → MASTER §12; ADR → decisions/.

### 2026-11-09 — SESSION_HANDOFF kaldırıldı; tek oturum girişi MASTER §12
- `docs/SESSION_HANDOFF.md` silindi. B0–B7 tablosu → [MASTER](MASTER.md) §12.1b; yeni oturum → §12.5 (`AGENTS.md` → MASTER).
- ROADMAP / BACKLOG / decisions/README / docs_sync faz lint’i MASTER’a yönlendirildi.
- Yasak: ikinci handoff / durum raporu / paralel özet dosyası.

### 2026-11-09 — API-B4 Kabul + API-B5 ops QC/sevkiyat
- Ürün sahibi B4 **Kabul**.
- B5: `/api/v1/ops/inspections/*` + `/api/v1/ops/shipments/*` (prepare/dispatch/deliver/cancel/pod); mevcut servis sarmalı; yeni HTML yok.
- Test `api.tests.test_api_b5_ops` **7 OK** (idempotency + PG concurrency). OpenAPI güncellendi.
- B5 **Kabul değil** — inceleme bekliyor. Sıradaki: B6 yalnız ayrı talimat.

### 2026-11-09 — API-B5 Kabul + API-B6 tedarikçi API
- Ürün sahibi B5 **Kabul**.
- B6: `/api/v1/supplier/offers/*` (submit/deactivate/versions) + `stock/adjustments/` + `rfqs/*` (ters kör mesaj/revizyon); `teklif_servisi` / `ledger_servisi` / `rfq_servisi`.
- Test `api.tests.test_api_b6_supplier` **3 OK**. OpenAPI güncellendi. B6 **Kabul değil**.

### 2026-11-09 — API-B6 Kabul + API-B7 dondurma / frontend-ready
- Ürün sahibi B6 **Kabul**.
- B7: OpenAPI yeniden üretildi (`--check` OK; çift önek 0; 81 path); `docs/API_CONTRACT.md` (matris + checklist + sınırlar); `test_api_b7_openapi` **1 OK**.
- B7 **Kabul değil**. Sıradaki: Next.js `frontend/` yalnız ayrı talimat.

### 2026-11-09 — DOC-CONSISTENCY-01 dokümantasyon tutarlılığı
- Sahiplik: `AGENTS.md` + MASTER’a `API_CONTRACT` / OpenAPI satırı; ADR-0017 faz tablosu MASTER §12.1b’ye yönlendirildi (kopya kaldırıldı).
- `scripts/docs_sync.py` faz lint’i B4 bayat mantığından B5–B7 / BACKLOG çapraz kontrole güncellendi.
- HISTORY eski B5/B6 “Kabul değil” satırları **tarihsel** bırakıldı (append-only).

### 2026-11-09 — API-B7 Kabul + B6/B7 commit
- Ürün sahibi B7 **Kabul** (Qubit). B6 tedarikçi API + B7 dondurma (OpenAPI/API_CONTRACT/docs_sync) working-tree’den commit; F9 HTML WIP dışı.

### 2026-11-09 — DOC-CONSISTENCY-02 tam proje kod↔docs denetimi
- BACKLOG `[API-B4]` bayat «henüz başlatılmadı» → **Kabul** (MASTER/commit ile hizalı).
- MASTER §2 `api` / güvenlik / Next.js / ADR-0014 KS-6 ifadeleri kodla hizalandı.
- `docs_sync` faz lint: API-B4 kartı MASTER §12.1b’ye bağlandı.

### 2026-11-09 — TECH-NX-CONTRACT-01 (NX-3…12 kod kanıt)
- `exception_handler`: hata yanıtları `application/problem+json` (`ProblemJSONRenderer` + `request.accepted_renderer`).
- ADR-0017 NX-3…12 satır satır **Kod: UYGULANDI/KISMİ**; madde durumu o sırada **Açık** (agent Kabul etmedi).
- `api.tests.test_api_nx_contract` **4 OK**; API_CONTRACT / MASTER §12 / BACKLOG kartı güncellendi.

### 2026-11-09 — NX-3…12 madde Kabul (Qubit)
- Ürün sahibi: ADR-0017 **NX-3…NX-12** maddeleri **Kabul**; NX-1…12 tamamı madde Kabul.
- ADR-0017 **bütünü Taslak** kalır (yalnız madde onayı; agent ADR Kabul etmez).
- Sıradaki: **NX-FE** (`frontend/`) yalnız açık talimat.

### 2026-11-09 — NX-FE Next.js `frontend/` iskelet
- `frontend/`: App Router + TS + Tailwind v4; aynı-origin `/api/v1` rewrite; session/CSRF client; `/` + `/login`.
- Tasarım kiti dokümanları `frontend/docs` + `.cursor/rules`; Django HTML dokunulmadı.
- `npm run lint` + `npm run build` OK. Sıradaki: **NX-SHELL** (shadcn + shell) veya F8-003/006.

### 2026-11-09 — NX-ARCH feature/domain FE iskeleti
- `features/{firmalar,…,belgeler,auth}` katmanları + `app/(portal)/*` page/loading/error.
- Rehber: `frontend/docs/FRONTEND_ARCHITECTURE.md`. Zod eklendi; shadcn hâlâ NX-SHELL.
- Lint/build OK (15 route).

### 2026-11-09 — F5-041b Contract Release sipariş tüketimi
- `ContractReleaseConsumption` (TUKETIM/IADE append-only); `kullanilabilir = serbest − net tüketim`.
- `order_servisi.olustur_from_checkout` / `iptal_siparis` bağ; Quote/Lock’a yazmaz; mig `fiyatlama.0018`.
- Test: `test_contract_release_consume_f5_041b` **4 OK** + F5-041 **6 OK**.

### 2026-11-09 — ADR-0018 CAP-PIYASA Taslak (docs)
- [ADR-0018](decisions/ADR-0018-cap-piyasa-kur-dayanikliligi.md) **Taslak**: kaynak merdiveni, LKG+banner, batch senkron/freeze, guardrail, yuvarlama, çapraz kur sanity, atomik publish, quote immutability.
- B-04 yeniden tanım Kabul’e bağlı; kod yok. BACKLOG `[CAP-PIYASA]`; MASTER §12.3.
- Geçici referans: kök `real_data/` (GoldXT) — toptan port yok; sonra silinebilir.

### 2026-11-10 — F10-021 RFQ katalog eşleştirme + F8-003/006
- F10-021: `RFQEslestirme` + `rfq_eslestirme_servisi` (aday/öner/onay/red); kural tabanlı skor; platform `approve_eslestirme`; mig `siparis.0006`; **7 OK**.
- F8-003: `sentry-sdk` pin + DSN opt-in + scrub; **3 OK**; staging event DOĞRULANAMADI.
- F8-006: quote/lock/cart_checkout soft smoke baseline; **1 OK**.
- **Sıradaki:** CAP-PIYASA (ADR-0018 Kabul) → object-level DRF / Mahsup HTTP.

### 2026-11-10 — F11-013 bildirim outbox (QC/iade)
- `qc.passed` / `qc.failed` (`inspection_servisi`) + `return.approved` (`return_servisi`); `order.created` zaten F4-090.
- Test: `kalite.tests.test_notify_f11_013` **3 OK**.

### 2026-11-10 — ADR-0018 Kabul + CAP-PIYASA UYGULANDI
- Ürün sahibi Kabul + uygulama talimatı.
- `fiyat_kaynagi` (ürün/ayar/politika); `feed_health` LKG+banner; `kaynak=tcmb`; batch dry-run/publish; guardrail; Binance/TCMB adaptör + sync komutları.
- Mig: `tanimlar.0004`, `urunler.0011`, `fiyatlama.0019`.
- Test: `test_cap_piyasa_adr0018` + kur/quote regresyon **37 OK**.

### 2026-11-10 — CAP-ALERT + F11-011/012/020
- CAP-ALERT: `KurAlertKurali` + `kur.alert` outbox; stale’de tetik yok; mig `tanimlar.0005`; **3 OK**.
- F11-012 ATP: `on_hand − reserved − blocked`; kör alıcı; **4 OK**.
- F11-011 quote/lock analitik (platform); **3 OK**.
- F11-020 replenishment öneri (checkout yok); **2 OK**.
- **Sıradaki (ayrı takip):** object-level DRF · Mahsup HTTP · FE · F11-001/010 raporlama.

### 2026-11-10 — F11-001/010/021/014 raporlama dilimi
- F11-001: [NOTE-F11-001](decisions/NOTE-F11-001-raporlama-v1.md) RM-1…6; Product P-RM-* (DRF/Mahsup/FE/ETL) erteli.
- F11-010 + F11-021: `siparis.services.rapor_servisi` (`ticari_siparis_ozet`, `alici_davranis_ozet`); tenant + kör; **5 OK**.
- F11-014: `anomali_servisi.ciro_esik_tara` audit + ops uyarı; **3 OK**.
- **Sıradaki (ayrı takip):** object-level DRF · Mahsup HTTP · FE.

### 2026-11-10 — CAP-ALERT ops + rapor güvenlik sertleştirme
- `KurAlertKuraliAdmin` (`manage_kur`); `evaluate_kur_alerts --now`; outbox `process_outbox` smoke; RUNBOOK §6/§8/§11b.
- Rapor: alıcı foreign `alici_firma_id` yok sayılır; deny → durable audit.
- Anomali deny → durable audit.
- Test: `test_kur_alert_cap` **4** + `test_rapor_f11_010_021` **6** + `test_anomali_f11_014` **3** = **13 OK**.
- F11-011: deny → durable audit; `test_fiyat_analitik_f11_011` **3 OK**.
- **Sıradaki (ayrı takip):** object-level DRF · Mahsup HTTP · FE; F12 Product (001/011/DYNPRICE/015) onay kapılı.

### 2026-11-10 — ADR-0019 Taslak + bekleyen ürün karar notu
- [ADR-0019](decisions/ADR-0019-object-level-drf.md): endpoint/model envanteri, S-1…S-6, rol matrisi, OL-1…11 onay maddeleri; **HTTP yok**.
- [NOTE-PENDING-PRODUCT-DECISIONS](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md): F12-001/011, CAP-DYNPRICE, F11-015 kısa formlar.
- BACKLOG `[SEC-OBJECT-DRF]`; MASTER §12.3 ADR-0019 **Taslak**.

### 2026-11-10 — ADR-0019 onay paketi netleştirme (kod yok)
- OL-1…11: her biri Mevcut / Öneri / Güvenlik / Seçim / **Bekliyor**.
- Matris çakışması giderildi (ops Order W ↔ OL-2).
- OL-3/OL-4: bugün `alici_mi` ile W açık → öneri sıkılaştırma (SoD).
- FXQ/DYN/I18N/AI ADR-0019’dan ayrık NOTE’ta.

### 2026-11-10 — ADR-0019 Kabul + OL-11
- Ürün sahibi: OL-1…11 tümü **A** → ADR **Kabul**.
- `api.permissions`: commerce read/write + Order/Cart/Quote object access; SoD (denetçi/onaycı/finans W yok).
- View hizası: quote/lock/cart/checkout/order/bulk; selector + `check_object_permissions`.
- Test: `test_object_level_adr0019` **6 OK**; F8-007 **5 OK**; B2 **4 OK**.
- Rapor/mahsup HTTP açılmadı (OL-7/8).

### 2026-11-10 — Teslimat sabitleme (cleanup + docs)
- MASTER/BACKLOG/HISTORY/RUNBOOK/decisions senkron; F9-010/011 Django HTML miras **UYGULANDI** (Next portal değil).
- `real_data/` gitignore; NOTE-PENDING (FXQ/DYN/I18N/AI) ayrı kaldı.
- Odaklı regresyon: **55 OK**; `manage.py check` OK; `docs_sync --check` OK; makemigrations --check OK.

### 2026-11-10 — Kod–doküman uyumluluk: `real_data/` kaldırma
- GoldXT özet → ADR-0018 §GoldXT (feed zaten `feed_adapters`; UI/port yok).
- Kök `real_data/` silindi; kod/test/CI/script/frontend referansı **0** (yalnız tarihsel docs + `.gitignore`).
- ROADMAP/RUNBOOK F9 “WIP commit dışı” → Django HTML miras (BACKLOG/MASTER ile hizalı).
- BACKLOG CAP-PIYASA geçici-ref satırı “kaldırıldı”.

### 2026-11-10 — Frontend ↔ Backend mimari uyum denetimi
- Envanter: Django domain app’ler + `frontend/src/features|app|lib`; canlı Next akışı yalnız auth/health.
- Domain feature’lar iskelet (`export {}`); ürün UI hâlâ `/buyer/` `/ops/` HTML.
- Rapor: [FRONTEND_ARCHITECTURE §9](../frontend/docs/FRONTEND_ARCHITECTURE.md); `HealthResponse.service?` hizası.

### 2026-11-10 — Backend API readiness gate (FRONTEND NOT READY)
- Envanter + matris: [API_READINESS](API_READINESS.md).
- Katalog API: `q` + `buyer_katalog_servisi` detay/varyant; OpenAPI bileşen enjeksiyonu (me/catalog/quote/lock/cart).
- ADR-0019 OL-7/8 açılmadı. Verdict: **FRONTEND NOT READY**.

### 2026-11-10 — ADR-0020 Kabul + CAP-PANO UYGULANDI
- Ürün sahibi onay: piyasa panosu (baz fiyat) + admin + kar yardımcısı + iç işlem `PANO`/`MANUEL`.
- App `piyasa`: `PiyasaUrun` / `PiyasaFiyatKurali`; `hesap` (Django’suz); `baz_fiyat` / `cozumle_islem_birim_fiyati` / `kar_yardimcisi`.
- Mig `piyasa.0001_adr0020_piyasa_panosu`; `seed_piyasa`; `manage_piyasa` rol matrisi.
- Test: `piyasa.tests` **11 OK**. Quote/order bağlama PP-9 sonraki dilim.

### 2026-11-10 — ADR-0021 Kabul + act-as + `/supplier/` + demo seed
- `firmalar.act_as_user`; middleware session swap; admin aksiyon; audit start/stop; portal banner.
- Tedarikçi HTML: `/supplier/` (teklif/stok/RFQ okuma); yazma API’de.
- `seed_demo_portals` → `demo_alici` / `demo_tedarikci`.
- Mig `firmalar.0009`; test **6 OK**.

### 2026-11-10 — CAP-PANO marj hizası (GoldXT)
- Ayrı `PiyasaFiyatKurali` admin/tanım kaldırıldı; marj ürün satırında (`marj_modu` TL|YUZDE, `alis_marj`/`satis_marj` ≥0).
- Metal/ayar yalnız `tanimlar` FK; ayar seçilince metal ayardan.
- Mig `piyasa.0002_goldxt_marj_urun_satiri`; `piyasa.tests` güncellendi.

### 2026-11-10 — ADR-0022 Taslak (CAP-PANO-v2)
- Ürün sahibi: v1 backend GoldXT beklentisinden uzak; FE değil domain eksik.
- Taslak: grup/varyant, global marj modu, Darphane işçilik, birimli kesintiler, metal+ayar kar girişi, `PiyasaKarPolitikasi`.
- ONS/KG çapraz → v2.1.

### 2026-11-10 — ADR-0022 Kabul + CAP-PANO-v2 UYGULANDI
- Qubit: “go onaylıyorum”.
- Modeller: `PiyasaMarjPolitikasi`, `PiyasaKarPolitikasi`, `DarphaneIscilik`; `PiyasaUrun.grup` / `varyant_etiket`; satır `marj_modu` kaldırıldı.
- `karlilik_simulasyonu` birimli kesinti (YUZDE|TL); `simule_metal_ayar`; admin kar formu güncellendi.
- Mig `piyasa.0003_adr0022_pano_v2_domain`; test **21 OK**.

### 2026-11-10 — ADR-0023 Kabul + Mahsup HTTP UYGULANDI
- Qubit: “diğer fazlara geç” → §12 Mahsup HTTP (PP-9 pano bağ erteli).
- `POST /api/v1/returns/{id}/mahsup/` (`post_ledger`); approve gövde `mahsup`; OpenAPI export.
- Test: `test_api_b3_finance_ops` + `test_api_b7_openapi` **13 OK**. OL-7 rapor HTTP hâlâ kapalı.

### 2026-11-10 — ADR-0024 Kabul + CAP-PANO-PP9 UYGULANDI
- Qubit: “ok kalan işten devam et” → PP-9.
- `piyasa.services.quote_baglama.quote_from_islem_fiyati` → KS-6 `hedef_toplam` + `hesap_girdisi` pano metadata.
- HTTP yok; buyer quote yolu değişmedi. Test: `test_quote_baglama` **4 OK** (+ KS-6 regresyon).

### 2026-11-10 — ADR-0025 Kabul + CAP-PANO-v2.1 UYGULANDI
- Qubit: “kalan işten devam” → ONS/KG.
- `PiyasaUrun.olcek` / `cikti_pb`; `hesap.hesapla_ham`; USDTRY döviz; seed `ons_usd` / `has_kg`.
- Mig `piyasa.0004_adr0025_ons_kg`; test **22 OK**.

### 2026-11-10 — “hepsini onaylıyorum” paketi
- ADR-0026 rapor/anomali HTTP; NOTE-PENDING A seçimleri Kabul (kod kapıları kapalı).
- API_READINESS → **FRONTEND READY**; `frontend/lib/api/schema.d.ts` + `npm run generate:api`.
- FE v1 §4 P1/P2 **dışı** imzalı; Next portal ayrı dilim talimatı.

### 2026-11-10 — API documentation standard (Swagger/ReDoc + lint)
- `/api/schema/` · `/api/docs/` · `/api/redoc/`; prod erişim `DEBUG` / `API_DOCS_PUBLIC` / staff|platform.
- 81 path 2xx DTO bağları; `scripts/lint_openapi.py` CI; `drf-spectacular` UI.
- TS client erteli. Verdict hâlâ **FRONTEND NOT READY**.

### 2026-11-10 — OpenAPI request body kapanışı (47 write op)
- `api/openapi_requests.py`: A payload + B Empty/Reason/TakipNo/Reorder; lint `requestBody.$ref` zorunlu.
- API_READINESS §2/§4 güncel (response stub iddiası kaldırıldı; FE v1 imza tablosu).
- Verdict: **FRONTEND NOT READY** (§4 imza + suite + TS).

### 2026-11-10 — Ops güvenlik + doküman drift onarımı
- Act-as AA-9: `AuditOlay.on_behalf_of` + middleware `act_as_audit_context` (gerçek aktör inkâr edilemezliği).
- HTML login throttle (`LoginThrottleMiddleware`); `CACHES` ayarı; `purge_idempotency_records`; CI’ya `piyasa.tests`.
- API_CONTRACT ↔ API_READINESS READY hizası; FE-SUITE kanıtı KISMİ işaretlendi; RUNBOOK çift API docs satırı silindi.
- **Secret:** `.env` gitignore’da; zip sızıntısı varsa DB şifresi + SECRET_KEY rotasyonu ürün sahibi.

### 2026-11-10 — Veri bütünlüğü / perf sertleştirme
- `StockBalance` ATP CheckConstraint; `get_or_create_balance_locked` IntegrityError yarış düzeltmesi.
- `LedgerEntry` hareket_tipi/ISO/CONTRA DB kuralları; `StockMovement` tip + QuerySet ban.
- Return/Onay domain `idempotency_key` UNIQUE; org kod replay; advisory `pg_try_*` + timeout.
- Rapor tarih aralığı (max 366g); pagination out-of-range → 404; `CONN_MAX_AGE`; LocMem prod `W001`.
- RUNBOOK: Movement trigger iddiası düzeltildi; cron’a purge + `clearsessions`.

### 2026-11-10 — Auth / webhook sertleştirme
- Login throttle: `client_ip` (TRUSTED_PROXY_COUNT) + kullanıcı adı kovası; Basic prod kapalı + Basic IP throttle.
- `ExpiringTokenAuthentication` (`AUTH_TOKEN_TTL_SECONDS`); `purge_expired_tokens`; parola min 12; session idle.
- Webhook HMAC + replay penceresi + isteğe bağlı IP allow-list; MFA platform/act-as **PLANLANDI**.

### 2026-11-10 — E-posta / bildirim (ADR-0027 Taslak)
- Yeni app `bildirim`: SmtpSettings (sealed parola), EmailTemplate, NotificationRule, EmailDelivery, RecipientSettings.
- Outbox handler → idempotent `EmailDelivery`; `process_email_queue`; Admin (SMTP/şablon/kural/log/alıcı + manuel gönderim).
- Domain enqueue: `order.cancelled`, `payment.*`, `shipment.delivered`, `firma.approved`, `user.welcome` (+ mevcut order/qc/return).
- Odaklı test: `bildirim.tests` **11 OK**. PDF/Celery/Next dışı.

### 2026-11-10 — ADR-0027 Kabul + migrate + cron
- Ürün sahibi Kabul; `bildirim` migrate; `seed_role_permissions`; RUNBOOK §11c cron (`process_outbox` → `process_email_queue`).

### 2026-11-10 — Denetim P0 dilimi (50-konu kalite)
- Outbox: handler yok → FAILED; `register_ack_handler` (`kur.alert`, `edi.punchout.inbound`).
- Payment: `tahsil_et` intent+order kilidi (ön + ledger).
- RUNBOOK zip/`.env` rotasyon notu (değer yazılmaz). Bilinçli açık: canlı ödeme/kargo, mutabakat, hak ediş derinliği.

### 2026-11-10 — Auth QA kapıları (şifre / login / MFA / prod)
- API: password-reset, password-reset/confirm, password-change; login gate (`aktif`+`onayli`); MFA e-posta OTP + middleware.
- Prod checks: LocMem E001, fake payment/carrier E002/E003; `ALLOW_*` bilinçli bypass.
- Test: `api.tests.test_auth_qa_gates` **8 OK** (tam suite yok).

### 2026-11-10 — Soft-launch yol A başlangıç
- `manage.py soft_launch_check` (+ `--allow-fake` / `--require-mfa` / `--strict`); RUNBOOK §11d.
- Odaklı test `firmalar.tests.test_soft_launch_check`; createcachetable + outbox/email smoke.

### 2026-11-10 — ADR-0028 davet + e-posta doğrulama (Taslak kod)
- `FirmaInvite` + `Kullanici.email_verified_at`; mig `firmalar.0012`.
- Servis: `invite_servisi` / `email_verify_servisi`; API invite create/list/accept + email-verify request/confirm.
- `/me.email_verified`; `EMAIL_VERIFY_REQUIRED_FOR_WRITE` → buyer commerce yazma kapısı (varsayılan kapalı).
- Admin: FirmaInvite (add yok); odaklı test **8 OK**. Ürün sahibi Kabul bekleniyor.

### 2026-11-10 — ADR-0029 API-only + ADR-0028 Kabul
- Ürün sahibi onay: `/buyer/` `/supplier/` `/ops/` HTML + `*_ui` + template silindi.
- `LOGIN_URL` → `/admin/login/`; `POST /api/v1/act-as/start|stop/`; `GET /me/dashboard/`.
- `FRONTEND_PORTAL_BASE_URL`; OpenAPI; HTML UI testleri API’ye taşındı / silindi.
- ADR-0028 **Kabul**; ADR-0021 HTML maddeleri supersede.

### 2026-11-11 — Docs↔kod audit (ADIM 0–5)
- Envanter: `docs/_audit/endpoint-inventory.md` (Django 104 route / OpenAPI 98 path / 106 op).
- Drift: OpenAPI↔kod path seti uyumlu; bayat HTML iddiaları (`API_CONTRACT` §4.9, MASTER/BACKLOG/ROADMAP/RUNBOOK/ADR-0017) koda göre güncellendi.
- FE→BE: Next yalnız `csrf/login/logout/me/health` çağırıyor; hepsi backend’de var.
- Smoke: `scripts/smoke_api.py` (+ sonuç FINAL-REPORT).

### 2026-11-11 — CRUD P0: teklif create + RFQ eşleştirme HTTP
- `POST /supplier/offers/` → `teklif_servisi.taslak_olustur` (tenant actor.firma).
- Ops: `/ops/rfq-lines/{line_id}/match-candidates|matches/` + `/ops/rfq-matches/{id}/approve|reject/`.
- OpenAPI 102 path / 112 op; API_CONTRACT §4.2–4.3 + FE-P1-RFQ **UYGULANDI**.
- FE feature `services/` tipli client (UI yok); FINAL-REPORT + crud-matrix.

### 2026-11-11 — NX-SHELL (P1)
- Next: `PortalShell` / `PortalNav` / `ThemeToggle` (`next-themes` class).
- shadcn-style `components/ui`: Button, Input, Label, Dialog; login form bağlandı.
- Kör havuz UI notu shell’de; Card/gradient yok.
- BACKLOG NX-SHELL **UYGULANDI**.

### 2026-11-11 — Audit kapanış (ADIM 1–8)
- WIP dilimli commit (ADR-0027/28/29 + integrity/ops); `makemigrations --check` OK.
- PG full suite **588 OK**; OpenAPI lint OK (98 path / 106 op).
- Smoke matrix: `api.tests.test_openapi_smoke_matrix` **276/276**; readiness yeniden üretildi.
- FE CSRF: `api.tests.test_fe_session_csrf_flow` (same-origin rewrite; CORS yok).
- Kapsam dışı (implement yok): teklif create + RFQ eşleştirme HTTP (`API_CONTRACT:106`, `API_READINESS:57`).
- Rapor: `docs/_audit/FINAL-REPORT.md`.

