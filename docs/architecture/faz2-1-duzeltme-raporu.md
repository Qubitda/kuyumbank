# Faz 2.1 — ADIM 2 düzeltme raporu

**Tarih:** 2026-11-08  
**Kaynak:** `faz2-1-dogrulama-raporu.md` + ADR-0006 (**Kabul edildi**)  
**Üretim migrate:** yapılmadı. Faz 3’e geçilmedi.

---

## 1. Değişen dosyalar ve sorumluluk

| Dosya | Sorumluluk |
|-------|------------|
| `docs/decisions/ADR-0006-faz2-1-kararlar.md` | Faz 2.1 kararları (Kabul; O2/O3/teklif sınır) |
| `docs/decisions/README.md` | ADR-0005 + ADR-0006 → Kabul |
| `docs/architecture/faz2-baslangic-raporu.md` | `urunleri_birlestir` ertelendi notu |
| `fiyatlama/selectors/tenant.py` | `scope_teklif_varyant_queryset` |
| `fiyatlama/admin/admin.py` | B1 readonly + FK scope + sunucu `tedarikci` |
| `fiyatlama/tests/test_teklif_admin_b1.py` | B1 testleri |
| `firmalar/services/rol_servisi.py` | B2 `assign_user_role(actor=...)` + perm/tenant |
| `firmalar/admin/kullanici_admin.py` | Firma/rol tenant scope; actor geçişi |
| `firmalar/management/commands/bootstrap_platform.py` | Chicken-egg: seed + sync (assign_user_role değil) |
| `firmalar/tests/test_assign_role_b2.py` | B2 testleri |
| `firmalar/tests/test_tenant_isolation.py` | `actor=` imza uyumu |
| `urunler/selectors/katalog_tenant.py` | `scope_eslestirme_hedef_urun_queryset` |
| `urunler/services/eslestirme_servisi.py` | B3/B4a öneri+onay sertleştirme |
| `urunler/services/gram_bandi.py` | Gram bandı hesabı |
| `urunler/tests/test_eslestirme_b3.py` | B3 |
| `urunler/tests/test_gram_bandi_b4a.py` | B4a |
| `urunler/tests/test_adr0005_kabul_b4a.py` | ADR-0005 §8 tamamlayıcı |
| `urunler/services/onay_servisi.py` | O1 geri_cek/taslaga_al/kritik; O5 dört göz |
| `urunler/services/__init__.py` | export |
| `urunler/admin/urun_admin.py` | O1 change kilidi; O4 MultipleChoiceField; actions |
| `urunler/tests/test_onay_o1.py` | O1 |
| `urunler/tests/test_toplu_red_o4.py` | O4 |
| `urunler/tests/test_dort_goz_o5.py` | O5 |
| `firmalar/services/audit_servisi.py` | O3 sidecar + TestCase FK fallback |
| `firmalar/tests/test_audit_durable_o3.py` | O3 TransactionTestCase |
| `docs/architecture/faz2-1-duzeltme-raporu.md` | Bu rapor |

---

## 2. Madde özeti

| ID | Sonuç |
|----|--------|
| B1 | Servis alanları readonly; `tedarikci` sunucu ataması; varyant FK selector |
| B2 | `actor` + `manage_users`/`manage_all_users` + firma değişikliği platform; audit hedef detail |
| B3 | Hedef scope + genel hata; kanıt şeması; ONAYLANDI/AYRILDI kilidi; kesin←`tedarikci_kodu`; audit’te guven gizli |
| B4a | Gram bandı + öneri/onay red; `urunleri_birlestir` **eklenmedi** (ertelendi) |
| O1 | `onay_bekliyor` change yok; `geri_cek`; onaylı kritik kilit; `taslaga_al` |
| O4 | `MultipleChoiceField` + çoklu ID testi |
| O5 | `onayla`/`yayina_al` dört göz + fail audit |
| O3 | Sidecar durable; TestCase FK sapması ADR’de |
| O2 | Migration `0007` + `onaya_gonder` çakışma kontrolü + testler |
| O6 | **Faz 3’e ertelendi** (`approve_teklif` / `manage_sozlesme` servis bağlama yok) |

---

## 3. O2 (uygulandı)

- Dosya: `urunler/migrations/0007_o2_kimlik_uniq_reddedildi_haric.py`
- Model: `urun_kimlik_ab_anahtar_uniq` → A/B + dolu anahtar + `!= reddedildi`
- Servis: `onaya_gonder` aktif çakışma ön kontrolü; constraint/`IntegrityError` → genel mesaj + fail audit
- Testler: `test_onaya_gonder_kimlik_o2.py`, `test_migration_0007_o2.py`

---

## 4. Çalıştırılan komutlar (gerçek çıktı) — ADIM 2 sonu

```
python manage.py check
→ System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests
→ Ran 136 tests in 120.983s
→ OK
```

---

## Ek A — O2 kabul sonrası (2026-11-08)

### Değişen dosyalar

| Dosya | Sorumluluk |
|-------|------------|
| `urunler/models/urun.py` | Unique condition `reddedildi` hariç |
| `urunler/migrations/0007_o2_kimlik_uniq_reddedildi_haric.py` | İleri/reverse (çakışmada reverse durur) |
| `urunler/services/onay_servisi.py` | Kimlik çakışma ön kontrol + genel hata |
| `urunler/tests/test_onaya_gonder_kimlik_o2.py` | Servis testleri |
| `urunler/tests/test_migration_0007_o2.py` | Migration ileri/reverse |
| `docs/decisions/ADR-0006-faz2-1-kararlar.md` | Kabul; O3 üretim netliği; teklif durum bilinçli sınır |
| `docs/decisions/README.md` | ADR-0006 → Kabul |

### Komutlar (gerçek çıktı)

```
python manage.py check
→ System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests
→ Ran 143 tests in 131.064s
→ OK
```

### Üst düzey test komutu hatası — kök neden (düzeltme yok)

**DOĞRULANDI:** `python manage.py test firmalar urunler fiyatlama tanimlar` label discovery, uygulama paketlerinin yanında cwd üzerindeki top-level isimleri de yüklemeye çalışır. ADR-0004 sonrası `fiyatlama/admin/` ve `fiyatlama/models/` paketleri `admin` / `models` olarak ikinci kez import edilince:

1. `admin` → `@admin.register` tekrar → `AlreadyRegistered: FiyatSozlesmesi`
2. `models` → `app_label` tanımsız → `RuntimeError`

Düzeltme yapılmadı (ayrı onay). Çalıştırma: `*.tests` modül yolları.

### Bilinçli sınır (ADR-0006)

Teklif `durum` admin’de salt okunur; durum servisi / `approve_teklif` **Faz 3**.

---

## 5. Karşılanmayan / ertelenen kabul testleri

| Madde | Not |
|-------|-----|
| `urunleri_birlestir` + varyant taşıma | Ertelendi (ADR-0006 B4b) |
| O6 `approve_teklif` / `manage_sozlesme` / teklif durum servisi | **Faz 3’e ertelendi** |
| Kategori derinlik + taşıma (ADR §8) | Mevcut `test_kategori_k016`; bu turda genişletilmedi |
| Onaylı katalogda tedarikçi varyant görünürlük (ADR-0005 §9) | Hâlâ ürün kararı açık |

---

## 6. Riskler

| Risk | Etiket |
|------|--------|
| O3 TestCase FK fallback — üretimde actor commit’li → sidecar kalıcı | DOĞRULANDI (ADR O3 + TransactionTestCase) |
| Teklif `durum` servisi yok (bilinçli / Faz 3) | PLANLAMA BULGUSU |
| Dört göz `yayina_al` gönderene bağlı | DOĞRULANDI |
| Üretimde `0007` migrate henüz uygulanmadı | DOĞRULANDI (bilinçli) |

---

## 7. Sonraki somut adım

1. (İsteğe bağlı) üst düzey test discovery düzeltmesi onayı  
2. Staging/üretim `0007` migrate — ayrı onay  
3. Faz 3 ancak ayrı talimat + ADR ile
