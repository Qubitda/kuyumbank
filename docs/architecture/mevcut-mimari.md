# Mevcut mimari (Faz 2.1 sonrası envanter)

**Tarih:** 2026-11-08  
**Runtime:** Python 3.14.6 · Django 6.1.2 · PostgreSQL  
**Kod kökü:** `Backend/config/`  
**Bağlı ADR:** 0003–0006 (Kabul); 0007 Faz 3 fiyatlama (**Taslak**)

## Uygulama haritası

| App | Sorumluluk | Servis / selector |
|-----|------------|-------------------|
| `firmalar` | `Firma`, `Kullanici`, adres, banka, `AuditOlay`, RBAC seed | `rol_servisi`, `yetki_servisi`, `audit_servisi` (`domain_atomic` / durable), `selectors/tenant` |
| `tanimlar` | Metal, milyem, metal/döviz kuru, fiyat grubu, satış kanalı | admin + seed; kur politikası Faz 3 (ADR-0007) |
| `urunler` | Kategori, `Urun` (`olusturan_firma`, kimlik A/B/C), varyant, katalog taşı, onay/eşleştirme | `onay_servisi`, `eslestirme_servisi`, `katalog_tenant`, gram bandı |
| `fiyatlama` | Sözleşme, `TedarikciTeklif` (3 fiyat modeli), teklif taşı, `hesapla()`, `cozumle()`, `PriceCalculationLog` | `fiyat_hesaplama` (saf; yalnız metal formülü); teklif/sözleşme **durum servisi yok** (ADR-0006 bilinçli sınır → Faz 3) |

`AUTH_USER_MODEL = firmalar.Kullanici`. Paket düzeni: ADR-0004 (`models/`, `services/`, `selectors/`, `admin/`, `tests/`).

## HTTP yüzeyi

`config/urls.py` → `admin/`. DRF / public API yok (Faz 7).

## Kimlik ve yetki (Faz 1 / 1.1)

- Kullanıcı: tek `firma` (NOT NULL) + tek `rol`; `save()` → `full_clean()` **tüm kullanıcılar** (superuser muafiyeti yok — ADR-0003).
- İş yetkisi: `has_perm` / `require_perm` + rol grubu matrisi; `is_superuser` tenant/perm kısa yolu **yok**.
- Tenant: `selectors` + admin `get_queryset` / FK scope; `view_all_tenants` yalnız platform + perm.
- Fail audit: `record_audit_durable` (domain_atomic dışı; dış atomic’te sidecar — ADR-0006 O3).

## Katalog (Faz 2 / 2.1)

- Katalog ürünü **platforma** aittir; `Urun.tedarikci` **kaldırıldı** → `olusturan_firma` (alıcıya gösterilmez).
- Onay akışı serviste; tedarikçi `onay_bekliyor` düzenleyemez; `geri_cek` / `taslaga_al`; dört göz onay.
- Kimlik unique: A/B + dolu anahtar + `onay_durumu != reddedildi` (0007).
- Eşleştirme: tedarikçi önerir, platform onaylar; `eslestirme_durumu` boş = quote için yetersiz (ADR-0007 taslak).

## Fiyatlama (mevcut — Faz 3 öncesi)

```mermaid
flowchart TD
  Firma[Firma]
  Kullanici[Kullanici]
  Urun[Urun olusturan_firma]
  Varyant[Varyant]
  Teklif[TedarikciTeklif]
  Sozlesme[FiyatSozlesmesi]
  Hesapla[hesapla metal formulu]
  Log[PriceCalculationLog]
  Kullanici --> Firma
  Urun -->|"olusturan_firma"| Firma
  Urun --> Varyant
  Teklif -->|"PROTECT tedarikci"| Firma
  Teklif -->|"CASCADE varyant — Faz3 PROTECT"| Varyant
  Sozlesme --> Firma
  Hesapla -.->|"orkestrasyon yok"| Log
```

- Üç teklif modeli: `METAL_BAZLI`, `GRAM_BIRIM`, `SABIT_PARCA` — quote eşlemesi ADR-0007.
- Faz 3 çıktısı proforma; KDV/vergi yok.
- `PriceQuote` / `PricingService` yok; admin’de teklif `durum` salt okunur.

## Bilinçli hedef (rapor §10)

Modular monolith; domain service; alıcı fiyatı `PriceQuote` + lock (Faz 3/4); stok üçlüsü Faz 4.

## Bağımlılıklar

`Backend/config/requirements.txt` · `.env` / `.env.example` (secret repoya girmez)
