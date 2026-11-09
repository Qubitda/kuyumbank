---
name: business-domain
description: >-
  Kuyumbank jewelry B2B domain rules: platform firm, catalog vs supplier offer,
  pricing quote/snapshot, stock reservation/movement/balance, order/RFQ/QC
  state machines. Use when designing or changing firmalar, urunler, fiyatlama,
  or future siparis/stok/finans modules.
---

# Business Domain (Kuyumbank)

**Prepared for:** Django **6.1** + Kuyumbank rapor v1.0  
**Canonical:** `docs/MASTER.md` + `docs/ROADMAP.md` / `docs/BACKLOG.md`; ADR → `docs/decisions/`

Django docs explain *how* to implement; this skill states *what* Kuyumbank must enforce.  
Field presence ≠ rule enforcement. Label uncertain claims DOĞRULANAMADI / PLANLAMA BULGUSU.

## Platform and firms

- One platform firm; buyers and suppliers are other firms (a firm may be both with separate permission sets).
- Users: one firm + one business role; passive firm → no ops.
- Platform mediates operations; buyers and suppliers do not meet directly.

## Catalog vs offer (K-006)

| Concept | Owner | Notes |
|---------|-------|-------|
| Catalog product / variant | **Platform** | Not owned by a single supplier long-term |
| Supplier offer (`TedarikciTeklif`) | Supplier | Many offers per variant |
| Buyer price | Platform quote | Never raw supplier cost |

**Catalog ownership (Faz 2):** `Urun.tedarikci` kaldırıldı → `olusturan_firma`; katalog platforma aittir. Teklif yaşam döngüsü (Faz 3.1): `fiyatlama.services.teklif_servisi` — durum yalnız servisten. Sözleşme K-007/K-008 (3.2): `sozlesme_servisi` + `cozumle`. Kur politikası (3.3): `tanimlar.services.kur_servisi` — tek aktif provider, stale fail-closed. Quote (3.5): `pricing_service.quote` → immutable `PriceQuote`.

K-011 (3.6): katalog `urunler.UrunTasi` (ProductStone) korunur; teklif maliyeti `fiyatlama.TeklifTasMaliyeti` (eski `fiyatlama.UrunTasi`). Quote taş bedeli yalnız teklif modelinden.

## Pricing (K-009, K-013)

- Pure math (3.4): `fiyat_hesaplama` — `hesapla_metal_bazli` / `hesapla_gram_birim` / `hesapla_sabit_parca` (+ legacy `hesapla`); Django-free; `toplam_vergisiz` HALF_UP 0.01.
- PB dönüşüm (3.4): `tanimlar.services.currency_conversion` — TRY per FX; taraf kur tipi; stale fail-closed.
- Offer gate (3a): `teklif_eslestirme_uygun_mu` — `eslestirme_durumu == onaylandi` + `hedef_urun` tutarlı; boş/onaysız teklif fiyata girmez.
- Rates (3.3): resolve via `kur_servisi` (buyer/supplier `kur_tipi` ayrı; no provider fallback).
- Orchestration (3.5): `pricing_service.quote()` — rates, ALICI `cozumle` (zorunlu), offer selection, immutable **PriceQuote**+Line. KS-6: `hedef_toplam=` platform `manage_sozlesme` (banka/GV quote’a girmez).
- Lock (3.7 / ADR-0010 **Kabul**): `pricing_service.lock_quote()` — geçerli quote; yeniden hesap yok; TTL=quote; L-07 `lock_quote` / `lock_quote_on_behalf` (+ on-behalf gerekçe). L-11: `OrderLine.price_lock` OneToOne + satır snapshot (F4-051). PriceLock’ta `has_adet` yok.
- Buyer surface (3.6 / B-02): `selectors.buyer_quote` — yalnız `toplam_vergisiz` (+ gram başı); satır/tedarikçi/maliyet yok; IDOR → DoesNotExist.
- `PriceCalculationLog` is technical audit, **not** commercial truth.
- Formula components: metal (`gram × milyem × saf_birim_fiyat`) + işçilik + taş + extras + platform service + channel margin (+ configurable tax). B-01 servis payı kalemi hukuk öncesi kodlanmaz; B-06 vergi Faz 3’te yok (proforma).
- Ambiguous contract resolution → error, do not guess (K-007/K-008; dilim 3.2).

## Stock (K-010) — `stok` app (F4 dilim 1–3 UYGULANDI)

Separate (DOĞRULANDI):

1. **StockBalance** — `available = on_hand − reserved − blocked`; anahtar warehouse+teklif+birim
2. **StockReservation** — TTL hold; create/cancel/expire yalnız `reserved` (movement yok); consume → SATIS
3. **StockMovement** — immutable ledger (GIRIS/CIKIS/DUZELTME/…); `ledger_servisi`

Birim (U-002): teklif `fiyat_modeli` → ADET/GRAM; **dönüşüm yok**.  
Stok truth: ledger (`StockMovement`/`StockBalance`); legacy dual kolon F4-070b ile kaldırıldı.  
`siparis`: Cart/CartLine → CheckoutAttempt (lock+rezerv) → Order/OrderLine (tüket SATIS) → iptal (IADE); Quick Reorder → güncel quote+ATP (`reorder_servisi`).

## Commerce / ops state

Cart/Checkout/Order/Reorder **UYGULANDI** (`siparis`); ince PRE HTTP (`api`, okuma iskeleti). Transitions yalnız servis + audit.  
Finance (ADR-0012 **Kabul**): `finans.LedgerEntry` (append-only + contra); `HedgeEntry` + `fx_servisi.open_has` (interim Quote.gram). Cari F5-011. Ödeme iadesi yok (U-004). Sıradaki: master §12.3.

## When implementing

1. Read related existing models/services only.
2. Match rapor §9 behavior.
3. If detail missing: safe default + Taslak ADR under `docs/decisions/`.
4. Stop for irreversible finance/legal/security guesses.
