# Dilim 3.5 — PriceQuote + PricingService.quote + immutability

**Tarih:** 2026-11-08  
**ADR:** ADR-0008 **Kabul** §2.4 / §2.4.1 / B-03  
**Kapsam dışı:** B-01 platform_servis, B-06 vergi, kör havuz alıcı UI (3.6), K-011 taş rename (3.6), PriceLock (3.7/Faz 4).

## Orkestrasyon

`fiyatlama.services.pricing_service.quote(alici_firma, satis_kanali, varyant, …)`:

1. Yayınlı ürün (`yayin_durumu=aktif`, `onayli`) + aktif varyant  
2. Kanal `quote_ttl_saniye` (yoksa fail-closed)  
3. Alıcı/tedarikçi metal kuru resolve (B-05; stale → hata)  
4. Teklif: YAYINDA + geçerli + `teklif_eslestirme_uygun_mu`; seçim `oncelik`↓ → iç maliyet↑ → `id`↑  
5. `cozumle` ALICI zorunlu; TEDARIKCI koşullu (belirsiz → hata)  
6. PB dönüşüm + `hesapla_teklif_kalemleri` (3.4)  
7. TTL ≤ aktif sağlayıcı `max_gecikme_saniye`  
8. `PriceQuote` + `PriceQuoteLine` (proforma; `toplam_vergisiz`)

## İmmutability

- Uygulama: `save` yalnız insert; `delete` yasak  
- DB: `BEFORE UPDATE OR DELETE` trigger (`0007_faz3_5_price_quote`)

## Dosyalar

- `fiyatlama/models/price_quote.py` — PriceQuote / Line  
- `fiyatlama/services/pricing_service.py` — quote + teklif seçimi  
- `fiyatlama/migrations/0007_faz3_5_price_quote.py`  
- `fiyatlama/tests/test_price_quote.py`  
- Admin salt okunur; selector tenant scope  

## Migration

`fiyatlama.0007_faz3_5_price_quote` — CreateModel + immutability trigger.
