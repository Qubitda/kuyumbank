# Dilim 3.4 — Üç model hesap + CurrencyConversion

**Tarih:** 2026-11-08  
**ADR:** ADR-0008 **Kabul** §2.1.1 / K-012  
**Kapsam dışı:** PriceQuote, `PricingService.quote`, B-01 platform_servis, B-06 vergi, kör havuz UI.

## Formüller (hedef PB’de, Decimal)

| Model | Ana kalem | + ortak |
|-------|-----------|---------|
| METAL_BAZLI | `metal = gram × milyem × saf_birim_fiyat` (milyem 0–1 oran) | `iscilik` + `kanal_marj` + `tas` + `ek_bedel` |
| GRAM_BIRIM | `gram_birim = gram × birim_fiyat` | `kanal_marj` + `tas` + `ek_bedel` (metal yok) |
| SABIT_PARCA | `sabit_parca = birim_fiyat` (gram çarpılmaz) | `kanal_marj` + `tas` + `ek_bedel` |

Marj: `YUZDE` / `TL_GR` / `TL_PARCA` (mevcut sözleşme semantiği).  
Yuvarlama: ara adım yok; `toplam_vergisiz` = HALF_UP `0.01`.

## CurrencyConversion

- `DovizKuru.kur` = TRY per 1 FX.
- FX→TRY: ×kur · TRY→FX: ÷kur · FX→FX: TRY pivot.
- Taraf → `KurPolitikasi` kur tipi; stale/eksik → hata; sabit gözlem sessiz yenilenmez.
- TRY dışı quantize: geçici `0.01` HALF_UP (ADR §6 muhasebe doğrulaması açık).

## Dosyalar

- `fiyatlama/services/fiyat_hesaplama.py` — üç model + `hesapla` uyumluluk
- `fiyatlama/services/fiyat_motoru.py` — PB dönüşümü + model çağrısı
- `tanimlar/services/currency_conversion.py` — K-012 servis
- Testler: `test_uc_model_hesaplama`, `test_fiyat_motoru`, `test_currency_conversion`

## Migration

Yok (şema değişmedi).
