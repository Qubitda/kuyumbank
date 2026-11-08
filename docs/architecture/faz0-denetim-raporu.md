# Faz 0 — Denetim raporu

**Tarih:** 2026-11-08 (kanıt sınıfları ile güncellendi)  
**Kaynak şartname:** `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md`  
**İlgili:** [Git/doküman denetimi](faz0-git-ve-dokuman-denetimi.md) · [Tenant güvenlik](faz0-tenant-guvenlik-denetimi.md) · [Faz 1 tasarım](faz1-kimlik-gecis-tasarimi.md)

**Uygulama Python değişikliği (Faz 0):** Yok — Ek kural B; ayrıntı git denetiminde.

## 1. Sürüm ve ortam

| Bileşen | Değer | Sınıf |
|---------|--------|-------|
| Python | 3.14.6 | DOĞRULANDI (`python --version`) |
| Django | 6.1.2 | DOĞRULANDI (`django.get_version` / pip) |
| django-environ | 0.12.0 | DOĞRULANDI (pip; settings import) |
| django-import-export | 4.4.3 | DOĞRULANDI (pip) |
| psycopg | 3.3.6 | DOĞRULANDI (pip) |
| Django 6.1 Python matrisi | 3.12–3.14 | DOĞRULANDI ([FAQ](https://docs.djangoproject.com/en/6.1/faq/install/)) |
| DRF/Celery ortamda yüklü | Evet | DOĞRULANDI (pip freeze) |
| DRF/Celery proje kullanımı | Hayır | DOĞRULANDI (INSTALLED_APPS / urls) |

### Çalıştırılan komutlar

| Komut | Sonuç | Sınıf |
|-------|--------|-------|
| `python manage.py check` | 0 issue | DOĞRULANDI |
| `python manage.py test urunler.tests fiyatlama.tests.test_fiyat_hesaplama tanimlar.tests` | 23 OK | DOĞRULANDI |
| Tenant / firmalar güvenlik testleri | Suite yok | DOĞRULANDI (yokluk) |
| Üretim check/migrate | Çalıştırılmadı | DOĞRULANAMADI |

## 2. Gap matrisi (etiketli)

| ID | Konu | Sınıf | Kanıt (özet) |
|----|------|-------|----------------|
| K-001 | API yok | DOĞRULANDI | `urls.py` L20–22 yalnız admin |
| K-002 | Tenant runtime yok | DOĞRULANDI | Middleware/manager/permission yok; ayrıntı tenant denetimi T-05/T-11 |
| K-003 | superuser bypass | DOĞRULANDI | `kullanici.py` L103; `onay_servisi.py` L29 |
| K-004 | `onaya_gonder` sahiplik yok | DOĞRULANDI | `onay_servisi.py` L78–94 `kullanici` kullanılmıyor |
| K-005 | Rol sync/admin/perm seed zayıf | DOĞRULANDI | `assign_user_role` var; admin `save_model` yok; perm seed yok |
| K-006 | Katalog tedarikçiye bağlı | DOĞRULANDI | `Urun.tedarikci` FK |
| K-007/8 | Sözleşme çakışma | PLANLAMA BULGUSU | Kod okuması + rapor; exclusion constraint runtime test yok |
| K-009 | Quote/lock yok | DOĞRULANDI | Model/app yok; yalnız `hesapla` + log |
| K-010 | Çift stok alanı | DOĞRULANDI | `Varyant.stok`, `TedarikciTeklif.stok_adet` |
| K-011 | İki `UrunTasi` | DOĞRULANDI | urunler + fiyatlama modelleri |
| K-013 | Ticari snapshot yok | DOĞRULANDI | `PriceQuote` yok |
| K-014 | MEDIA ayarı | DOĞRULANDI | settings’te MEDIA_* yok; ImageField var |
| K-020 | Kritik test eksik | DOĞRULANDI | firmalar tests yok; 23 test katalog/hesap |
| K-022 | AuditEvent yok | DOĞRULANDI | model/app yok |
| Kör havuz | Uygulanmamış | DOĞRULANDI | API/maskeleme yok; admin tedarikçi gösterir |

## 3. Migration envanteri

| App | Dosyalar | Data mig. | Sınıf |
|-----|----------|-----------|-------|
| firmalar | 0001_initial | Yok | DOĞRULANDI |
| tanimlar | 0001_initial | Yok | DOĞRULANDI |
| urunler | 0001–0003 | Yok | DOĞRULANDI |
| fiyatlama | 0001_initial | Yok | DOĞRULANDI |

## 4. Faz 0 teslimatları

Allowlist: [faz0-git-ve-dokuman-denetimi.md](faz0-git-ve-dokuman-denetimi.md) §1.

## 5. Sonraki adım

Kod yazmadan: [faz1-kimlik-gecis-tasarimi.md](faz1-kimlik-gecis-tasarimi.md) onaylanacak. Onay sonrası Faz 1 uygulaması ayrı talimatla başlar.
