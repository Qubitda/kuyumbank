# ADR-0025 — Pano ONS/KG çapraz satırlar (CAP-PANO-v2.1)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “kalan işten devam”)  
**Bağımlılık:** ADR-0022 V2-3; ADR-0018 kur/döviz  
**Kapsam ID:** CAP-PANO-v2.1

## Kararlar

| ID | Karar |
|----|--------|
| OX-1 | `PiyasaUrun.olcek`: `GRAM` \| `ONS` \| `KG` (varsayılan GRAM). |
| OX-2 | `PiyasaUrun.cikti_pb`: `TRY` \| `USD` (varsayılan TRY). |
| OX-3 | Ham (marj öncesi): GRAM·TRY = saf×milyem×miktar; KG·TRY = saf×milyem×1000×miktar; ONS·TRY = saf×TROY×milyem×miktar; `*·USD` = TRY-ham / USDTRY (`resolve_doviz_kuru`). |
| OX-4 | `TROY` = `tanimlar.fiyat_kaynagi.TROY_OZ_GRAM`. `gram` alanı = miktar çarpanı (1 oz / 1 kg / 1 gr). |
| OX-5 | `baz_fiyat` / `pano_ozeti` çıktısına `olcek`, `cikti_pb` eklenir. Seed: örnek `ons_usd`, `has_kg`. |
| OX-6 | HTTP yok; FE yok. |

## Checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** |
| Model + mig + servis + test | Bu dilim |
