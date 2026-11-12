# ADR-0032 — OpenAPI → TypeScript codegen (`schema.d.ts`)

**Durum:** **Taslak** (CI `--check` drift henüz bağlanmadı) — FAZ 1 ile `npm run generate:api` + `schema.d.ts` uygulandı (ürün sahibi FAZ 1 talimatı, 2026-11-12)  
**Bağımlılık:** [ADR-0017](ADR-0017-nextjs-api-sozlesmesi.md) (OpenAPI normatif) · [ADR-0031](ADR-0031-vite-spa-portal.md) (Vite SPA)  
**İlişki:** `docs/api/openapi-v1.json` tek şema kaynağı; FE `src/lib/api/types.ts` şu an elle

## Bağlam

Vite portal tipleri OpenAPI’den üretilmiyor; `generate:api` script’i yok. Elle tipler drift riski taşır. Normatif dosyalar repo kökünde (`docs/API_CONTRACT.md`, `docs/api/openapi-v1.json`); `frontend/` içinde kopya yok.

## Öneri (Kabul sonrası)

| Konu | Öneri |
|------|--------|
| Araç | `openapi-typescript` (veya eşdeğer) — yalnız **tipler**, runtime client generate yok |
| Girdi | `../docs/api/openapi-v1.json` |
| Çıktı | `frontend/src/lib/api/schema.d.ts` (git’te commit; CI `--check` drift) |
| Script | `npm run generate:api` → tek komut; README’de belgelenir |
| Elle tipler | `types.ts` şemaya re-export / daraltma; domain feature types OpenAPI path şemasına dayanır |
| Yasak | Sahte endpoint için elle “çalışıyormuş” tip; mock alan adları |

## Sonuçlar (Kabul edilirse)

- Backend OpenAPI değişince FE tip güncellemesi zorunlu (CI kırmızı).
- Mevcut elle `types.ts` aşamalı migrasyon; big-bang zorunlu değil.

## Kabul öncesi

Kod/script **yazılmaz**. Bu ADR **Taslak** kalır.
