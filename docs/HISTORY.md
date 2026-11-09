# Faz tarihçesi

> Yalnız eklenir. Eski bulgular otomatik olarak güncel durum değildir; güncel durum için [MASTER](MASTER.md) §2 ve §12.

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

### Açık temalar
B-01/B-06; dual stock (F4-070); DRF yok; TRY dışı yuvarlama; U-003…011, U-014/015.

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
