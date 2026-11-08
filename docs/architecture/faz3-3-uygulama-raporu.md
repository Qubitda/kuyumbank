# Dilim 3.3 — Kur politikası uygulama raporu

**Tarih:** 2026-11-08  
**ADR:** ADR-0008 **Kabul** (B-02…B-05 + çoklu YAYINDA; B-01 hukuk dışı; B-06 erteli)  
**Kapsam:** Yalnız kur politikası — quote motoru / CurrencyConversion / PriceQuote **yok**.

## Tamamlananlar

- Ürün kararları ADR-0008 + `docs/adr-0008-urun-kararlari.md` kayıtları.
- `KurSaglayici` (tek aktif), `KurPolitikasi` (ayrı alıcı/tedarikçi tipi).
- `MetalKuru` / `DovizKuru` gözlem alanları (sağlayıcı, kur tipi, alınma, manuel audit alanları).
- `SatisKanali.quote_ttl_saniye` (B-03 konfig saklama).
- `tanimlar.services.kur_servisi`: aktif provider, stale kontrol, resolve (fail-closed), manuel dört göz, feed yazımı.
- Yetki: `tanimlar.manage_kur` → platform super/admin/finance matrisi.
- Migration: `tanimlar.0002_faz3_3_kur_politikasi` (+ `0003` index rename).

## Bilinçli dışı

- B-01 gizli hizmet payı; B-06 vergi; PricingService.quote; çoklu YAYINDA seçim kodu (3.5+).

## Riskler

| Risk | Etiket |
|------|--------|
| Kur sağlayıcı lisans / sözleşme | DOĞRULANAMADI (§6 dış doğrulama) |
| Üretimde mevcut kur satırı backfill | Yerel migrate OK; staging/prod envanteri bu turda yok |
| Quote TTL sayısal değerleri finans tarafından doldurulmalı | PLANLAMA — aksi halde 3.5 fail-closed |
