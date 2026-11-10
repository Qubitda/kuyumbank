# ADR-0008 — Faz 3b: Kur politikası, fiyat hesabı, PriceQuote snapshot, görünürlük

> **Arşiv notu:** Bu ADR metni 2026-11-09 tarihinde `KUYUMBANK_MASTER.md` §6.3 arşivinden taşındı; içerik değiştirilmedi. Artık var olmayan dosyalara giden bağlantılar düz metne çevrildi. Güncel karar durumu: [README](README.md).

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Kabul:** 2026-11-08 (ürün sahibi — B-02…B-05 + çoklu YAYINDA; kayıt: `docs/adr-0008-urun-kararlari.md` _(dosya kaldırıldı)_)  
**Bağlı:** ADR-0007 (Faz 3a, Kabul), ADR-0005, ADR-0006 (Kabul); kanonik rapor K-009, K-011…K-013, K-019; §5.2, §5.4, §9.3, §9.4, §12.3; B-01…B-06  
**Etki analizi:** tarihsel özet bu master arşivinde.  
**Önkoşul:** Dilim 3.3+ kodu bu ADR **Kabul** gerektirir. Teklif yaşam döngüsü / K-007 / K-008 → ADR-0007.  
**Onay:** Ürün sahibi kabul etti (agent kendi taslağını onaylamaz)

**Net not:** B-01 gizli platform hizmet payı hukuk görüşü gelmeden servis payı kalemi **kodlanmaz**; B-02 alıcı görünürlük kararı bunu açmaz. B-06 vergi ertelenmesi (proforma) B-01’i kapatmaz.

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/).

---

## 1. Bağlam

ADR-0007 teklif durum makinesi ve sözleşme NULL-safe kısıtlarını tanımlar. Bu ADR: üç fiyat modeli → quote, `PricingService.quote`, kur politikası, `PriceQuote` değişmezliği, alıcı görünürlük, B-06 proforma.

---

## 2. Kararlar (bağlayıcı taslak)

### 2.1.1 Üç teklif fiyat modeli → quote

Mevcut `hesapla()` (`fiyat_hesaplama.py`): yalnız `metal_bedeli = gram × milyem × saf_birim_fiyat` + işçilik + marj + `tas_bedeli`. **GRAM_BIRIM / SABIT_PARCA bilmez.**

Orkestrasyon `PricingService` model seçer; saf çekirdek genişletilir veya model-spesifik saf fonksiyonlar eklenir (Django’suz kalır).

| Model | Quote girdileri | Kalemler (satır) | Yuvarlama |
|-------|-----------------|------------------|-----------|
| **METAL_BAZLI** | `teklif.gram` (veya varyant gram bandı içi), `ayar.milyem`, metal kuru `saf_birim_fiyat`, sözleşme işçilik/marj, teklif `iscilik_override` (varsa işçilik yerine), `teklif_tas_bedeli`, `varyant.ek_bedel` (TRY→quote PB) | `metal`, `iscilik`, `kanal_marj` (alıcı sözleşmesinden), `tas`, `ek_bedel`, `platform_servis` (konfig/sözleşme); **vergi satırı yok** | Ara adım yok; final satır + **vergisiz** `toplam` / `toplam_vergisiz` PB `quantize` (TRY: 0.01, HALF_UP) |
| **GRAM_BIRIM** | `teklif.gram`, `teklif.birim_fiyat`, `teklif.para_birimi` → dönüşüm; taş/ek_bedel/servis/alıcı marj aynı hat | `gram_birim` (= gram × birim, dönüşmüş), `tas`, `ek_bedel`, `platform_servis`, `kanal_marj` — **metal satırı yok**; **vergi satırı yok** | Aynı |
| **SABIT_PARCA** | `teklif.birim_fiyat` (+ PB); gram metal hesabına girmez; taş/ek/servis/marj | `sabit_parca`, `tas`, `ek_bedel`, `platform_servis`, `kanal_marj`; **vergi satırı yok** | Aynı |

Ortak: teklif YAYINDA + geçerli + eşleşme onaylı (ADR-0007 kapısı); kur stale değil; alıcı sözleşmesi çözülür (§2.4.1). Model alan zorunlulukları mevcut DB check + servis. **Faz 3’te KDV/vergi kalemi üretilmez** (§2.9).

### 2.4 PricingService.quote() ve snapshot

**Giriş:** `alici_firma`, `satis_kanali`, `varyant`, isteğe bağlı `teklif_id`; yoksa platform teklif seçimi (§5 ÖNERİ — çoklu YAYINDA).

**Adımlar:** yayınlı ürün/varyant → teklif YAYINDA+geçerli+**eşleşme onaylı** → teklif seçimi → kurlar (stale yok) → **sözleşmeler (§2.4.1)** → PB dönüşüm → model-spesifik hesap (§2.1.1) → **PriceQuote + Line** (immutable).

#### 2.4.1 Hangi sözleşme kimin için?

`FiyatSozlesmesi.KontratTipi`: `ALICI` | `TEDARIKCI` (mevcut model).

| Tip | Firma | Quote’da rol |
|-----|-------|----------------|
| **ALICI** | Alıcı firma | **Satış tarafı:** kanal marjı / platform hizmet (servis payı) kalemleri. `cozumle(firma=alici, kontrat_tipi=ALICI, …)` — **quote için zorunlu çözüm**. Eksik/belirsiz → quote yok. |
| **TEDARIKCI** | Tedarikçi firma | **Maliyet tarafı (opsiyonel Faz 3):** işçilik override yoksa tedarikçi anlaşması; maliyet kırılımı alıcıya gitmez. İlk dilimde: teklif alanları + metal kuru yeterli olabilir; TEDARIKCI sözleşme çözümü “gerekirse” — yoksa teklif `iscilik_override` / model fiyatı. Belirsiz çift çözüm → hata. |

`cozumle` tek firma alır; quote **iki ayrı çağrı** yapabilir (önce ALICI zorunlu; TEDARIKCI koşullu). Snapshot’a her çözülen `sozlesme_id`/`versiyon` yazılır.

**PriceQuote:** alıcı, kanal, varyant, seçilen teklif+versiyon, ALICI (ve varsa TEDARIKCI) sözleşme ref, PB, **`toplam_vergisiz`** (vergi öncesi net; alıcıya vergi dahil/hariç tutar gösterilmez), `gecerlilik_sonu`, kur gözlemleri (alıcı/tedarikçi kur tipi ayrı — B-05), `hesap_girdisi` JSON, aktör, zaman. Belge dili: **proforma / fiyat teklifi** — “fatura” kullanılmaz. Vergi line tipi Faz 3’te üretilmez (§2.9).

**Değişmezlik (zorunlu):** (1) uygulama: `save`/`update` engeli; (2) **DB trigger** (veya eşdeğer RLS/rule) UPDATE/DELETE’i reddeder. Yalnız “mümkünse” değil — finansal zorunluluk.

**Quote TTL:** konfig (B-03); değer yoksa quote üretilmez.

**PriceLock:** Faz 4 arayüzü; bu ADR tanımlar, sipariş tablosu yok.

### 2.5–2.7 K-011 / K-012 / K-019 (Dilim 3.3 kur politikası)

| Madde | Karar |
|-------|--------|
| Sağlayıcı (B-04) | `KurSaglayici`; aynı anda **tek aktif anlık**; otomatik soft hop **yok**. Stale → **LKG + `FEED_STALE_LKG` banner** ([ADR-0018](ADR-0018-cap-piyasa-kur-dayanikliligi.md) **Kabul**). TCMB EOD / manuel kriz snapshot bilinçli düşüş. |
| Gözlem | Mevcut `MetalKuru` / `DovizKuru` genişletilir: `saglayici`, `kur_tipi`, piyasa `zaman` ≠ `alinma_zamani`, manuel `neden` + onaylayan. |
| Stale | `(alinma − zaman)` veya `(now − zaman)` > sağlayıcı `max_gecikme_saniye` → geçersiz; sessiz “son bilinen kur” **yok**. |
| Kur tipi (B-05) | `KurPolitikasi`: `alici_kur_tipi` ve `tedarikci_kur_tipi` ayrı; resolve taraf parametresiyle seçer. |
| Manuel giriş | Neden zorunlu; giren ≠ onaylayan (dört göz); `AuditOlay`; yalnız aktif sağlayıcıya bağlanır. |
| Quote TTL (B-03) | `SatisKanali.quote_ttl_saniye` kanal bazlı konfig; değer yoksa ileride quote üretilmez (3.5). TTL ≤ kullanılan gözlemin max gecikmesi (3.5 assert). |
| Dilim sınırı | **3.3** yalnız kur politikası. **3.4** üç model + CurrencyConversion. **3.5** PriceQuote. K-011 taş rename → 3.6. |

### 2.8 Alıcı görünürlük

**B-02 Kabul (A):** Alıcı varsayılan olarak yalnız `toplam_vergisiz` (+ isteğe bağlı gram başı). Kırılım hukuk onayı olmadan açılmaz. Servis payı ayrı görünür satır olmaz.

**B-01 hukuk görüşü gelmeden servis payı kalemi kodlanmaz** (görünürlük kararı servis payı üretimini açmaz). Alıcı yüzey uygulaması → dilim 3.6.

### 2.9 Vergi

**Ürün sahibi kararı (2026-11-08):** Faz 3 belge türü **proforma / fiyat teklifidir**. KDV ve vergi hesaplaması Faz 3 kapsamı **dışındadır**.

| Madde | Karar |
|-------|--------|
| Hesap / saklama | KDV/vergi **hesaplanmaz**, saklanmaz; alıcıya vergi dahil/hariç tutar **gösterilmez**. |
| Toplam | `PriceQuote` toplamı = vergi öncesi (net). Alan/dokümantasyon adı bunu açıkça belirtir (ör. `toplam_vergisiz`). |
| Belge dili | Quote ve çıktıda **“fatura” kullanılmaz**; **“proforma / fiyat teklifi”**. |
| Oran | Vergi oranı kodda, seed’de veya konfigte **sabitlenmez**. |
| İleride | Ayrı ADR; yeni line tipi veya ayrı katman. Mevcut immutable `PriceQuote` kayıtları **geriye dönük değiştirilmez**. |
| B-06 | Mali müşavir doğrulaması **şimdilik gerekmez**; vergi motoru ihtiyacı doğduğunda yeniden açılır. |

B-01 / gizli platform hizmet payı (şeffaflık) bu ertelemeden **etkilenmez** — ayrı hukuk konusu (§6).

---

## 3. Migration ve veri taşıma

| Adım | İçerik |
|------|--------|
| 4 | Taş rename; PriceQuote + Line; quote UPDATE trigger |
| Reverse | Çakışmada dur; satır silme yok |

Adım 1–3 → ADR-0007.

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| TTL / kur tipi / servis payı sayısal değeri | Konfig; yoksa quote yok |
| Vergi | Faz 3’te yok; proforma (B-06 ertelendi — ürün sahibi kararı) |
| Eşleşme boş | Quote yok (ADR-0007 kapısı; otomatik onaylama yok) |

---

## 5. ÜRÜN SAHİBİ KARARLARI (Kabul 2026-11-08)

| ID | Konu | Karar |
|----|------|--------|
| B-02 | Alıcıya görünen kalem | **A —** Varsayılan **yalnız toplam** (+ isteğe bağlı gram başı). Kırılım hukuk onaysız açılmaz. Servis payı ayrı satır görünmez. |
| B-03 | Quote TTL | **A —** **Kanal bazlı**. TTL ≤ ilgili kur gözleminin max gecikmesi. Sayı finans konfigi. Değer yoksa quote yok. |
| B-04 | Kur sağlayıcı | **A —** Aynı anda **tek aktif provider**; otomatik fallback yok. Manuel: neden + dört göz + audit. Max gecikme konfig. |
| B-05 | Kur tipi | **A —** Alıcı ve tedarikçi için **ayrı tipler**; ikisi de (quote diliminde) snapshot’a. |
| — | Çoklu YAYINDA teklif | Alıcı seçmez. Sıra: `oncelik` ↓ → en düşük iç maliyet → `teklif.id` ↑. (Uygulama: quote dilimi 3.5+) |
| — | Servis payı kaynağı | **Kodlanmaz** (B-01 açık). Taslak not: ALICI kalem + global konfig; hukuk sonrası. |
| — | C sınıfı eşleşme istisnası | **Yok.** |
| B-06 | Vergi/KDV | **ERTELENDİ** (2026-11-08): Faz 3 proforma; KDV/vergi yok; mali müşavir şimdilik gerekmez. |

---

## 6. DIŞ DOĞRULAMA GEREKİR

| ID | Konu |
|----|------|
| B-01 | Platform hukuki rol |
| B-01 | **Gizli (faturaya yedirilen, görünmeyen) platform hizmet payı** — B2B/B2C şeffaflık ve fatura uyumu. **B-06 ertelemesi bunu kapatmaz** (proforma toplamı yine hizmet payını içerebilir; hukuk görüşü açık kalır). |
| — | Kur sağlayıcı lisans |
| — | TRY dışı yuvarlama muhasebesi |

`btree_gist` → ADR-0007 §6.

---

## 7. Kabul testleri (§12.3)

| Ek | Test |
|----|------|
| — | Üç fiyat modeli için quote kalem/toplam (birim test + servis) |
| — | Quote UPDATE trigger reddi |
| — | Kur stale → quote yok; snapshot’a kur yazılır (§12.3 ilgili maddeler) |
| — | Alıcı yüzeyinde maliyet/tedarikçi kimliği yok |

---

## 8. Dilimler

4. **3.3** Kur politikası  
5. **3.4** Üç model hesap + CurrencyConversion  
6. **3.5** quote + trigger immutability — uygulandı  
7. **3.6** kör havuz + K-011 — uygulandı  
8. **3.7** PriceLock arayüzü → Faz 4  

Dilim **3.0–3.2** → ADR-0007.

---

## 9. Non-goals

**KDV/vergi hesaplama ve resmi e-fatura/e-arşiv üretimi (Faz 3 dışı)**; belge türü proforma / fiyat teklifi. Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`. Teklif durum makinesi / K-007 / K-008 (ADR-0007).

---

## 10. Onay checklist

- [x] B-02…B-05 + çoklu YAYINDA: ürün sahibi kabul (2026-11-08)  
- [x] B-06 vergi/KDV: **ertelendi** (proforma)  
- [x] B-01 / gizli hizmet payı: **kapsam dışı** (hukuk bekleniyor; kod yok)  
- [x] ALICI vs TEDARIKCI sözleşme rolü (§2.4.1)  
- [x] Durum: **Kabul edildi** (ürün sahibi)  
- [x] Üç fiyat modeli + `toplam_vergisiz` + quote trigger — dilim 3.4–3.5 uygulama  
- [ ] §6 kalan dış doğrulama (kur lisans, TRY dışı yuvarlama) — uygulama sırasında açık
