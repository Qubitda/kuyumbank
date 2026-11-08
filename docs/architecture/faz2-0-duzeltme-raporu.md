# Faz 2.0 — Düzeltme raporu

**Tarih:** 2026-11-08  
**Kapsam:** Düzeltme turu; yeni özellik yok (zorunlu `hedef_urun` + `approve_eslestirme` hariç — görev maddesi 3).  
**Üretim migrate:** yapılmadı.

Kanıt: **DOĞRULANDI** / **DOĞRULANAMADI** / **PLANLAMA BULGUSU**

---

## 1. Değişen dosyalar ve sorumluluk

| Dosya | Sorumluluk |
|-------|------------|
| `firmalar/migrations/0003_faz1_backfill_platform.py` | Rolü dolu firmasız → DUR + `audit_user_assignments`; yalnız boş rol superuser/staff bağlanır |
| `urunler/migrations/0005_faz2_katalog_ownership.py` | RemoveField öncesi teklif taslağına taşıma; nullable alter + reverse geri yazma |
| `urunler/services/eslestirme_servisi.py` | kesin=kimlik eşleşmesi; `hedef_urun`; durum kilidi sonrası; `approve_eslestirme`; ayır←ONAYLANDI |
| `fiyatlama/models/tedarikci_teklif.py` | `hedef_urun` FK; `approve_eslestirme` Meta.permission |
| `fiyatlama/migrations/0004_faz2_0_hedef_urun_approve_eslestirme.py` | Şema |
| `firmalar/role_permissions.py` | Matris + Django view/change; `approve_eslestirme` |
| `fiyatlama/selectors/tenant.py` | Teklif/sözleşme/log/taş scope + maliyet görünürlüğü |
| `fiyatlama/admin/admin.py` | Tenant scope; maliyet/log gizleme |
| `firmalar/services/yetki_servisi.py` | `is_active` / `firma.aktif` → False |
| `firmalar/services/audit_servisi.py` | `domain_atomic` + durable guard |
| `urunler/services/onay_servisi.py` | `domain_atomic` kullanımı |
| Testler | 0003/0005 migration, eslestirme, has_perm, rol admin, fiyatlama admin, audit durable |
| `docs/architecture/faz2-0-duzeltme-raporu.md` | Bu rapor |

---

## 2. Madde özeti

### 1) firmalar.0003
Firmasız + rolü dolu (veya staff/superuser değil) → `RuntimeError` + `audit_user_assignments` yönlendirmesi. Boş rol + superuser/staff → platform + `platform_super`.

### 2) urunler.0005
`tedarikci` / `tedarikci_urun_kodu` → her varyant için `TedarikciTeklif` taslağı (`tedarikci`, `tedarikci_kodu`). Varyantsız/gram’sız → dur. Reverse: nullable re-add + tekliften geri yazma (docstring’de veri kaybı notu).

### 3) eslestirme_servisi
(a) `kesin` yalnız teklif kimliği == `kimlik_anahtari`  
(b) `hedef_urun` kalıcı  
(c) durum kontrolü `select_for_update` sonrası; `urunu_ayir` yalnız `ONAYLANDI`  
(d) `fiyatlama.approve_eslestirme`  
(e) testler

### 4–7) Admin scope, has_perm, rol matrisi, audit
Selector tabanlı fiyatlama admin; maliyet/log alıcı-tedarikçide gizli; pasif kullanıcı/firma yetkisiz; Django model perms grup seed; `domain_atomic` ile durable koruması.

### 8) .env
| Kontrol | Sonuç | Sınıf |
|---------|--------|-------|
| Git index’te `.env` | Yok (`git ls-files` boş) | DOĞRULANDI |
| Git history ekleme | Eşleşme yok | DOĞRULANDI |
| Diskte varlık | `backend/config/.env` var | DOĞRULANDI |
| ignore | `backend/.gitignore` | DOĞRULANDI |
| Anahtar adları (değer yok) | SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_* | DOĞRULANDI |
| Döndürme | Yerel SECRET_KEY / DB_PASSWORD **döndürülmeli** (değer yazılmadı) | PLANLAMA BULGUSU / operasyon |

---

## 3. Test komutları (PostgreSQL)

```text
python manage.py check
→ System check identified no issues (0 silenced).   [DOĞRULANDI]

python manage.py makemigrations --check --dry-run
→ No changes detected   [DOĞRULANDI]

python manage.py test firmalar.tests urunler.tests fiyatlama.tests
→ Ran 104 tests in ~96s — OK   [DOĞRULANDI]
```

Migration özel: `test_migration_0003_backfill` (2), `test_migration_0005` (3) — OK.

---

## 4. Riskler

| ID | Risk | Sınıf |
|----|------|-------|
| R1 | Yerleşik DB’de 0005 zaten uygulanmışsa RunPython yeniden çalışmaz; veri taşıma yalnız yeni kurulum / unapply-apply ile | DOĞRULANDI |
| R2 | `urunleri_birlestir` hâlâ stub (görev dışı) | PLANLAMA BULGUSU |
| R3 | Üretim migrate yok | DOĞRULANDI |
| R4 | Yerel `.env` secret döndürme operatör işi | DOĞRULANAMADI (yapılmadı) |
