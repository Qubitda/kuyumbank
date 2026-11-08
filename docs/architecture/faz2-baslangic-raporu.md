# Faz 2 — Başlangıç raporu

**Tarih:** 2026-11-08  
**Önkoşul:** Faz 1.1 GO; ADR-0005 **Kabul edildi**

---

## Tamamlananlar

### Docs
| Dosya | Sorumluluk |
|-------|------------|
| `docs/decisions/ADR-0005-katalog-platform-ownership.md` | K1–K6 bağlayıcı; Kabul |
| `docs/decisions/ADR-0005-bekleyen-kararlar.md` | KAPANDI → ADR’ye yönlendirir |
| `docs/architecture/faz2-etki-analizi.md` | Karar sonrası güncelleme |

### K-015
| Dosya | Sorumluluk |
|-------|------------|
| `config/settings.py` | `PLATFORM_BRAND_NAME`, `VARYANT_GRAM_BANDI_ORAN` |
| `.env.example` | Marka / gram bandı örnekleri |
| `urunler/services/seo_servisi.py` | Teknik SEO fallback |
| `urunler/models/urun.py`, `kategori.py` | “Örnek Kuyumculuk” / pazarlama metni kaldırıldı |

### K-016
| Dosya | Sorumluluk |
|-------|------------|
| `urunler/models/kategori.py` | `alt_agac_yuksekligi` + clean’de alt ağaç |
| `urunler/services/kategori_servisi.py` | `kategori_tasi` |

### Ownership / eşleştirme (ADR-0005 dilim 1)
| Dosya | Sorumluluk |
|-------|------------|
| `urunler/models/urun.py` | `olusturan_firma`, `kimlik_*`; `tedarikci` kaldırıldı |
| `urunler/models/varyant.py` | `gram_bandi_min/max` |
| `fiyatlama/models/tedarikci_teklif.py` | Eşleştirme alanları |
| `urunler/services/onay_servisi.py` | K-004 → `olusturan_firma` |
| `urunler/services/eslestirme_servisi.py` | Öner/onayla/reddet/ayır; birleştir kapıları |
| `urunler/selectors/katalog_tenant.py` | `olusturan_firma` scope |
| `urunler/admin/urun_admin.py` | Admin alanları |
| Migrations `urunler.0005–0006`, `fiyatlama.0003` | Şema |

---

## Testler

```text
python manage.py check → 0 issues
python manage.py makemigrations --check --dry-run → No changes detected
python manage.py test firmalar.tests urunler.tests fiyatlama.tests.test_fiyat_hesaplama
→ Ran 78 tests — OK (PostgreSQL)
```

---

## Riskler / sonraki dilim

| Madde | Not |
|-------|-----|
| `urunleri_birlestir` | **Ertelendi** (ADR-0006 B4b); bu fazda implementasyon yok |
| Onaylı katalogda tedarikçi varyant görünürlüğü | ADR §9 açık |
| K-014 medya | Kapsam dışı |
| Üretim migrate | Yapılmadı (ayrı onay) |
