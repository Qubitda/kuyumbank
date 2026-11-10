# NOTE-F11-001 — Raporlama read-model v1 (teknik not)

**Tür:** Teknik not (F11-001 kabul: “ADR veya teknik not”)  
**Tarih:** 2026-11-10  
**Durum:** v1 teknik sabit · Product ADR maddeleri ayrı (Taslak bekler)

## v1 teknik kararlar (uygulama otoritesi — F11-011 ile hizalı)

| ID | Karar |
|----|--------|
| RM-1 | **Read path:** canlı ORM aggregate / annotate over transactional tables (`Order`, `OrderLine`, `PriceQuote`, `PriceLock`). Ayrı CQRS/OLAP tablo **yok** (v1). |
| RM-2 | **Tenant:** kesit `alici_firma_id` (veya actor.firma); client `firma_id` yok sayılır; çapraz tenant yasak. |
| RM-3 | **Kör havuz:** alıcı yüzeyinde tedarikçi kimliği / maliyet / marj kırılımı yok. |
| RM-4 | **Para:** Decimal; float yasak; tutarlar `snapshot_satir_tutari_vergisiz` / `toplam_vergisiz`. |
| RM-5 | **Yetki:** platform finans/ops (`view_all` + ilgili perm) veya alıcı yalnız kendi firması. |
| RM-6 | **Celery/materialized view yok** (v1); sync service çağrısı. |

## Product ADR’ye bırakılanlar (kod yok)

| ID | Konu |
|----|------|
| P-RM-1 | Ayrı warehouse / star-schema / gece ETL |
| P-RM-2 | Alıcı self-serve rapor portalı (FE) |
| P-RM-3 | Saklama / anonymization süresi |
| P-RM-4 | Object-level DRF rapor HTTP matrisi |
| P-RM-5 | Mahsup / finans iade rapor HTTP |

→ Bunlar Object-level DRF / Mahsup HTTP / FE ile birlikte ürün kararı.

## Kanıt zinciri

- F11-011 (quote/lock) zaten RM-1…6 uyguladı.
- Bu not F11-010 / F11-021 / F11-014’ü açar.
