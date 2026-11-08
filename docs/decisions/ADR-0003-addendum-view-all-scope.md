# ADR-0003 Addendum — `view_all_tenants` daraltması

**Durum:** Kabul edildi (uygulama sonrası bilinçli sapma kaydı)  
**Tarih:** 2026-11-08  
**Üst ADR:** [ADR-0003](ADR-0003-faz1-kimlik-rbac.md)

## Karar

`firmalar.view_all_tenants` permission’ı **yalnızca** şu rollere seed edilir:

- `platform_super`
- `platform_admin`
- `platform_ops`
- `platform_finance`
- `platform_catalog`

**Verilmez:** `platform_quality`, `platform_logistics`, `platform_support`

## Gerekçe

`faz1-teknik-inceleme.md` §2.3’te bu üç rol için tenant-genel liste **S (sınırlı)** idi. İlk seed hepsine `view_all` vermişti; doğrulama turunda ADR-0003-05 senaryosu 7 (superuser sessiz aşım) ile çakışmayı önlemek ve “S = tam view_all değil” ilkesini korumak için daraltıldı.

Kod: `firmalar/role_permissions.py` (PLATFORM_QUALITY/LOGISTICS/SUPPORT → boş perm tuple).

## Sonuç

Bu roller platform firmasına bağlı olsa bile çapraz tenant listeleme yapamaz; QC/lojistik/destek için ileride dar scope permission’ları ayrı ADR ile eklenebilir.
