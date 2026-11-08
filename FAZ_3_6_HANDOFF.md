# Faz 3.6 — Agent devir raporu

**Tarih:** 2026-11-08  
**Dal:** `adim-1-ilerleme`  
**Önceki checkpoint:** `b516893` — Dilim 3.4–3.5 (commit’li)  
**Kod kökü:** `backend/config/`  
**Kapsam:** Kör havuz (B-02) + K-011 rename. **Faz 3.7 başlanmadı.**

3.6 değişiklikleri **henüz commit edilmedi** (ürün sahibi onayı gerekir).

---

## 1. Tamamlananlar

### K-011
- `fiyatlama.UrunTasi` → `TeklifTasMaliyeti` (`RenameModel`, tablo yeniden adlandırıldı).
- Katalog `urunler.UrunTasi` korundu (ProductStone).
- Birleştirme yok; quote taş bedeli yalnız teklif maliyetinden.
- Deprecated alias: `fiyatlama.models.UrunTasi = TeklifTasMaliyeti`.

### Kör havuz / B-02
- `selectors/buyer_quote.py`: alıcı DTO (`toplam_vergisiz`, PB, geçerlilik, ürün, gram başı); satır/tedarikçi/maliyet yok.
- Object-level: kapsam dışı → `BuyerQuoteNotFound` (404).
- `PriceQuoteAdmin` alıcı alan maskesi; satır inline yalnız platform maliyet.
- `TeklifTasMaliyeti` alıcıya kapalı (queryset + module permission).

### Süreç
- `AGENTS.md`: dilim sonu `FAZ_*_HANDOFF.md` + Git checkpoint standardı eklendi.

---

## 2. Dosyalar

### Oluşturulan
| Dosya |
|-------|
| `fiyatlama/models/teklif_tas_maliyeti.py` |
| `fiyatlama/migrations/0008_faz3_6_k011_teklif_tas_maliyeti.py` |
| `fiyatlama/migrations/0009_faz3_6_teklif_help_text.py` |
| `fiyatlama/selectors/buyer_quote.py` |
| `fiyatlama/tests/test_faz3_6_kor_havuz_k011.py` |
| `docs/architecture/faz3-6-uygulama-raporu.md` |
| `FAZ_3_6_HANDOFF.md` |

### Değiştirilen
| Dosya |
|-------|
| `fiyatlama/models/__init__.py` (eski `urun_tasi.py` silindi) |
| `fiyatlama/admin/admin.py` |
| `fiyatlama/selectors/tenant.py`, `__init__.py` |
| `mevcut-mimari.md`, `faz3-etki-analizi.md`, AGENTS, README, skills |

### Commit dışı
| Dosya | Not |
|-------|-----|
| `docs/*.docx` | İlgisiz; stage etme |

---

## 3. Testler

| # | Komut | Sonuç |
|---|--------|--------|
| 1 | `python manage.py test fiyatlama.tests.test_faz3_6_kor_havuz_k011` | **12 OK** |
| 2 | `python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests` | **254 OK** (~228s) |
| 3 | `makemigrations --check --dry-run` | **No changes detected** |

---

## 4. Migration

- `fiyatlama.0008_faz3_6_k011_teklif_tas_maliyeti` — RenameModel  
- `fiyatlama.0009_faz3_6_teklif_help_text` — AlterField help_text  
- Yerel migrate uygulandı; üretim migrate onaysız yapılmaz.

---

## 5. Riskler

| Risk | Etiket |
|------|--------|
| B-01 / B-06 hâlâ kod dışı | Bilinçli |
| Alıcı satır kırılımı hukuk onaysız kapalı (B-02) | Bilinçli |
| `UrunTasi` alias deprecated — yeni kod `TeklifTasMaliyeti` kullanmalı | Operasyonel |
| 3.6 uncommitted | Operasyonel |
| DRF yok — API masking Faz 7’de tekrarlanmalı | PLANLAMA |

---

## 6. Sonraki agent

1. Bu handoff + `faz3-6-uygulama-raporu.md` oku.  
2. Onayla 3.6 commit (docx hariç); isteğe bağlı push.  
3. **3.7** yalnız açık talimat + ADR-0008 PriceLock sınırı ile.  
4. Skill: güvenlik → `multi-tenant-security`; model → `django-engineering`.  
5. Kök: `backend/config`.

---

**Özet hüküm:** Dilim 3.6 kod+test+docs **COMPLETE**; commit bekliyor. 3.7’ye hazır (PriceLock arayüzü).
