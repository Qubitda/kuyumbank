# İlerleme günlüğü

Tek doğruluk kaynağı: `docs/analiz_v3.md`.  
Koruma kuralları: `.cursor/rules/proje.mdc` (dal: `adim-0-koruma-kurallari`).

---

## Adım 0 — Mevcut kod envanteri (Ask / salt okuma)

**Tarih:** 2026-11-04  
**Dal:** (kod değişmedi; rapor bu dosyaya Adım 1’de işlendi)  
**Eklenen dosyalar:** yok (yalnızca okuma)

### a) Dokümanda olup projede ZATEN VAR olanlar

| Konu | Dosya |
| --- | --- |
| Firma (alıcı/tedarikçi/platform) | `Backend/config/firmalar/firma.py` |
| Kullanıcı + roller | `Backend/config/firmalar/kullanici.py` |
| Kıymetli metal | `Backend/config/tanimlar/kiymetli_metal.py` |
| Ayar/milyem | `Backend/config/tanimlar/ayar_milyem.py` |
| Metal kuru (`DateTimeField`, gün içinde çok kayıt) | `Backend/config/tanimlar/metal_kuru.py` |
| Döviz kuru | `Backend/config/tanimlar/doviz_kuru.py` |
| Fiyat grubu (sözleşme hazırlığı) | `Backend/config/tanimlar/fiyat_grubu.py` |
| Kategori (hiyerarşik) | `Backend/config/urunler/kategori.py` |
| Ürün + varyant + taş + onay akışı | `urunler/urun.py`, `varyant.py`, `urun_tasi.py`, `servisler.py` |
| PostgreSQL, env settings | `Backend/config/config/settings.py` |
| Seed / testler | `seed_*.py`, `firmalar/tests.py`, `urunler/tests.py` |

### b) Dokümanda olup projede OLMAYANLAR

- `calisma_modu`, `teslimat_modu`
- Üç katman: `UrunModel` / `UrunVaryant` / `TedarikciTeklif` (mevcut: `Urun` → `Varyant`)
- `aile` (kuyum/mucevher/taki), `UrunGorsel`
- `Sozlesme`, `SozlesmeCozumleyici`
- `FiyatHesaplamaServisi`, `PriceCalculationLog`
- `Talep` / `AliciTeklifi`, fiyat kilidi
- `Siparis`, `Sevkiyat`, `KontrolKaydi`
- App’ler: `katalog`, `fiyatlama`, `talep`, `siparis`, `operasyon`, `audit`
- `django-simple-history`
- Alıcıya sızdırmaz serializer katmanı

### c) Dokümanla ÇELİŞEN mevcut kod

| Dosya | Çelişki |
| --- | --- |
| `urunler/urun.py` | Tedarikçi `Urun` üzerinde; doküman model’i platformda, teklifi ayrı tutar |
| `urunler/varyant.py` | Gram/fiyat/stok varyantta; dokümanda fiyat/stok teklifte |
| `urunler/urun_tasi.py` | Taş ürüne bağlı; dokümanda teklife bağlı |
| İsimler | `KiymetliMetal` / `MetalKuru` / `DovizKuru` vs dokümandaki `PreciousMetal` / `MetalRate` / `FXRate` (davranış yakın; mevcut kod yeniden adlandırılmayacak) |

### d) Önerilen sıra (mevcut koda dokunmadan; ≤3 yeni dosya / adım)

| # | Adım | Yeni dosyalar | Mevcut dosya değişikliği? | Risk |
| --- | --- | --- | --- | --- |
| 1 | İlerleme günlüğü | `docs/ILERLEME.md` | Yok | Yok |
| 2 | Kur “en güncel” servisi | `tanimlar/servisler.py`, `tanimlar/tests/test_kur_servisleri.py` | Yok | Düşük |
| 3 | Fiyat motoru iskeleti (saf Python) | `fiyatlama/` paketinden en fazla 3 dosya | `settings.py` (onaylı) | Orta |
| 4 | Fiyat motoru testleri (Excel örnekleri) | `fiyatlama/tests/...` | Yok | Düşük |
| 5 | Sözleşme modeli | model + servis + test | settings + migration onayı | Yüksek |
| 6 | `SozlesmeCozumleyici` | servis + test | Yok | Orta |
| 7 | Firma mod alanları | — | `firmalar/firma.py` + migration onayı | Yüksek |
| 8+ | Yeni katalog katmanı (`katalog` app), eski `urunler` silinmeden | yeni modeller | settings; ileride köprü | Yüksek |
| … | Talep → sipariş → operasyon | yeni app’ler | settings/migration onayları | Yüksek |

**Açık karar:** Eski `urunler.Urun` canlı kalacak mı, yoksa yeni `katalog` app’i yanına mı eklenecek? Adım 8’e kadar netleştirilmeli.

**Bilinen sorunlar:** Yok (Adım 0 yalnızca okuma).

**Sıradaki adım:** Adım 1 — bu dosyanın oluşturulması (aşağıda).

---

## Adım 1 — İlerleme günlüğü

**Tarih:** 2026-11-04  
**Dal:** `adim-1-ilerleme`  
**Yapılan:** Adım 0 raporunu `docs/ILERLEME.md` olarak kaydetmek.  
**Eklenen dosyalar:**
- `docs/ILERLEME.md`

**Mevcut dosya değişikliği:** yok  
**Test:** dosya belgesi; kod testi yok  
**Sıradaki adım:** Adım 2 — `tanimlar` kur “en güncel” servisi (`tanimlar/servisler.py` + test)  
**Bilinen sorunlar:** `adim-0-koruma-kurallari` henüz `main`’e merge edilmedi; kural dosyası o dalda.
