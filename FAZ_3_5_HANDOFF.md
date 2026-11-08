# Faz 3.5 — Agent devir raporu

**Tarih:** 2026-11-08  
**Dal:** `adim-1-ilerleme`  
**Kod kökü:** `backend/config/`  
**Kapsam:** Dilim 3.5 (`PricingService.quote` + `PriceQuote` + immutability). **Faz 3.6 başlanmadı.**

Not: 3.4 uncommitted ağacı bu dilimde korunarak üzerine 3.5 eklendi; commit/push ürün sahibi onayı ister.

---

## 1. Tamamlananlar

- `PriceQuote` / `PriceQuoteLine` (proforma, `toplam_vergisiz`; B-01/B-06 satırı yok).
- `pricing_service.quote`: yayın → TTL → kur (B-05) → teklif seçimi → `cozumle` → hesap → snapshot.
- Teklif seçimi: `oncelik`↓ → iç maliyet↑ → `id`↑.
- İmmutability: uygulama + PostgreSQL UPDATE/DELETE trigger (`0007`).
- Admin salt okunur; selector tenant scope.
- Yaşayan docs + skills güncellendi.

---

## 2. Dosyalar

### Oluşturulan
- `fiyatlama/models/price_quote.py`
- `fiyatlama/services/pricing_service.py`
- `fiyatlama/migrations/0007_faz3_5_price_quote.py`
- `fiyatlama/tests/test_price_quote.py`
- `docs/architecture/faz3-5-uygulama-raporu.md`
- `FAZ_3_5_HANDOFF.md`

### Değiştirilen (3.5)
- `fiyatlama/models/__init__.py`, `services/__init__.py`, `selectors/tenant.py`, `admin/admin.py`
- `fiyat_hesaplama.py` / `fiyat_motoru.py` (yorum)
- `mevcut-mimari.md`, `faz3-etki-analizi.md`, ADR-0008 checklist, AGENTS, README, skills

---

## 3. Testler

| Komut | Sonuç |
|-------|--------|
| `python manage.py test fiyatlama.tests.test_price_quote` | **14 OK** |
| `python manage.py test fiyatlama.tests tanimlar.tests` | **109 OK** |
| `python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests` | **242 OK** (~210s) |
| `makemigrations --check --dry-run` | No changes |

---

## 4. Riskler

- B-01 / B-06 bilinçli dışı.
- TRY dışı yuvarlama geçici `0.01` (ADR §6).
- 3.4+3.5 uncommitted (operasyonel).
- Alıcı satır kırılımı kapalı (B-02 → 3.6).

---

## 5. Sonraki

1. Onayla 3.4+3.5 commit/push (`.docx` hariç).
2. Dilim **3.6**: kör havuz alıcı yüzeyi + K-011 taş rename.
