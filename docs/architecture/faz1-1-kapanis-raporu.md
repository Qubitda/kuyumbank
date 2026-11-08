# Faz 1.1 — Kapanış raporu (P0 + P1)

**Tarih:** 2026-11-08  
**Kapsam:** Audit rollback (K-004 / `onay_servisi`) + `urunler` admin tenant scope.  
**Yapılmadı (bilinçli):** Model/migration değişikliği, üretim migrate, Faz 2 kodu, ADR-0005 onayı.

Kanıt etiketleri: **DOĞRULANDI** / **DOĞRULANAMADI** / **PLANLAMA BULGUSU**

---

## 1. Değişen dosyalar ve sorumluluk

| Dosya | Sorumluluk |
|-------|------------|
| `Backend/config/firmalar/services/audit_servisi.py` | `record_audit` + `record_audit_durable` (ürün atomic dışı başarısız deneme) |
| `Backend/config/urunler/services/onay_servisi.py` | Yetki/sahiplik atomic dışı; fail audit atomic dışı; başarı audit ürün yazımıyla aynı atomic; `refresh_from_db` ile stale durum engeli |
| `Backend/config/urunler/selectors/katalog_tenant.py` | Tek selector: `scope_urun_queryset`, `scope_urun_related_queryset`, `user_may_see_tedarikci_identity` (`can_view_all_tenants`; `is_superuser` kısa yolu yok) |
| `Backend/config/urunler/selectors/__init__.py` | Selector export |
| `Backend/config/urunler/admin/urun_admin.py` | Urun/Varyant/UrunKanal/UrunTasi `get_queryset`, inline, FK, autocomplete, list_display/filter/fieldset tedarikçi gizleme; action queryset scope |
| `Backend/config/urunler/tests/test_audit_rollback.py` | P0 TransactionTestCase: fail/success audit + ürün durumu |
| `Backend/config/urunler/tests/test_k004_extended.py` | Fail audit persist iddiası güncellendi |
| `Backend/config/urunler/tests/test_admin.py` | ADR-0003-05 urunler admin hücreleri (1–4, 6, 7) |
| `docs/architecture/faz1-1-kapanis-raporu.md` | Bu rapor |

---

## 2. P0 — Audit rollback

### Davranış

- `onaya_gonder` / `onayla` / `reddet` / `yayina_al` / `pasife_al`: sahiplik ve permission kontrolleri `transaction.atomic` dışında.
- Reddedilen deneme: `record_audit_durable` → sonra istisna (ürün atomic’ine girilmez veya atomic sonrası `ValidationError` yakalanıp audit yazılır).
- Başarılı geçiş: ürün `UPDATE` + `record_audit(success=True)` aynı atomic içinde.
- Atomic öncesi durum okumaları `refresh_from_db()` ile yapılır (çağıranın stale instance riski).

### Testler

| Test | Beklenen |
|------|----------|
| `test_failed_ownership_audit_persists` | Fail audit kalır; durum değişmez |
| `test_failed_permission_audit_persists` | Fail audit |
| `test_failed_validation_audit_persists_product_unchanged` | Fail audit; `taslak` |
| `test_failed_onayla_audit_persists` | Fail audit |
| `test_failed_reddet_audit_persists` | Fail audit |
| `test_failed_yayina_al_audit_persists` | Fail audit |
| `test_failed_pasife_al_audit_persists` | Fail audit |
| `test_success_onaya_gonder_single_audit` | Tam bir success audit |
| `test_success_full_transition_audits` | Her geçişte 1 success audit |
| `test_failed_audit_visible_after_nested_product_atomic` | Nested atomic + assertRaises sonrası audit |
| `test_failed_audit_persists_on_ownership_deny` | K-004 extended |
| `test_audit_on_success` | Success audit |

---

## 3. P1 — urunler admin tenant scope (ADR-0003-05)

Tek selector: `urunler.selectors.katalog_tenant`. Platform çapraz görünürlük yalnız `firmalar.view_all_tenants`.

### Hücre → test adı

| Senaryo | Yüzey | Test adı |
|---------|-------|----------|
| 1 Listeleyemez | Admin changelist | `test_s1_changelist_urun_hides_other_firma` |
| 1 Listeleyemez | Selector | `test_s1_selector_urun_hides_other_firma` |
| 2 ID ile getiremez | Admin change/get | `test_s2_change_get_object_other_firma_none` |
| 2 ID ile getiremez | İlişkili admin get | `test_s2_varyant_get_object_other_firma_none` |
| 3 Değiştiremez | Change queryset | `test_s3_other_urun_not_in_change_queryset` |
| 3 Değiştiremez | Action scope | `test_s3_action_queryset_scoped_excludes_b` |
| 4 İlişkili nesne | Varyant changelist | `test_s4_varyant_changelist_scoped` |
| 4 İlişkili nesne | UrunKanal changelist | `test_s4_urun_kanal_changelist_scoped` |
| 4 İlişkili nesne | Inline queryset | `test_s4_inline_queryset_scoped` |
| 4 İlişkili nesne | FK formfield | `test_s4_formfield_urun_fk_scoped` |
| 4 İlişkili / kimlik | Tedarikçi gizleme | `test_s4_tedarikci_identity_hidden_from_supplier_staff` |
| 6 Platform perm | Changelist all | `test_s6_platform_admin_sees_all_urun` |
| 7 Superuser sessiz aşamaz | Changelist | `test_s7_superuser_without_view_all_no_urun_bypass` |

Senaryo 5 (firma yöneticisi platform yetkisi) urunler admin hücresi olarak istenmedi; mevcut `firmalar` / `test_services` kanıtı duruyor.

---

## 4. Komutlar ve çıktılar (PostgreSQL)

```text
python manage.py check
→ System check identified no issues (0 silenced).   [DOĞRULANDI]

python manage.py makemigrations --check --dry-run
→ No changes detected   [DOĞRULANDI]

python manage.py test firmalar.tests urunler.tests fiyatlama.tests.test_fiyat_hesaplama
→ Ran 72 tests in ~64.7s — OK   [DOĞRULANDI]
```

Test runner: `Creating test database for alias 'default'...` (PostgreSQL test DB).

---

## 5. Kalan riskler

| ID | Risk | Sınıf |
|----|------|-------|
| R1 | ADR-0005 (Faz 2 katalog ownership) onaylanmadı; Faz 2 kodu yok | PLANLAMA BULGUSU |
| R2 | Admin `has_change_permission(obj=…)` model seviyesinde; nesne engeli `get_queryset` / `get_object` üzerinden (ID tahmini → `None`) | DOĞRULANDI (get_object testleri) |
| R3 | Inline `get_queryset`, Django model `view`/`change` yoksa `qs.none()` döner; tenant scope ancak model perm varken ölçülür | DOĞRULANDI |
| R4 | Üretim migrate çalıştırılmadı (görev kuralı) | DOĞRULANDI |
| R5 | Browser/Client admin E2E yok; RequestFactory + ModelAdmin API | DOĞRULANAMADI (E2E) |

---

## 6. GO / NO-GO

**GO (Faz 1.1 kapanışı)** — P0 audit rollback ve P1 urunler admin tenant scope düzeltildi; suite yeşil; migration drift yok.

**Engel (ADR-0005 hariç):** Yok.

**Sonraki kapı:** ADR-0005 onayı olmadan Faz 2 koduna geçilmez.
