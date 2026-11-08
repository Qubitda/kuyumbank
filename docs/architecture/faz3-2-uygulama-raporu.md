# Faz 3a / Dilim 3.2 — K-007 / K-008 uygulama raporu

**Tarih:** 2026-11-08  
**ADR:** 0007 (Kabul) §2.2–2.3  
**Durum:** Uygulandı

## Seçimler (gerekçe)

| Konu | Seçim | Gerekçe |
|------|--------|---------|
| K-007 unique | `UniqueConstraint(..., nulls_distinct=False)` on `(sozlesme, metal, ayar)` | Django 6.1 PostgreSQL API; tek constraint; NULL metal/ayar tekilliği |
| K-008 çakışma | `ExclusionConstraint` + `btree_gist` + `COALESCE(satis_kanali_id,0)` + `daterange(..., '[]')` | ADR-0007 tercih; yerel extension **1.8 DOĞRULANDI** |
| `cozumle` sıra | kanal → ayar → versiyon | Görev / K-007 rapor sırası |
| Servis | `sozlesme_servisi` + servis overlap kontrolü | Friendly hata; exclusion ile aynı semantik |

## Değişen dosyalar

| Dosya | Sorumluluk |
|-------|------------|
| `fiyatlama/models/fiyat_sozlesmesi_kalemi.py` | K-007 unique + clean (AKTIF kilit, duplicate) |
| `fiyatlama/models/fiyat_sozlesmesi.py` | K-008 ExclusionConstraint + DateRange |
| `fiyatlama/models/sozlesme_cozumleme.py` | Öncelik sırası |
| `fiyatlama/services/sozlesme_servisi.py` | aktif/pasif/versiyon + manage_sozlesme + audit |
| `fiyatlama/admin/admin.py` | AKTIF readonly + action→servis |
| `fiyatlama/migrations/0006_faz3_2_k007_k008.py` | BtreeGistExtension + constraints |
| `config/settings.py` | `django.contrib.postgres` |
| `fiyatlama/tests/test_k007_*`, `test_k008_*`, `test_migration_0006.py` | Kapsam testleri |

## Testler (DOĞRULANDI)

```text
python manage.py check → 0 issue
python manage.py makemigrations --check --dry-run → No changes detected
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests
→ Ran 195 tests — OK (~280s)
```

## Açık / DOĞRULANAMADI

- Üretim hosting’de `btree_gist` yetkisi **DOĞRULANAMADI** (ADR-0007). Extension kurulamazsa servis kilidi zaten var; exclusion migration üretimde ayrıca doğrulanmalı.
- Mevcut yerel DB’de sözleşme satırı 0 — constraint öncesi çakışma yoktu (**DOĞRULANDI**).
