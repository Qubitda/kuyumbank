# Faz 1 — Uygulama raporu

**Tarih:** 2026-11-08  
**ADR:** 0003, 0004  
**Durum:** Tamamlandı (yerel DB migrate + 35 test OK)

## Değiştirilen / oluşturulan dosyalar (sorumluluk)

| Dosya | Sorumluluk |
|-------|------------|
| `firmalar/roles.py` | Kanonik rol sabitleri |
| `firmalar/role_permissions.py` | Merkezi rol→perm matrisi + idempotent seed |
| `firmalar/models/firma.py` | `firma_kodu`, Meta.permissions |
| `firmalar/models/kullanici.py` | 8 platform rolü, NOT NULL firma, superuser bypass kaldırıldı, manager |
| `firmalar/models/audit_olay.py` | Audit kaydı |
| `firmalar/services/*` | rol, yetki, platform kurulum, audit |
| `firmalar/selectors/tenant.py` | Tenant scope okuma |
| `firmalar/admin/*` | save_model / get_queryset scope |
| `firmalar/management/commands/bootstrap_platform.py` | Geçiş backfill |
| `firmalar/management/commands/seed_role_permissions.py` | Seed |
| `firmalar/migrations/0002–0004_*` | Şema + backfill + NOT NULL |
| `urunler/models/urun.py` | Meta.permissions |
| `urunler/services/onay_servisi.py` | K-004 sahiplik + perm; platform perm |
| `fiyatlama/models/*` | Meta.permissions |
| `*/tests/*` | Tenant + K-004 + mevcut suite güncellemesi |

## Testler (DOĞRULANDI)

```text
python manage.py check → 0 issue
python manage.py test firmalar.tests urunler.tests fiyatlama.tests.test_fiyat_hesaplama
→ Ran 35 tests — OK
python manage.py audit_user_assignments → tutarlı
```

## Riskler

- Admin `KullaniciAdmin.save_model` assign + UserAdmin save birleşimi; production admin UX manuel doğrulanmalı.
- `view_all_tenants` quality/logistics/support’ta yok; ihtiyaç ayrı ADR/seed güncellemesi ister.
- Üretim DB’sinde migrate bu oturumda çalıştırılmadı (yalnızca yerel geliştirme).
