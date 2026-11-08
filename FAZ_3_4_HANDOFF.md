# Faz 3.4 — Agent devir raporu

**Tarih:** 2026-11-08  
**Dal:** `adim-1-ilerleme`  
**HEAD (push’lu):** `0a77b26` — `chore: Backend -> backend rename and living docs sync`  
**Kod kökü:** `backend/config/`  
**Kapsam:** Dilim 3.4 (üç fiyat modeli + CurrencyConversion). **Faz 3.5 başlanmadı.**

Bu rapor yalnızca durum aktarımıdır; aşağıdaki dosya oluşturulurken uygulama koduna dokunulmamıştır.

---

## 1. Tamamlanan geliştirmeler

- **METAL_BAZLI / GRAM_BIRIM / SABIT_PARCA** saf Decimal hesapları (`fiyat_hesaplama.py`); legacy `hesapla()` korundu.
- Ortak kalemler: kanal marjı (`YUZDE` / `TL_GR` / `TL_PARCA`), taş, ek_bedel. **`platform_servis` yok (B-01).** Vergi yok (B-06).
- Yuvarlama: ara adım yok; `toplam_vergisiz` TRY `0.01` **HALF_UP**.
- **CurrencyConversion** (`tanimlar.services.currency_conversion`): `DovizKuru.kur` = TRY / 1 FX; FX→TRY ×, TRY→FX ÷, FX→FX TRY pivot; taraf → `KurPolitikasi` kur tipi; stale/eksik hata; verilen gözlem sessiz yenilenmez.
- İnce sarmalayıcı: `fiyat_motoru.hesapla_teklif_kalemleri` (birim fiyat PB dönüşümü + model çağrısı).
- Yaşayan dokümanlar 3.4 durumuna güncellendi (`faz3-4-uygulama-raporu.md`, `mevcut-mimari`, AGENTS, README, ADR/skills özetleri).

**Bilinçli dışı:** `PricingService.quote`, `PriceQuote`, immutability trigger, kör havuz UI, teklif seçim sırası kodu, sözleşme orkestrasyonu.

---

## 2. Değiştirilen ve oluşturulan dosyalar

**Durum:** 3.4 çıktıları **henüz commit edilmedi** (working tree dirty).

### Oluşturulan (untracked)
| Dosya |
|-------|
| `backend/config/fiyatlama/services/fiyat_motoru.py` |
| `backend/config/fiyatlama/tests/test_uc_model_hesaplama.py` |
| `backend/config/fiyatlama/tests/test_fiyat_motoru.py` |
| `backend/config/tanimlar/services/currency_conversion.py` |
| `backend/config/tanimlar/tests/test_currency_conversion.py` |
| `docs/architecture/faz3-4-uygulama-raporu.md` |

### Değiştirilen (modified)
| Dosya |
|-------|
| `backend/config/fiyatlama/services/fiyat_hesaplama.py` |
| `backend/config/fiyatlama/services/__init__.py` |
| `backend/config/tanimlar/services/__init__.py` |
| `AGENTS.md` |
| `backend/README.md` |
| `docs/architecture/mevcut-mimari.md` |
| `docs/architecture/faz3-etki-analizi.md` |
| `docs/decisions/ADR-0008-faz3b-kur-fiyatlama-quote.md` |
| `docs/decisions/README.md` |
| `docs/analysis/README.md` |
| `.cursor/skills/business-domain/SKILL.md` |
| `.cursor/skills/testing-quality/SKILL.md` |

### Commit dışı bırakılmalı
| Dosya | Not |
|-------|-----|
| `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.docx` | Untracked; 3.4 ile ilgili değil |

---

## 3. Henüz tamamlanmamış işler

- 3.4 değişikliklerinin **commit / push**’u (onay gerekir).
- Dilim **3.5:** `PricingService.quote()`, `PriceQuote` + Line, immutability (app + DB trigger), quote TTL assert, teklif seçimi, sözleşme `cozumle` orkestrasyonu.
- B-01 platform hizmet payı (hukuk).
- ADR §6: kur lisans; **TRY dışı yuvarlama** muhasebe doğrulaması (kodda geçici `0.01` HALF_UP).

---

## 4. Çalıştırılan testler ve gerçek sonuçları

Çalışma dizini: `backend/config`. Ortam: PostgreSQL (proje varsayılanı).

| # | Komut | Sonuç |
|---|--------|--------|
| 1 | `python manage.py test fiyatlama.tests.test_fiyat_hesaplama fiyatlama.tests.test_uc_model_hesaplama fiyatlama.tests.test_fiyat_motoru tanimlar.tests.test_currency_conversion tanimlar.tests.test_kur_politikasi --verbosity=1` | **37 OK**, 0 fail, 0 skip (~5.5s) |
| 2 | `python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests --verbosity=1` | **228 OK**, 0 fail, 0 skip (~284s) |
| 3 | `python manage.py makemigrations --check --dry-run` | **No changes detected** |

Skill baseline notu: Dilim 3.4 sonrası **228 tests OK** (2026-11-08).

---

## 5. Başarısız testler ve hata mesajları

Yok. Yukarıdaki koşularda başarısız test raporlanmadı.

---

## 6. Migration durumu

- Dilim 3.4 için **yeni migration yok** (yalnız servis/test/docs).
- `makemigrations --check --dry-run` temiz.
- Önceki kur şeması: `tanimlar.0002_faz3_3_kur_politikasi` + `0003_faz3_3_kur_index_rename` (zaten `0a77b26` / 3.3 commit zincirinde).

---

## 7. Tespit edilen mimari veya güvenlik riskleri

| Risk | Etiket |
|------|--------|
| B-01 gizli/platform servis payı kodlanmadı; 3.5 quote toplamı bunu içermeyecek | Bilinçli kapsam |
| TRY dışı quantize geçici `0.01` — ADR-0008 §6 muhasebe doğrulaması açık | PLANLAMA / ürün-finans |
| Kur sağlayıcı lisans §6 | DOĞRULANAMADI |
| `fiyat_motoru` metal `saf_birim_fiyat` / `ek_bedel` / `tas` için hedef PB varsayar; quote orkestrasyonu 3.5’te birleştirmeli | Bilinçli sınır |
| 3.4 uncommitted; kayıp riski commit/push olmadan | Operasyonel |
| Windows’ta klasör adı IDE’de hâlâ `Backend` görünebilir; git index `backend/` | Bilinen FS case |

Tenant izolasyonu / RBAC bu dilimde yeni HTTP yüzeyi eklenmedi; kur resolve mevcut `kur_servisi` kurallarını kullanır.

---

## 8. Nerede kalındı

- **Son işlem:** Dilim 3.4 uygulama + test + docs tamam; **commit/push yapılmadı**.
- **Son dokunulan rapor/doküman seti:** `docs/architecture/faz3-4-uygulama-raporu.md` ve yaşayan envanter/AGENTS/skills.
- **Kod odak noktası:** `backend/config/fiyatlama/services/fiyat_hesaplama.py`, `fiyat_motoru.py`, `tanimlar/services/currency_conversion.py`.
- **Faz 3.5’e geçilmedi.**

---

## 9. Faz 3.4 için kalan görevler

1. Ürün sahibi onayıyla 3.4 dosyalarını stage et (`.docx` hariç).
2. Tek açıklayıcı commit + `origin/adim-1-ilerleme` push (force yok).
3. İsteğe bağlı: staging’de migrate gerekmez (şema yok); regresyon tekrarı yalnız yeni değişiklik varsa.

3.4 işlevsel kapsam kod tarafında **COMPLETE** sayıldı; kapanış için yalnızca git güvence adımı açık.

---

## 10. Sonraki Agent — kesin adımlar

1. Bu dosyayı ve `docs/architecture/faz3-4-uygulama-raporu.md` + ADR-0008 §2.1.1 / §8 dilim 3.5’i oku.
2. `git status` ile uncommitted 3.4 ağacını doğrula; **onay olmadan commit etme**.
3. 3.4 commit istenirse: yalnız ilgili dosyalar, `.docx` hariç, testleri sebepsiz yeniden koşma.
4. **Faz 3.5 talimatı gelmeden** `PriceQuote` / `PricingService.quote` / trigger yazma.
5. 3.5 başlarken tüket: `hesapla_modele_gore` / `hesapla_*`, `currency_conversion.convert`, `kur_servisi.resolve_*`, `cozumle`, teklif kapısı `teklif_eslestirme_uygun_mu`; B-01 kalemini kodlama.
6. Skill yükle: görev tipine göre tek skill (`django-engineering` veya `business-domain` / `testing-quality`).
7. Çalışma kökü: `backend/config` (`manage.py`).

---

**Özet hüküm:** Dilim 3.4 kod+test+docs hazır; **uncommitted**. Sonraki sohbet önce git güvencesi, sonra açık talimatla 3.5.
