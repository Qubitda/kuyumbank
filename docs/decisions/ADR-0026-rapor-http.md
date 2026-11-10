# ADR-0026 — Rapor / anomali HTTP (OL-7 açılımı)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “go hepsini onaylıyorum”)  
**Bağımlılık:** ADR-0019 OL-7; F11-010/014/021; NOTE-F11-001 RM-1…6  
**Kapsam ID:** CAP-RAPOR-HTTP

## Kararlar

| ID | Karar |
|----|--------|
| RH-1 | `GET /api/v1/reports/orders/` → `ticari_siparis_ozet` (opsiyonel `?alici_firma_id=` platform). |
| RH-2 | `GET /api/v1/reports/buyer-behavior/` → `alici_davranis_ozet` (`alici_firma_id` platform için zorunlu). |
| RH-3 | `GET /api/v1/ops/anomalies/ciro/` → `ciro_esik_tara` (`esik_ciro` zorunlu; opsiyonel `alici_firma_id`). |
| RH-4 | Yetki/tenant serviste; client `firma_id` yok sayılır; kör havuz. |
| RH-5 | FE portal bu ADR’de yok; yalnız HTTP + OpenAPI + test. |

## Checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** |
| Kod + OpenAPI + test | Bu dilim |
