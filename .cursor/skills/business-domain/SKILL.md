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
**Canonical:** `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md` (§5, §9, K-006–K-013, K-010)

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

**Catalog ownership (Faz 2):** `Urun.tedarikci` kaldırıldı → `olusturan_firma`; katalog platforma aittir. Teklif yaşam döngüsü (Faz 3.1): `fiyatlama.services.teklif_servisi` — durum yalnız servisten; alıcı/quote ADR-0008.

Two stone models exist (`urunler.UrunTasi` vs `fiyatlama.UrunTasi`) — rename pricing side toward offer stone cost (K-011) when touching that area.

## Pricing (K-009, K-013)

- Pure math: `fiyatlama.services.fiyat_hesaplama.hesapla` (keep pure; dilim 3.1 değiştirmedi).
- Offer gate (3a): `teklif_eslestirme_uygun_mu` — `eslestirme_durumu == onaylandi` + `hedef_urun` tutarlı; boş/onaysız teklif fiyata girmez.
- Orchestration belongs in a future `PricingService.quote()` (ADR-0008): rates, contract, offer version → immutable **PriceQuote** → lock on order.
- `PriceCalculationLog` is technical audit, **not** commercial truth.
- Formula components: metal (`gram × milyem × saf_birim_fiyat`) + işçilik + taş + extras + platform service + channel margin (+ configurable tax).
- Ambiguous contract resolution → error, do not guess (K-007/K-008; dilim 3.2).

## Stock (K-010)

Separate:

1. **Balance** — quantity on hand (offer/variant + supplier)
2. **Reservation** — checkout hold with TTL; cart does not decrement
3. **Movement** — immutable ledger of changes (sale, adjust, return)

Do not treat `Varyant.stok` and `TedarikciTeklif.stok_adet` as dual sources of truth. Direct count edits forbidden; corrections via movements.

## Commerce / ops state

Order transitions only via services with role + precondition + audit. No free-text status. Side flows (cancel/return/refund) are separate — no arbitrary rollback.

QC failure blocks shipment. Finance ledger: no delete; reverse with contra entries.

## When implementing

1. Read related existing models/services only.
2. Match rapor §9 behavior.
3. If detail missing: safe default + ADR under `docs/decisions/`.
4. Stop for irreversible finance/legal/security guesses.
