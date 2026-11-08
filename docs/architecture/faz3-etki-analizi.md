# Faz 3 — Etki analizi (teklif / fiyatlama / snapshot)

**Tarih:** 2026-11-08 (analiz) · **Uygulama notu:** dilim **3.1–3.3 uygulandı** — [`faz3-1`](faz3-1-uygulama-raporu.md) / [`faz3-2`](faz3-2-uygulama-raporu.md) / [`faz3-3`](faz3-3-uygulama-raporu.md); §3 bulguları tarihsel (analiz anı).  
**Kapsam (analiz):** Salt okunur kod incelemesi; o tarihte kod/migration değişmedi.  
**Bağlı:** Kanonik rapor K-006…K-009, K-011…K-013, K-019; §5.2, §5.4, §9.3, §9.4, §12.3; ADR-0005, ADR-0006; ADR-0007 Faz 3a (**Kabul**) / ADR-0008 Faz 3b (**Kabul**; 3.3).

Etiketler: **DOĞRULANDI** / **DOĞRULANAMADI** / **PLANLAMA BULGUSU**

---

## 1. Özet

Faz 3’te yeniden kullanılacak çekirdek: saf `hesapla()`, `cozumle()` iskeleti, `FiyatSozlesmesi` versiyon zinciri, `TedarikciTeklif` + eşleştirme alanları, tenant selector’lar.  
**3.1 sonrası kapandı:** teklif durum servisi (`teklif_servisi`), versiyon/geçerlilik, YAYINDA partial unique, CASCADE→PROTECT, eşleşme predicate.  
**Hâlâ açık:** K-007 çelişkisi, K-008 tarih exclusion, `PriceQuote` / kur (ADR-0008), iki `UrunTasi`, para birimi tutarsızlığı, `Varyant.stok` / `stok_adet` ikiliği (Faz 4’e sınır).

---

## 2. Yeniden kullanılacak (koru / sarmala)

| Bileşen | Kanıt | Not |
|---------|-------|-----|
| `hesapla()` saf Decimal | `fiyatlama/services/fiyat_hesaplama.py:25–82` | Yalnız metal formülü; GRAM_BIRIM/SABIT_PARCA quote’a ADR-0008 §2.1.1 ile bağlanır. **DOĞRULANDI** |
| `cozumle()` skor + belirsizlik hatası | `fiyatlama/models/sozlesme_cozumleme.py:33–101` | K-007 sonrası kalem unique ile uyumlu hale getirilecek. **DOĞRULANDI** |
| `FiyatSozlesmesi` versiyon / PROTECT | `fiyat_sozlesmesi.py:58–65`, `:77–95` | Yayın immutability servisle zorlanacak. **DOĞRULANDI** |
| `TedarikciTeklif` fiyat modeli + constraint | `tedarikci_teklif.py:9–71`, `:126–143` | Durum servisi + versiyon/geçerlilik eksik. **DOĞRULANDI** |
| Eşleştirme (Faz 2) | `urunler/services/eslestirme_servisi.py` | Boş `eslestirme_durumu` = bekliyor = fiyat motorunda yok (ADR-0007 kapı; quote ADR-0008; C istisnası yok). **DOĞRULANDI** (alan default `''`) |
| Teklif admin readonly durum | `fiyatlama/admin/admin.py:98–115` | ADR-0006 bilinçli sınır; Faz 3 servis açacak. **DOĞRULANDI** |
| Tenant selectors | `fiyatlama/selectors/tenant.py` | Teklif/sözleşme scope kalır. **DOĞRULANDI** |
| `approve_teklif` / `manage_sozlesme` seed | `firmalar/role_permissions.py` + Meta permissions | Serviste henüz `require_perm` yok (ADR-0006 O6). **DOĞRULANDI** |
| Varyant: katalog vs teklif taş bedeli ayrımı (doktrin) | `varyant.py:171–201` | Doğru yön; isimlendirme K-011. **DOĞRULANDI** |

---

## 3. Kırılacak / tamamlanacak noktalar

### 3.1 Tedarikçi teklifi yaşam döngüsü

> **Uygulama (2026-11-08):** dilim 3.1 ile kapatıldı — `teklif_servisi`, `versiyon`/`onceki_teklif`/`gecerlilik_*`, YAYINDA partial unique, `varyant` PROTECT, `teklif_eslestirme_uygun_mu`. Kanıt: [`faz3-1-uygulama-raporu.md`](faz3-1-uygulama-raporu.md). Aşağıdaki satırlar **analiz anı** bulgularıdır.

| Bulgu (analiz anı) | Etiket | Kanıt (o tarih) |
|-------|--------|-------|
| `durum` alanları var; geçiş servisi yok | DOĞRULANDI | o tarih: model + admin readonly |
| `approve_teklif` yalnız Meta/seed | DOĞRULANDI | o tarih: serviste `require_perm` yoktu |
| `valid_from` / `valid_until` / teklif `versiyon` yok | DOĞRULANDI | o tarih: alan yoktu → 3.1’de eklendi |
| `varyant` FK **CASCADE** | DOĞRULANDI | o tarih CASCADE → 3.1 PROTECT |
| `tedarikci_mi` doğrulaması yok | DOĞRULANDI | o tarih; 3.1 serviste sahiplik |
| Aktif teklif çakışma (firma+varyant+SKU) yok | DOĞRULANDI | o tarih; 3.1 YAYINDA partial unique |
| K-006 eski “ürün sahibi = tedarikçi” kanıtı | PLANLAMA BULGUSU | ADR-0005 sonrası katalog platform; teklif↔varyant sahipliği |

### 3.2 K-007 sözleşme kalemi çelişkisi

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| `clean()` genel+spesifik aynı metal’i yasaklar | DOĞRULANDI | `fiyat_sozlesmesi_kalemi.py:11–14`, `:90–105` |
| `cozumle()` spesifik > genel hedefler | DOĞRULANDI | `sozlesme_cozumleme.py:79–82` |
| DB unique (sozlesme+metal+ayar) yok; NULL unique tuzağı | DOĞRULANDI | Meta `:61–69`; ADR-0007: `nulls_distinct=False` veya partial unique seti |

**Karar (ADR-0007 / 3.2):** clean çelişkisini kaldır; unique `(sozlesme, metal, ayar)` (ayar NULL dahil partial); cozumle fallback koru.

### 3.3 K-008 aktif tarih çakışması

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| Tarih sırası CheckConstraint var | DOĞRULANDI | `fiyat_sozlesmesi.py:78–83` |
| AKTIF aralık exclusion / servis kilidi yok; NULL kanal exclusion tuzağı | DOĞRULANDI | `:77–95`; ADR-0007: `COALESCE(kanal,0)` + `btree_gist` (**DOĞRULANAMADI** prod extension) |
| Yayın/pasifleştirme servisi yok | DOĞRULANDI | Model `save()` yalnız `full_clean` `:115–117` |

### 3.4 K-009 orkestrasyon / snapshot

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| `PricingService.quote` / `PriceQuote` yok | DOĞRULANDI | `fiyatlama/services/` yalnız `fiyat_hesaplama.py` |
| `PriceCalculationLog` teknik log; teklif FK yok | DOĞRULANDI | `price_calculation_log.py:6–9`, `:17–32` |
| `hesapla` çıktısında para birimi / kur / sözleşme yok | DOĞRULANDI | `fiyat_hesaplama.py:72–82` |
| Formülde `ek_bedel`, platform servis yok; vergi yok | DOĞRULANDI | `toplam = metal+iscilik+marj+tas` `:67` vs rapor §5.4 (`+ vergiler`). **Ürün sahibi (2026-11-08):** Faz 3 proforma; KDV/vergi hesaplanmaz (ADR-0008 §2.9; B-06 ertelendi). |
| Log’da `kilit_bitis` var ama kilit servisi yok | DOĞRULANDI | `price_calculation_log.py:56` |

### 3.5 K-011 iki UrunTasi

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| Katalog `urunler.UrunTasi` bedel “TL” | DOĞRULANDI | `urunler/models/urun_tasi.py:33` |
| Teklif `fiyatlama.UrunTasi` + `para_birimi` | DOĞRULANDI | `fiyatlama/models/urun_tasi.py:5–23` |
| Aynı verbose “Ürün Taşı” | DOĞRULANDI | her iki Meta |

### 3.6 K-012 / K-019 para ve kur

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| `Varyant.sabit_fiyat` / `ek_bedel` “TL” sabiti | DOĞRULANDI | `varyant.py:48–54` |
| `MetalKuru` TL/gr; kaynak enum; gecikme/geçerlilik yok | DOĞRULANDI | `metal_kuru.py:12–31` |
| `DovizKuru` kur tipi (alış/satış) yok | DOĞRULANDI | `doviz_kuru.py:9–21` |
| Dönüşüm servisi yok | DOĞRULANDI | grep `CurrencyConversion` yok |
| Stale kur politikası yok | DOĞRULANDI | modellerde max_age alanı yok |

### 3.7 Stok (Faz 3 sınırı / Faz 4)

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| `Varyant.stok` + `TedarikciTeklif.stok_adet` ikiliği | DOĞRULANDI | `varyant.py:57`; `tedarikci_teklif.py:66` |
| Faz 3’te ticari stok motoru yok | PLANLAMA BULGUSU | K-010 → Faz 4; teklif `stok_adet` quote uygunlukta okunur, rezervasyon yok |

### 3.8 Kör havuz / alıcı görünürlük

| Bulgu | Etiket | Kanıt |
|-------|--------|-------|
| Admin listede tedarikçi/maliyet gizleme kısmi | DOĞRULANDI | `fiyatlama/admin/admin.py` `user_may_see_fiyat_maliyet` |
| Alıcı API yok | DOĞRULANDI | DRF Faz 7; B-02 konfigürasyon |
| Servis bedeli kalemi `hesapla`’da yok | DOĞRULANDI | `fiyat_hesaplama.py:67` |

---

## 4. Veri / migration riskleri (planlama)

| Risk | Etiket |
|------|--------|
| Yerel/staging teklif+sözleşme satır sayısı | DOĞRULANAMADI (bu turda DB envanteri yok) |
| CASCADE→PROTECT: silinmiş varyanta bağlı teklif | PLANLAMA BULGUSU — taşıma öncesi orphan kontrolü |
| K-007 clean gevşetince mevcut veri | PLANLAMA BULGUSU — genel+spesifik zaten clean ile engelli; mevcut DB uyumlu olmalı |
| `PriceCalculationLog` → `PriceQuote` taşıma | PLANLAMA BULGUSU — log ticari truth değil; quote yeni tablo, log teknik kalabilir |

---

## 5. Faz 3 dilim önerisi (sıra)

| Dilim | ADR | Konu |
|-------|-----|------|
| **3.0** | ADR-0007 (3a) | Staging yok (uzak DB yok, yalnız yerel PostgreSQL); yerel `btree_gist` 1.8 doğrulandı (CREATE EXTENSION OK); üretim yetkisi **DOĞRULANAMADI** — hosting henüz yok |
| **3.1** | ADR-0007 (3a) | Teklif yaşam döngüsü + versiyon swap + CASCADE→PROTECT + predicate — **uygulandı** |
| **3.2** | ADR-0007 (3a) | K-007/K-008 (sözleşme NULL-safe / exclusion) — **uygulandı** |
| **3.3** | ADR-0008 (3b) | Kur politikası — **uygulandı** |
| **3.4** | ADR-0008 (3b) | Üç model hesap + CurrencyConversion — **uygulandı** |
| **3.5** | ADR-0008 (3b) | PriceQuote + trigger — **uygulandı** |
| **3.6** | ADR-0008 (3b) | kör havuz + K-011 — **uygulandı** |
| **3.7** | ADR-0008 (3b) | PriceLock arayüzü → Faz 4 |

---

## 6. Sonraki adım

Dilim **3.1–3.6 tamam.** Sıradaki: Dilim **3.7** (PriceLock arayüzü) veya Faz 4 (stok/sipariş) — açık talimat + ADR sınırı.
