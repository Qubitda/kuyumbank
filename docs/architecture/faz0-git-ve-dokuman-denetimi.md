# Faz 0 — Git diff ve dokümantasyon denetimi

**Tarih:** 2026-11-08  
**Amaç:** Ek kural B’ye göre Faz 0 değişiklik sınırını doğrulamak; kanıt sınıflarını (Ek kural A) uygulamak.

## 1. Faz 0 dosya allowlist (bu fazın ürünü)

### Oluşturulan

| Dosya |
|-------|
| `AGENTS.md` |
| `.cursor/rules/kuyumbank-core.mdc` |
| `.cursor/skills/django-engineering/SKILL.md` |
| `.cursor/skills/multi-tenant-security/SKILL.md` |
| `.cursor/skills/business-domain/SKILL.md` |
| `.cursor/skills/testing-quality/SKILL.md` |
| `Backend/README.md` |
| `docs/analysis/README.md` |
| `docs/architecture/mevcut-mimari.md` |
| `docs/architecture/faz0-denetim-raporu.md` |
| `docs/architecture/faz0-git-ve-dokuman-denetimi.md` (bu dosya) |
| `docs/architecture/faz0-tenant-guvenlik-denetimi.md` |
| `docs/architecture/faz1-kimlik-gecis-tasarimi.md` |
| `docs/decisions/README.md` |
| `docs/decisions/ADR-0001-agent-standartlari.md` |
| `docs/decisions/ADR-0002-runtime-ve-bagimliliklar.md` |

### Değiştirilen (Faz 0 bilerek)

| Dosya | Neden |
|-------|--------|
| `Backend/config/requirements.txt` | Bağımlılık bildirimi düzeltildi (doğrudan deps; ortamla hizalı) |
| `Backend/config/.env.example` | Örnek secret/DB kimlik bilgisi kaldırıldı; placeholder |

## 2. Uygulama kodu — Ek kural B doğrulaması

**DOĞRULANDI:** Faz 0 allowlist’inde `Backend/config/**/*.py` (models/views/services/migrations) yok.

Working tree’de görülen geniş `firmalar`/`tanimlar`/`urunler`/`fiyatlama` yeniden düzenlemesi (düz dosyadan paket yapıya geçiş, silinen `models.py` vb.) **Faz 0 ürünü değildir**; önceden mevcut WIP olarak korunmuştur (Ek kural B: mevcut Git değişiklikleri ezilmez).

Doğrulama komutu (allowlist dışı app py değişikliğinin Faz 0’a ait olmadığını göstermek için):

```text
git status --short -- AGENTS.md .cursor docs/analysis docs/architecture docs/decisions Backend/README.md Backend/config/requirements.txt Backend/config/.env.example
```

Beklenen: yalnızca yukarıdaki allowlist dosyaları (ve bu denetim turunda eklenen mimari md’ler).

**DOĞRULANDI:** Veritabanı şeması / migration dosyası Faz 0’da oluşturulmadı veya değiştirilmedi (Faz 0 allowlist’te migration yok).  
**DOĞRULANAMADI:** “Üretim veritabanına bağlanılmadı” — üretim erişimi bu oturumda yok; bağlanılmadığı varsayımı ortam sınırından gelir, canlı kanıt yok.

## 3. Bağımlılık düzeltmesi (kullanıcı geri bildirimi)

| Konu | Sınıf | Kanıt |
|------|-------|--------|
| `settings.py` `import environ` | DOĞRULANDI | `Backend/config/config/settings.py` L10 |
| `import_export` INSTALLED_APPS | DOĞRULANDI | `settings.py` L56 |
| HEAD `requirements.txt` içinde `django-environ` yok | DOĞRULANDI | `git show HEAD:Backend/config/requirements.txt` |
| Ortamda `django-environ==0.12.0` | DOĞRULANDI | `pip freeze` (Faz 0’da kuruldu) |
| Ortamda `psycopg==3.3.6`, `psycopg2` yok | DOĞRULANDI | `pip freeze` / `pip show` |
| HEAD requirements `psycopg2==2.9.13` | DOĞRULANDI | git show HEAD |
| Ortamda DRF/Celery yüklü | DOĞRULANDI | `pip freeze` |
| DRF/Celery projede kullanılıyor | DOĞRULANDI (hayır) | `INSTALLED_APPS` ve urls yalnızca admin; requirements’a **eklenmedi** |
| Transitive pin’ler (asgiref/sqlparse…) | PLANLAMA BULGUSU | Doğrudan gereksinim değil; önceki Faz 0 sürümü fazla pin’liydi → sadeleştirildi |

Güncel `requirements.txt` yalnızca: Django, django-environ, django-import-export, psycopg[binary].

## 4. `.env.example` güvenlik notu

| Konu | Sınıf | Kanıt |
|------|-------|--------|
| HEAD `.env.example` içinde dolu `SECRET_KEY` ve `DB_USER`/`DB_PASSWORD` | DOĞRULANDI | `git show HEAD:Backend/config/.env.example` |
| Faz 0 sonrası placeholder’a çekildi | DOĞRULANDI | working tree diff |

Gerçek `.env` içeriği okunmadı / raporlanmadı.

## 5. Dokümantasyon denetimi (bu turda düzeltilenler)

- Django docs = framework normatif referans; **Kuyumbank skill’i değildir** → `AGENTS.md` + skill başlıkları
- Ek kural A (DOĞRULANDI / DOĞRULANAMADI / PLANLAMA BULGUSU) → `AGENTS.md` + denetim raporları
- Ek kural B (Faz 0 değişiklik sınırı) → `AGENTS.md` + bu dosya
- Tenant denetimi derinleştirildi → `faz0-tenant-guvenlik-denetimi.md`
- Gap matrisi etiketlenecek → `faz0-denetim-raporu.md` güncellenir

## 6. Test kanıtı (yeniden sınıflandırma)

| Komut | Sonuç | Sınıf |
|-------|--------|--------|
| `python manage.py check` | 0 issue | DOĞRULANDI |
| `python manage.py test urunler.tests fiyatlama.tests.test_fiyat_hesaplama tanimlar.tests` | 23 OK | DOĞRULANDI |
| Tenant izolasyon testleri | Yok | DOĞRULANDI (test dosyası yok) |
| `firmalar` test suite | Yok | DOĞRULANDI |
| Üretim ortamı check | Çalıştırılmadı | DOĞRULANAMADI |
