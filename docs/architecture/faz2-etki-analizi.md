# Faz 2 — Etki analizi (`Urun.tedarikci` / katalog ownership)

**Tarih:** 2026-11-08 (ADR-0005 kabul sonrası güncelleme)  
**Bağlı:** [`ADR-0005`](../decisions/ADR-0005-katalog-platform-ownership.md) — **Kabul edildi**  
**Kapsam notu:** K-014 medya object storage kararı yok → Faz 2 **DIŞI**.

---

## B1. `Urun.tedarikci` bağımlılık tablosu

| Dosya:satır (yaklaşık) | Kullanım | Faz 2 kararı (ADR-0005) |
|------------------------|----------|-------------------------|
| `urunler/models/urun.py` L38–43 | FK `tedarikci`, `tedarikci_urun_kodu` | **Kaldır**; `olusturan_firma` + `kimlik_sinifi` / `kimlik_anahtari` |
| `urunler/models/varyant.py` L29 | `tedarikci_sku` | Teklife taşı; gram bandı alanları |
| `urunler/services/onay_servisi.py` | K-004: `urun.tedarikci_id` | `olusturan_firma_id` + taslak sahipliği |
| `urunler/selectors/katalog_tenant.py` | `tedarikci_id` scope | `olusturan_firma_id` (taslak); teklif ayrı selector |
| `firmalar/selectors/tenant.py` | `tedarikci_id` fallback | Katalog platform; teklif `tedarikci_id` |
| `urunler/admin/urun_admin.py` | tedarikçi alan/arama | `olusturan_firma` yalnız platform; alıcıya yok |
| `urunler/tests/*` | Fixture + K-004 | Yeni sahiplik + eşleştirme testleri |
| `urunler/migrations/0001_initial.py` | Şema | Yeni migration: ekle → doldur → kaldır |
| `fiyatlama/models/tedarikci_teklif.py` | ticari bağ | **Kalır** + eşleştirme alanları |
| Seed `seed_urunler.py` | tedarikçi ile ürün | Platform ürün + teklif seed |

**DOĞRULANDI:** Bağımlılık yolları grep ile doğrulandı (Faz 1.1 doğrulama turu).  
**PLANLAMA BULGUSU → KARAR:** Taşıma sırası ADR-0005 §6’da bağlayıcı.

---

## B2. Veri envanteri (yerel DB, salt okunur)

| Metrik | Değer | Sınıf |
|--------|--------|-------|
| Firma | ≥1 (platform) | DOĞRULANDI (önceki tur) |
| Urun | 0 | DOĞRULANDI |
| Urun.tedarikci dolu | 0 | DOĞRULANDI |
| Varyant / TedarikciTeklif | 0 | DOĞRULANDI |
| Stok mismatch | 0 | DOĞRULANDI |

**DOĞRULANAMADI:** Staging/üretim envanteri. Yerelde taşıma riski düşük; dolu ortamlarda §13.2 stok birleştirme yasağı geçerli.

---

## B3. İş kartı sırası

1. K-015 SEO marka parametresi  
2. K-016 kategori taşıma + alt ağaç derinliği  
3. Ownership / eşleştirme (ADR-0005 model + servis)  
4. K-014 — kapsam dışı  

---

## B4 bağlantısı

Karar metni: [`ADR-0005`](../decisions/ADR-0005-katalog-platform-ownership.md).
