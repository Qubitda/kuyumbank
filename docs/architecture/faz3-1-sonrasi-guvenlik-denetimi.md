# Faz 3.1 sonrası — güvenlik / admin yüzey denetimi

**Tarih:** 2026-11-08  
**Kapsam:** Dilim 3.1 sonrası kod incelemesi (bu oturumda test koşulmadı; etiketler kod kanıtlı).  
**Kaynak:** Bağımsız arşiv incelemesi + yerel dosya/satır doğrulama.  
**Bağlı:** ADR-0003…0007; `mevcut-mimari.md`; `faz3-1-uygulama-raporu.md`  
**Sonraki karar:** [`ADR-0009`](../decisions/ADR-0009-admin-yuzey-sertlestirme.md) (**Taslak**)

Etiketler: **DOĞRULANDI (kod)** = dosya/satır; runtime/test bu turda **DOĞRULANAMADI**.

---

## 1. Özet

Servis katmanı (RBAC, `domain_atomic`, fail-audit, teklif durum makinesi) disiplinli. Asıl risk: **admin, servis kurallarını atlayabiliyor** veya maliyet görünürlüğü tedarikçiyi yanlış kapatıyor. Dilim 3.2 / ADR-0008’den önce bu yüzeylerin kapatılması önerilir.

---

## 2. Yüksek öncelik (1–5)

| # | Bulgu | Etiket | Kanıt |
|---|--------|--------|-------|
| 1 | Firma yöneticisi `is_staff` / `is_superuser` form alanlarını görebiliyor; `change_kullanici` alıcı/tedarikçi rollerinde | DOĞRULANDI (kod) | `firmalar/admin/kullanici_admin.py:34`; `role_permissions.py` `change_kullanici` (ALICI_YONETICI / TEDARIKCI_SAHIP). Runtime: DOĞRULANAMADI |
| 2 | YAYINDA teklifte `gram` / fiyat / geçerlilik / `stok_adet` / `oncelik` admin’den düzenlenebilir; yalnız `_servis_alanlari` readonly | DOĞRULANDI (kod) | `fiyatlama/admin/admin.py:98–111`, `:170–177`. ADR-0007 versiyon kuralını atlar. Test yok. |
| 3 | `_maliyet_fields` (`birim_fiyat`, `iscilik_override`) `user_may_see_fiyat_maliyet` → yalnız `view_all_tenants`; tedarikçiye de gizli | DOĞRULANDI (kod) | `selectors/tenant.py:7–10`; `admin.py:97`, `:222–225`. GRAM_BIRIM/SABIT_PARCA için DB constraint `birim_fiyat` zorunlu → tedarikçi admin’den o modelleri dolduramaz. Rapor §7 ile çelişki. |
| 4 | O1 kilidi `UrunAdmin` / inline’da; bağımsız `VaryantAdmin` (`list_editable` gram/fiyat/stok), `UrunTasiAdmin`, `UrunKanalAdmin`’de yok | DOĞRULANDI (kod) | `urunler/admin/urun_admin.py:212–214` vs `:304–309`. ADR-0006 O1 eksik yüzeyi. |
| 5 | `yeni_versiyon_olustur` `eslestirme_*` / `hedef_urun` kopyalar; gram bandı yeniden doğrulanmaz | DOĞRULANDI (kod) | `teklif_servisi.py:323+`, `:386–390`. Predicate yalnız eşleşme alanları (`tenant.py:22–36`). ADR-0005 K3 delinme riski. |

---

## 3. Orta öncelik (özet)

| Bulgu | Etiket | Not |
|-------|--------|-----|
| Kimlik unique ihlal mesajı → oracle (kör havuz) | DOĞRULANDI (kod tasarım) / runtime DOĞRULANAMADI | Servis genel hata; ModelForm constraint mesajı sızdırabilir |
| Slug = `slugify(ad)`, Türkçe “ı” kaybı, çakışmada IntegrityError | DOĞRULANDI (kod) | K-016 kısmi |
| `requirements.txt` UTF-16 LE; Pillow yok ama `ImageField` var | DOĞRULANDI (kod) | BOM `\xff\xfe`; `kategori.py` ImageField |
| Fail-audit sidecar her red’de yeni bağlantı | DOĞRULANDI (kod) | ADR-0007 operasyon notu; rate limit yok |
| `cozumle()` sıra: ayar → kanal; K-007 kanal → ayar | DOĞRULANDI (kod) | ADR veya kod hizası (3.2 ile) |
| Eşleştirme: tutarsız `hedef_urun` onaylanabilir; AYRILDI dönüş yok; bazı yollarda fail audit yok | DOĞRULANDI (kod) | K5 |
| `approve_firma` kullanılmıyor; `onay_durumu` change_firma ile | DOĞRULANDI (kod) | |
| AuditOlay admin yok; immutability/IP/before-after yok; LOGGING yok | DOĞRULANDI (kod) | |
| `gecerlilik_bitis` geçen YAYINDA düşürme işi yok | DOĞRULANDI (kod) | Quote kapısında (0008) |
| `urunler.0005` RunPython + şema aynı migration | DOĞRULANDI (kod) | PG pending trigger uyarısı; üretim DOĞRULANAMADI |

---

## 4. Düşük / doküman notları

- `islcilik_dahil_mi` yazım hatası migration’a işlemiş — geri dönüş maliyetli; bilinçli borç.
- Bağımsız incelemedeki “README test komutu eski” / “ADR-0007 iki madde açık” iddiaları: yerelde README + checklist kısmen güncellendi (`95b502d`); arşiv eski olabilir.
- `.docx` kanonik `.md` gerisinde — commit etme; `.md` otorite.
- AGENTS Faz 0–8 vs rapor §14 Faz 0–10 numaralandırma sapması — PLANLAMA; eşleme tablosu ayrıca.

---

## 5. K-* özeti (inceleme ile uyumlu)

| Durum | Maddeler |
|-------|----------|
| Kapandı (büyük ölçüde) | K-003, K-004, K-005, K-006, K-015, K-016 (slug hariç) |
| Kısmi | K-002, K-017, K-020, K-022–K-024 |
| Açık (planlı) | K-007/008 (3.2), K-009/013 (3b), K-011, K-012, K-019 |
| Faz dışı / bekliyor | K-001, K-010, K-014, K-018, K-021 |

---

## 6. Önerilen sıra (ürün sahibi)

1. **ADR-0009 Kabul** → yüksek 1–5 + Pillow/requirements encoding + O1 yüzeyleri (kod + test + rapor).  
2. Dilim **3.2** (K-007/K-008) — `cozumle` sıra hizasını burada çöz.  
3. **ADR-0008** netleştirme / Kabul — quote, maliyet görünürlüğü (bulgu 3 ile çakışır; 0009’da tedarikçi maliyet ayrımı şart).  
4. Orta maddeler (audit admin, firma onay servisi, slug) sonraki sertleştirme diliminde.

**Bu turda kod yazılmadı** (ADR-0009 henüz Taslak).
