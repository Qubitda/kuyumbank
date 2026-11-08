# Faz 2.1 — ADIM 1 yeniden doğrulama (salt okunur)

**Tarih:** 2026-11-08  
**Kapsam:** B1–B4, O1–O6; kod/migration değiştirilmedi.  
**ADR sınırı:** ADR-0005. Faz 3 yok. Üretim DB / migrate yok.

Etiketler: **DOĞRULANDI** / **DOĞRULANAMADI** / **PLANLAMA BULGUSU**

---

## Özet tablo

| ID | Konu | Durum | Kanıt |
|----|------|-------|-------|
| B1 | TedarikciTeklifAdmin: tedarikçi hassas alan + FK scope | **Açık** | `fiyatlama/admin/admin.py:76–117` — `get_readonly_fields` / `formfield_for_foreignkey` yok; formda `durum`, `onaylayan`, eşleştirme, `tedarikci`, `varyant` serbest |
| B2 | KullaniciAdmin tenant + assign actor/perm | **Açık** | `kullanici_admin.py:16–55` — Firma FK scope yok; `assign_user_role(..., actor=user)` (`rol_servisi.py:36–37`); actor/perm parametresi yok |
| B3 | teklif_eslestir_oner kontrolleri | **Açık** | `eslestirme_servisi.py:85–125` — hedef görünürlük/durum yok; ONAYLANDI→önerilebilir; kanıt şeması doğrulanmıyor; kimlik oracle: `kanit` ile kesin (`:63–81`) |
| B4 | birleştir / gram bandı / onay hedef etki / kabul testleri | **Açık** | `urunleri_birlestir` yok; `VARYANT_GRAM_BANDI_ORAN` yalnız settings+help_text; `eslestirmeyi_onayla` yalnız teklif durumu (`:128–148`) |
| O1 | Onay bekleyen düzenleme / kritik alan → yeniden onay | **Açık** | `katalog_tenant.py:28–31` onay_bekliyor scoped; `urun_admin.py:175–180` durum kilidi yok; re-approve servisi yok |
| O2 | `urun_kimlik_ab_anahtar_uniq` kapsamı | **Kapandı** (bilgi) | Tüm A/B + dolu anahtar kayıtları (`urun.py:185–192`); aktif filtresi yok — daraltma migration ister (ADIM 2 kararı) |
| O3 | durable dış atomic (admin/import) | **Kısmen** | Guard yalnız `domain_atomic` (`audit_servisi.py:54–67`); `test_audit_durable.py` dış atomic/admin senaryosu yok |
| O4 | Toplu Reddet `_selected_action` çoklu | **Açık** | `TopluRedForm` CharField+MultipleHiddenInput (`urun_admin.py:19–25`, `:214–224`); çoklu seçim testi yok |
| O5 | onayla dört göz (onaylayan ≠ gönderen) | **Açık** | `onay_servisi.py:170–213` — `olusturan_kullanici` karşılaştırması yok |
| O6 | `approve_teklif` / `manage_sozlesme` servis kullanımı | **Kapandı** (bilgi) | Seed/matris + Meta; `require_perm` / servis çağrısı yok (`role_permissions.py` only) |

---

## B1 — TedarikciTeklifAdmin

**Durum: Açık** — **DOĞRULANDI**

- `TedarikciTeklifAdmin` (`fiyatlama/admin/admin.py:76–117`): `get_queryset` tenant scoped (`:93–94`); **`get_readonly_fields` yok**; **`formfield_for_foreignkey` yok**.
- Model alanları (`durum`, `onaylayan`, `eslestirme_durumu`, `eslestirme_guveni`, `tedarikci`, `varyant`, …) varsayılan change formda yazılabilir.
- FK dropdown’ları platform/tenant ile sınırlandırılmıyor → tedarikçi kullanıcı (change izni varsa) başka firma / varyant seçebilir (**IDOR yüzeyi**).

---

## B2 — KullaniciAdmin + assign_user_role

**Durum: Açık** — **DOĞRULANDI**

- Liste queryset tenant/platform scoped (`kullanici_admin.py:33–37`).
- `firma` / `rol` fieldset’te düzenlenebilir (`:16`, `:23`); **`formfield_for_foreignkey` yok** → Firma dropdown tüm firmalar.
- `save_model` → `assign_user_role(user=obj, firma=obj.firma, rol=obj.rol)` (`:51`); `request.user` aktör olarak geçirilmiyor.
- `assign_user_role` (`rol_servisi.py:28–44`): audit `actor=user` (atanan kişi); **actor parametresi yok**; **permission kontrolü yok**.

---

## B3 — teklif_eslestir_oner

**Durum: Açık** — **DOĞRULANDI**

| Alt soru | Sonuç | Kanıt |
|----------|-------|-------|
| `hedef_urun` görünürlük/durum | Yok (yalnız ayar_id) | `eslestirme_servisi.py:88–96` |
| Güven kesin/manuel oracle | Evet — `kanit` içinden kimlik anahtarı okunur | `_teklif_kimlik_degeri` / `_guven_hesapla` `:63–81` |
| ONAYLANDI geri çekme (tedarikçi öneri) | Evet — durum kilidi yok; her zaman `ONERILDI` yazar | `:100–102` |
| `eslestirme_kaniti` doğrulama | Yok — `kanit or {}` kaydı | `:104` |

Not: `urunu_ayir` platform + ONAYLANDI (`:191–205`); tedarikçi ONAYLANDI’yı `teklif_eslestir_oner` ile `ONERILDI`’ye çekebilir.

---

## B4 — birleştir / gram / onay etki / kabul testleri

**Durum: Açık** — **DOĞRULANDI** (kodda yok / kullanılmıyor)

| Alt soru | Sonuç | Kanıt |
|----------|-------|-------|
| `urunleri_birlestir` | Yok | Repo’da sembol yok (grep) |
| `VARYANT_GRAM_BANDI_ORAN` runtime kullanımı | Yok | `settings.py:141` + `varyant.py:43` help_text; servis/hesap yok |
| `eslestirmeyi_onayla` → `hedef_urun` etkisi | Yok | Yalnız `eslestirme_durumu` + `eslestiren_kullanici` (`:136–139`) |

### ADR-0005 §8 kabul testleri — eksik / kısmi

| Test (ADR §8) | Durum |
|---------------|--------|
| Tenant/IDOR taslak | Kısmen (mevcut testler var; B1 FK açık) |
| Tedarikçi yalnız kendi taslağını onaya gönderir | Var (K-004 testleri) |
| `urunu_ayir` | Var (servis + testler) |
| A/B sertifika çift kayıt engeli | Constraint var; gram bandı / birleştirme yok |
| Ayar farklı ürünler eşleşemez | Var (`ayar_uyusmazligi`) |
| Gram bandı dışı teklif ayrı varyant | **Yok** (oran kullanılmıyor) |
| Teklif yalnız kendi tedarikçisi | Var (`_require_own_teklif`) |
| Alıcı yüzeyinde tedarikçi/`olusturan_firma` yok | Kısmen (list_display gizleme; form FK scope eksik) |
| Kategori derinlik + taşıma | Bu turda tam suite doğrulaması dışı / kısmi |
| SEO sabit örnek marka yok | Bu turda ayrı assert doğrulanmadı — **DOĞRULANAMADI** (grep odaklı değil) |

---

## O1 — Onay bekleyen düzenleme / yeniden onay

**Durum: Açık** — **DOĞRULANDI**

- Tedarikçi scope: `onay_bekliyor` dahil (`katalog_tenant.py:28–31`).
- Admin `save_model` durum / kilit kontrolü yok (`urun_admin.py:175–180`).
- Onaylı ürün kritik alan değişince yeniden onay akışı yok (servis/signal yok).

**ADIM 2 politikası ürün kararı ister** (taslağa dön / kilitli).

---

## O2 — `urun_kimlik_ab_anahtar_uniq`

**Durum: Kapandı (bilgi net)** — **DOĞRULANDI**

- Condition: `kimlik_sinifi ∈ {A,B}` ve `kimlik_anahtari != ""` (`urun.py:185–192`).
- `aktif` / `yayin_durumu` / `onay_durumu` filtresi **yok** → tüm kayıtlarda geçerli.
- “Yalnız aktif” daraltması **migration** ister → ADIM 2’de plan + onay.

---

## O3 — record_audit_durable dış atomic

**Durum: Kısmen** — **DOĞRULANDI**

- `record_audit_durable` yalnız `_in_domain_atomic` ise `RuntimeError` (`audit_servisi.py:54–67`).
- Docstring: TestCase dış atomic’inde yazım assert için görünür; production autocommit’te kalıcı.
- Admin changeform / import_export `transaction.atomic` içinde fail-path durable çağrılırsa **rollback ile silinir** — guard bunu yakalamaz.
- Test: `firmalar/tests/test_audit_durable.py` — domain_atomic içi/dışı; **admin/outer atomic senaryosu yok**.

---

## O4 — Admin toplu Reddet `_selected_action`

**Durum: Açık** — **DOĞRULANDI** (kod) + **DOĞRULANAMADI** (runtime çoklu davranış bu turda ayrı request testi yok)

- Form: `_selected_action = forms.CharField(widget=forms.MultipleHiddenInput)` (`urun_admin.py:19–20`).
- Apply: `cleaned_data["_selected_action"]` → str ise tek elemanlı liste (`:218–223`).
- CharField + MultipleHiddenInput listesi tipik olarak `str(list)` üretme / tek değer kaybı riski taşır; **çoklu seçim için dedicated test yok** (grep: reddet action admin testi yok).

Görev “Bunu test et” dedi; ADIM 1 salt okunur — runtime davranış ADIM 2’de test + düzeltme.

---

## O5 — Dört göz (onaylayan ≠ gönderen)

**Durum: Açık** — **DOĞRULANDI**

- `onayla` (`onay_servisi.py:170–213`): platform `approve_urun` + durum; **`olusturan_kullanici_id != kullanici.pk` kontrolü yok**.

---

## O6 — approve_teklif / manage_sozlesme

**Durum: Kapandı (bilgi: seed-only)** — **DOĞRULANDI**

- Tanım: Meta permissions + `role_permissions.py` matrisi.
- Servislerde `P["approve_teklif"]` / `P["manage_sozlesme"]` / `require_perm(...)` kullanımı **yok** (grep yalnız seed/migration/model).

---

## ADR-0005 README tutarlılığı

**Durum: Açık (doküman tutarsızlığı)** — **DOĞRULANDI**

| Kaynak | Durum alanı |
|--------|-------------|
| `docs/decisions/ADR-0005-katalog-platform-ownership.md:3` | **Kabul edildi** |
| `docs/decisions/README.md:12` | **TASLAK** |
| ADR §11 checklist | Kabul işaretli (`:196–202`) |

README güncellenmeli (doküman düzeltmesi; uygulama kodu değil).

---

## Çalıştırılan komutlar

Çalışma dizini: `Backend/config`

### `python manage.py check`

```
System check identified no issues (0 silenced).
```

**DOĞRULANDI** — exit 0.

### `python manage.py makemigrations --check --dry-run`

```
No changes detected
```

**DOĞRULANDI** — exit 0.

### Görevdeki paket etiketi: `python manage.py test firmalar urunler fiyatlama tanimlar`

```
ERROR: admin (unittest.loader._FailedTest.admin)
AlreadyRegistered: The model FiyatSozlesmesi is already registered...
ERROR: models (unittest.loader._FailedTest.models)
RuntimeError: Model class models.tedarikci_teklif.TedarikciTeklif doesn't declare an explicit app_label...
Ran 106 tests in 96.848s
FAILED (errors=2)
```

**DOĞRULANDI** — discovery, app paketlerini top-level `admin` / `models` olarak yeniden import ediyor; **2 import hatası**. Asıl test gövdesi bu komutta güvenilir “OK” sayılmaz.

### Düzeltilmiş discovery: `python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests`

```
Ran 104 tests in 95.905s
OK
```

**DOĞRULANDI** — 104 OK.

---

## ADIM 1 sonucu

Salt okunur doğrulama bitti. **ADIM 2’ye geçilmedi.**

Açık / kısmen (düzeltme adayı, onay sonrası): **B1, B2, B3, B4, O1, O3 (kısmen), O4, O5**; doküman: ADR README.

Karar bekleyenler (ADIM 2 talimatı): O1 politika, O2 unique daraltma + migration planı, B4 birleştir/gram tanımı.

---

## Sonraki faz (beklemede)

Kullanıcı onayı + ADIM 2: öncelik B1 → B2 → B3 → B4 → O1 → O4 → O5 → O3 → O2; çıktı `docs/architecture/faz2-1-duzeltme-raporu.md`.
