# ADR-0030 — Platform ürün CRUD HTTP (CAP-URUN-CRUD-HTTP)

**Durum:** **Kabul** (2026-11-11, ürün sahibi Qubit)  
**Tarih:** 2026-11-11  
**Bağımlılık:** ADR-0005 (katalog ownership), ADR-0006 (onay), ADR-0017 (API sözleşme), ADR-0029 (API-only)  
**Kapsam:** Platform katalog yazma yüzeyi Admin dışı; FE `/admin` ürün dilimi

## Amaç

Buyer `GET /catalog/` yalnız yayınlı okur. Platform ürün oluşturma / onaya gönderme / onay / yayın için ince HTTP.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| U-1 | Yazma uçları `submit_urun` / `approve_urun` / `publish_urun`. Alıcı/tedarikçi yazamaz. |
| U-2 | Path öneki: `/api/v1/ops/products/` (buyer `/catalog/` salt okuma). |
| U-3 | İş kuralları `katalog_yazma_servisi` + `onay_servisi`; view ince. |
| U-4 | Ops DTO’da tedarikçi maliyet/SKU yok; `olusturan_firma_id` yalnız ops. |
| U-5 | Onay/yayın SM mevcut; sessiz overwrite yok. |
| U-6 | Idempotency-Key yazmalarda; OpenAPI + export + FE generate. |

## Kapsam dışı (bilinçli)

Toplu CSV import · görsel MEDIA signed URL · tedarikçi ürün taslağı HTTP (ayrı dilim).

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-11) |
| Servis + HTTP + test + OpenAPI | UYGULANDI |
| FE admin ürün paneli | UYGULANDI (minimal) |
