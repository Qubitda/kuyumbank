# ADR-0011 — Faz 4 ticari çekirdek

**Durum:** **Kabul** (ürün sahibi, 2026-11-08)
**Uygulama:** F4 dilim 1–8 + PRE-001…004 UYGULANDI (bkz. [MASTER](../MASTER.md) §12)

> Bu dosya master §6.4'ten taşındı (2026-11-09).


**Amaç:** Çalışan B2B işlem çekirdeği — stok ledger → rezervasyon → sepet → checkout/lock → sipariş + fiyat snapshot.  
**Kapsam dışı:** Ödeme, cari/finans, QC, kargo, RFQ, B-01/B-06, konsinye/emanet (U-008).

## Varsayımlar (Kabul — F4-A1…A16)

| ID | Karar |
|----|--------|
| F4-A1 | Paketler: `stok` + `siparis` (ADR-0004 düzeni). Cart siparis app’te. |
| F4-A2 | **Warehouse:** platform veya tedarikçi sahibi; tenant selector; transfer UI yok. |
| F4-A3 | **StockMovement:** tek yazım kaynağı; immutable (app+DB); doğrudan balance edit yasak. |
| F4-A4 | **StockBalance:** projeksiyon; `available = on_hand − reserved − blocked` (Decimal). |
| F4-A5 | **StockReservation:** checkout hold + TTL; sepet stok düşürmez; expire → available geri. |
| F4-A6 | Oversell yok: `select_for_update` + PG test (F4-021). |
| F4-A7 | **Cart/CartLine:** alıcıya özel; kör havuz (tedarikçi/maliyet yok). |
| F4-A8 | **Checkout:** geçerli PriceLock + rezervasyon zorunlu; expired lock/quote → fail; idempotency key. |
| F4-A9 | **Order/OrderLine:** durum yalnız servis SM; serbest status yok; her geçiş audit. |
| F4-A10 | **L-11:** Order → PriceLock bağ (OneToOne veya PROTECT FK); satır fiyat snapshot quote/lock’tan kopya; sonradan değişmez; kur değişimi geçmişi etkilemez. |
| F4-A11 | Dual-stock: `Varyant.stok` / `TedarikciTeklif.stok_adet` yazma kapatılır → ledger; silent dual-write yok; kaldırma F4-070. |
| F4-A12 | Birim (U-002 **Kabul A**): `fiyat_modeli`→ADET (`SABIT_PARCA`) / GRAM (`METAL_BAZLI`,`GRAM_BIRIM`); **birimler arası dönüşüm/toplama yok**; balance anahtarı birim içerir. Legacy `stok`/`stok_adet` yalnız ADET semantiği — GRAM ledger’a kör kopya yasak. QC tolerans → Faz 6. |
| F4-A13 | Konsinye/emanet (U-008): **Faz 4 dışı**; yalnız sahipli depo stoku. |
| F4-A14 | HTTP (U-012 önerisi): **ince PRE-API** (DRF pin + health + cart/order iskelet + tenant test); tam Prosperer API yok. |
| F4-A15 | İptal (F4-053): stok iade movement; ödeme iadesi yok. |
| F4-A16 | Fail audit: domain_atomic dışı durable (mevcut desen). |

## Uygulama sırası

1. **F4-002 + F4-010 — UYGULANDI:** Warehouse, dual-stock envanter, birim  
2. **F4-011/012/013 — UYGULANDI:** Movement + Balance + düzeltme (`ledger_servisi`)  
3. **F4-020/021 — UYGULANDI:** StockReservation TTL + oversell (`reservation_servisi`); F4-022 expire görevi hâlâ backlog  
4. **F4-030/031 — UYGULANDI:** Cart/CartLine (`siparis`, `cart_servisi`)  
5. **F4-040/041 — UYGULANDI:** CheckoutAttempt + lock + rezervasyon; fail durable  
6. **F4-050/051/052 — UYGULANDI:** Order/OrderLine + L-11 snapshot + rezervasyon tüket  
7. **F4-053 — UYGULANDI:** sipariş iptal + stok IADE (finans yok)  
8. **F4-080 — UYGULANDI:** Quick Reorder (güncel quote; ATP fail-closed)  
9. **PRE-001…004 — UYGULANDI:** DRF pin + health/me/cart/order + OpenAPI schema  
10. PRE-005 idempotency / F4-081 bulk ← **sıradaki**  
11. F4-070 legacy stok / F4-090 outbox  

**Kabul kriterleri (özet):** oversell yok; expired lock checkout fail; OrderLine tutarı kurdan etkilenmez; tenant IDOR yok.
