# Faz 1 — Doğrulama raporu

**Tarih:** 2026-11-08  
**Kural:** Model/migration/servis/admin **değiştirilmedi**. Yalnızca test + docs eklendi.  
**Kanıt etiketleri:** DOĞRULANDI / DOĞRULANAMADI / PLANLAMA BULGUSU

---

## A1. Test altyapısı

| Madde | Sonuç | Sınıf |
|-------|--------|-------|
| DB ENGINE | `django.db.backends.postgresql` (`settings.py` L98–100) | DOĞRULANDI |
| DB NAME | `kuyumbank` | DOĞRULANDI |
| SQLite mı? | **Hayır** | DOĞRULANDI |

### Komutlar

```text
python manage.py check
→ System check identified no issues (0 silenced).   [DOĞRULANDI]

python manage.py makemigrations --check --dry-run
→ No changes detected   [DOĞRULANDI]

python manage.py audit_user_assignments
→ Tüm kullanıcıların firma/rol ataması tutarlı.   [DOĞRULANDI]

python manage.py test firmalar.tests urunler.tests fiyatlama.tests.test_fiyat_hesaplama
→ Ran 49 tests in ~23.5s — OK   [DOĞRULANDI]

tanimlar.tests
→ Anlamlı case yok; suite’e dahil edildiğinde ek test sayısı 0   [DOĞRULANDI]
```

Test runner ayrı PostgreSQL test DB oluşturur (`Creating test database for alias 'default'...`).

---

## A2. ADR-0003-05 izolasyon matrisi

Senaryolar × yüzey. Hücre = test adı veya `TEST YOK`.

| Senaryo | Selector | Domain servis | Admin changelist | Admin change/get | Admin add/delete/action |
|---------|----------|---------------|------------------|------------------|-------------------------|
| 1 Listeleyemez | `test_list_other_firma_adres_hidden` | TEST YOK (genel yazma servisi yok) | `test_changelist_firma_adresi_scoped`, `test_changelist_firma_model_scoped`, `test_changelist_kullanici_scoped` | TEST YOK | TEST YOK |
| 2 ID ile getiremez | `test_get_other_firma_raises_404`, `test_cannot_assert_same_firma_on_b_adres` | `test_other_firma_cannot_submit` (K-004) | (queryset boş → object gizlenir; ayrı get_object testi YOK) | TEST YOK | TEST YOK |
| 3 Değiştiremez/silemez | `test_scoped_queryset_excludes_b_before_update` | TEST YOK (FirmaAdresi için domain update servisi yok) | TEST YOK | TEST YOK | TEST YOK |
| 4 İlişkili nesne | `assert_same_firma` + K-004 IDOR | `test_idor_submit_other_supplier_product` | TEST YOK (`urun` admin `get_queryset` **yok**) | TEST YOK | TEST YOK |
| 5 Firma yöneticisi platform yetkisi yok | `test_firma_yonetici_no_approve_urun`, `test_firm_admin_cannot_use_platform_perm` | `test_platform_disi_kullanici_onaylayamaz` | — | — | — |
| 6 Platform yalnız kendi perm | `test_platform_admin_has_view_all` + catalog seed | `onayla`/`publish` perm path | `test_platform_admin_sees_all_adres` | TEST YOK | TEST YOK |
| 7 Superuser sessiz aşamaz | `test_superuser_without_view_all_perm_no_tenant_bypass` | yetki_servisi superuser short-circuit kullanmaz (grep) | TEST YOK | TEST YOK | TEST YOK |

**Dosyalar:**  
`firmalar/tests/test_tenant_isolation.py`, `test_admin_tenant_scope.py`, `test_mutation_isolation.py`, `test_superuser_firma.py`  
`urunler/tests/test_k004_*.py`, `test_services.py`

### Açık bulgular (kod düzeltilmedi)

| ID | Bulgu | Sınıf |
|----|--------|-------|
| G-A2-1 | `urunler` admin’de `get_queryset` tenant scope **yok** (`urun_admin.py` grep) | DOĞRULANDI |
| G-A2-2 | Admin change/delete/action için object-level test ve enforcement zayıf; çoğunlukla queryset’e güveniliyor | PLANLAMA BULGUSU / kısmen DOĞRULANDI |
| G-A2-3 | Başarısız `onaya_gonder` audit’i `transaction.atomic` nedeniyle **persist olmuyor** (`test_failed_audit_not_persisted_due_to_atomic`) | DOĞRULANDI |

---

## A3. Superuser / firma NOT NULL

| Yol | Sonuç | Kanıt | Sınıf |
|-----|--------|-------|-------|
| `create_superuser` | Platform firma + `platform_super` atar | `test_create_superuser_assigns_platform_firma` | DOĞRULANDI |
| `User(...); save()` firmasız (superuser bayraklı) | `ValidationError` | `test_plain_create_without_firma_rejected` | DOĞRULANDI |
| `create_user` firmasız | `ValidationError` | `test_objects_create_user_without_firma_rejected` | DOĞRULANDI |
| Admin form | Ayrı Client E2E yok | — | DOĞRULANAMADI |

### `is_superuser` grep (iş yetkisi)

| Konum | Rol | Sınıf |
|-------|-----|-------|
| `kullanici.py` create_superuser manager | Bayrak set | DOĞRULANDI (beklenen) |
| `yetki_servisi.py` docstring | Superuser `has_perm` kısa yolu **bilinçli kullanılmıyor** | DOĞRULANDI |
| `bootstrap_platform.py` | Firmasız staff/superuser backfill filtresi | DOĞRULANDI |
| `kullanici_admin.py` | Form alanı / list_display | DOĞRULANDI |
| `onay_servisi.platform_kullanicisi_mi` | **Yok** (kaldırılmış) | DOĞRULANDI |
| `urunler/tests/_base.py` | Platform user = `PLATFORM_CATALOG` + firma; superuser bypass yok | DOĞRULANDI |

`if rol == '...'` string switch: **eşleşme yok** (grep). Rol set üyelikleri `roles.PLATFORM_ROLLERI` vb. üzerinden — kabul edilebilir.

---

## A4. Permission matrisi vs teknik inceleme §2.3

| §2.3 hücre | Seed (`role_permissions.py`) | Sapma |
|------------|-------------------------------|--------|
| Firma onayı super/admin E | `approve_firma` var | Uyum |
| Tenant-genel quality/logistics/support **S** | `view_all` **yok** (boş) | Bilinçli daraltma → [ADR-0003 addendum](../decisions/ADR-0003-addendum-view-all-scope.md) |
| Ürün onay/yayın catalog E | `approve_urun`, `publish_urun` | Uyum |
| onaya_gonder platform H* | `submit_urun` super’da var; catalog’da yok; runtime sahiplik engeller | Super’da perm var ama K-004 sahiplik H* — **tutarsızlık riski** (perm ≠ acting_as) | PLANLAMA BULGUSU |
| QC / lojistik E | Seed’de QC/lojistik perm yok | Beklenen (model yok) |

### Seed idempotent

```text
seed_role_permissions() x2
groups 18 -> 18
permissions_total 182 -> 182
matrix_equal True
```
**DOĞRULANDI**

---

## A5. K-004 `onaya_gonder`

| Senaryo | Test | Sonuç |
|---------|------|--------|
| Kendi firma ürünü | `test_owner_can_submit` | OK |
| Başka firma | `test_other_firma_cannot_submit` | OK |
| Yetkisiz rol (depo) | `test_yetkisiz_rol_submit_denied` | OK |
| IDOR (başka tedarikçi ürünü) | `test_idor_submit_other_supplier_product` | OK |
| Platform tedarikçi adına | `test_platform_without_submit_on_foreign_product` | OK (red) |
| Audit başarı | `test_audit_on_success` | OK |
| Audit başarısızlık | `test_failed_audit_not_persisted_due_to_atomic` | **Gap:** kayıt rollback | DOĞRULANDI açık |

---

## A6. Migration güvenliği

| Migration | Veri kaybı | Not | Sınıf |
|-----------|------------|-----|-------|
| firmalar.0002 | Düşük (additive) | firma_kodu null, AuditOlay, choices, perms | DOĞRULANDI (dosya okuma) |
| firmalar.0003 | Orta (backfill) | Platform + kod/user doldurma; reverse no-op | DOĞRULANDI |
| firmalar.0004 | Yüksek kapı | NOT NULL | aşağı |
| urunler.0004 / fiyatlama.0002 | Yok | Yalnız Meta.permissions | DOĞRULANDI |

### Reverse → forward

```text
migrate firmalar 0001 → OK (0004,0003,0002 unapply)
migrate firmalar → OK (0002–0004 re-apply)
audit_user_assignments → tutarlı
```
**DOĞRULANDI** (yerel DB)

### NOT NULL kapısı

0003’e inilip SQL ile `firma_id=NULL` kullanıcı eklendikten sonra:

```text
migrate firmalar 0004
→ IntegrityError: column "firma_id" ... contains null values
```
**DOĞRULANDI** — NULL varken 0004 FAIL eder; satır silinerek zorlanmaz.

---

## A7. Güvenlik hijyeni

| Madde | Sonuç | Sınıf |
|-------|--------|-------|
| `git ls-files` `.env` | Yalnız `backend/config/.env.example` | DOĞRULANDI |
| `.gitignore` | `.env`, `.env.*`, `!.env.example` | DOĞRULANDI |
| Gerçek `.env` içerik | Okunmadı / raporlanmadı | — |
| Zayıf secret uyarısı | Yerel geliştirmede zayıf `SECRET_KEY`/DB parolası varsa **döndürülmeli** (değer yazılmadı) | PLANLAMA BULGUSU |

---

## Eklenen test dosyaları (bu tur)

- `firmalar/tests/test_superuser_firma.py`
- `firmalar/tests/test_admin_tenant_scope.py`
- `firmalar/tests/test_mutation_isolation.py`
- `urunler/tests/test_k004_extended.py`

---

## Açık riskler (öncelik)

1. **P0:** Başarısız kritik işlem audit’i atomic rollback ile kayboluyor (K-004 acceptance maddesi zayıf).  
2. **P1:** `Urun` / `Varyant` admin tenant `get_queryset` yok — staff başka tedarikçi ürününü görebilir.  
3. **P2:** `platform_super` seed’de `submit_urun` var; sahiplik yine engeller ama perm geniş.

---

## GO / NO-GO (özet)

Bkz. sohbet son mesajı.
