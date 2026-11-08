# ADR-0007 — Faz 3: Tedarikçi teklifi, fiyatlama, fiyat snapshot

**Durum:** Taslak  
**Tarih:** 2026-11-08 (revizyon: kabul öncesi eksikler)  
**Bağlı:** ADR-0005, ADR-0006 (Kabul); kanonik rapor K-006…K-009, K-011…K-013, K-019; §5.2, §5.4, §9.3, §9.4, §12.3; B-02…B-06  
**Etki analizi:** [`docs/architecture/faz3-etki-analizi.md`](../architecture/faz3-etki-analizi.md)  
**Onay:** Ürün sahibi onayı bekleniyor (agent Kabul işaretlemez)

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/) (`UniqueConstraint.nulls_distinct`).

---

## 1. Bağlam

Faz 2 katalog ownership’i ayırdı. Fiyatlama parçalı: saf `hesapla` yalnız metal formülünü bilir; teklifte üç `fiyat_modeli` var. Teklif durum servisi, `PriceQuote`, kur politikası, K-007/K-008 (NULL-safe unique/exclusion) eksik. ADR-0006: teklif `durum` admin salt okunur; `approve_teklif` / `manage_sozlesme` Faz 3’e ertelenmişti.

---

## 2. Kararlar (bağlayıcı taslak)

### 2.1 Tedarikçi teklifi yaşam döngüsü

| Madde | Karar |
|-------|--------|
| Sahiplik | Teklif `tedarikci_id == kullanici.firma_id`; firma `tedarikci_mi=True`. Client `tedarikci_id` güvenilmez. |
| Katalog bağ | Platform `Varyant` (ADR-0005). Eski “ürün.tedarikci == teklif.tedarikci” **geçersiz**. |
| Eşleştirme (quote) | **Zorunlu:** `eslestirme_durumu == onaylandi` ve `hedef_urun` tutarlı. `eslestirme_durumu` boş (`''`) veya dolu ama `onaylandi` değil → **“eşleştirme bekliyor”** → quote **yok** (genel hata). C sınıfı / elle istisna **yok**. |
| Faz 2 taslak teklifler | Migration ile gelen tekliflerde `eslestirme_durumu=''`: quote’a girmez. Operasyon: `teklif_eslestir_oner` → platform `eslestirmeyi_onayla` sonrası quote. Backfill otomatik `onaylandi` **yapılmaz**. |
| Durum makinesi | `TASLAK → ONAY_BEKLIYOR → YAYINDA ↔ PASIF`; yalnız servis + perm + audit. |
| `approve_teklif` | Platform + permission; dört göz (ADR-0006 O5). |
| Versiyon geçişi | Yayınlı teklifte fiyat/gram/model değişimi → **yeni satır/versiyon** `ONAY_BEKLIYOR` (veya taslak); **eski YAYINDA kalır**. Yenisi onaylanınca **tek `domain_atomic`**: yeni → YAYINDA, eski → PASIF. Fiyatsız boşluk yok. Quote/sipariş eski `teklif_id`/`versiyon` taşır. |
| Geçerlilik | `gecerlilik_baslangic` / `gecerlilik_bitis` YAYINDA için zorunlu; süresi dolmuş → quote yok. |
| Aktif çakışma | Aynı `tedarikci + varyant + tedarikci_kodu` (boş kodda `tedarikci+varyant`) için **bir** YAYINDA; partial unique + servis. Çoklu YAYINDA (farklı kod): alıcı seçmez — §5 ÖNERİ. |
| FK | `varyant` CASCADE → **PROTECT**; aktif teklif varken varyant silinemez. |
| Admin | Durum readonly; action → servis. |

### 2.1.1 Üç teklif fiyat modeli → quote

Mevcut `hesapla()` (`fiyat_hesaplama.py`): yalnız `metal_bedeli = gram × milyem × saf_birim_fiyat` + işçilik + marj + `tas_bedeli`. **GRAM_BIRIM / SABIT_PARCA bilmez.**

Orkestrasyon `PricingService` model seçer; saf çekirdek genişletilir veya model-spesifik saf fonksiyonlar eklenir (Django’suz kalır).

| Model | Quote girdileri | Kalemler (satır) | Yuvarlama |
|-------|-----------------|------------------|-----------|
| **METAL_BAZLI** | `teklif.gram` (veya varyant gram bandı içi), `ayar.milyem`, metal kuru `saf_birim_fiyat`, sözleşme işçilik/marj, teklif `iscilik_override` (varsa işçilik yerine), `teklif_tas_bedeli`, `varyant.ek_bedel` (TRY→quote PB) | `metal`, `iscilik`, `kanal_marj` (alıcı sözleşmesinden), `tas`, `ek_bedel`, `platform_servis` (konfig/sözleşme); **vergi satırı yok** | Ara adım yok; final satır + **vergisiz** `toplam` / `toplam_vergisiz` PB `quantize` (TRY: 0.01, HALF_UP) |
| **GRAM_BIRIM** | `teklif.gram`, `teklif.birim_fiyat`, `teklif.para_birimi` → dönüşüm; taş/ek_bedel/servis/alıcı marj aynı hat | `gram_birim` (= gram × birim, dönüşmüş), `tas`, `ek_bedel`, `platform_servis`, `kanal_marj` — **metal satırı yok**; **vergi satırı yok** | Aynı |
| **SABIT_PARCA** | `teklif.birim_fiyat` (+ PB); gram metal hesabına girmez; taş/ek/servis/marj | `sabit_parca`, `tas`, `ek_bedel`, `platform_servis`, `kanal_marj`; **vergi satırı yok** | Aynı |

Ortak: teklif YAYINDA + geçerli + eşleşme onaylı; kur stale değil; alıcı sözleşmesi çözülür (§2.4.1). Model alan zorunlulukları mevcut DB check + servis. **Faz 3’te KDV/vergi kalemi üretilmez** (§2.9).

### 2.2 K-007 sözleşme kalemi

| Madde | Karar |
|-------|--------|
| Çelişki | Aynı metal için genel (`ayar=NULL`) + ayara özel **birlikte olabilir**. |
| Unique (NULL-safe) | PostgreSQL’de `NULL` değerler unique’te varsayılan olarak birbirinden farklıdır. Tercih (Django 6.1): `UniqueConstraint(fields=[...], nulls_distinct=False)` — [docs](https://docs.djangoproject.com/en/6.1/ref/models/constraints/#nulls-distinct) (yalnız PostgreSQL). Alternatif: **iki (veya üç) partial unique**: (1) `ayar__isnull=False` → `(sozlesme, metal, ayar)`; (2) `ayar__isnull=True, metal__isnull=False` → `(sozlesme, metal)`; (3) gerekirse `metal__isnull=True, ayar__isnull=True` → `(sozlesme)` tek genel. Uygulama diliminde biri seçilir; test her iki NULL yolunu kapatır. |
| `clean()` | “Genel varken spesifik yasak” kalkar. |
| `cozumle` | Spesifik > genel; kanal > kanalsız; yüksek versiyon; eşit skor → hata, fiyat yok. |

### 2.3 K-008 sözleşme tarih çakışması

| Madde | Karar |
|-------|--------|
| Kural | Aynı `firma + kontrat_tipi + kanal_anahtarı` kapsamında AKTIF `daterange` çakışmaz. |
| NULL kanal | Ham `satis_kanali_id` exclusion’da **yetersiz** (`NULL` çakışma sayılmaz). İfade: `COALESCE(satis_kanali_id, 0)` (veya sentinel) + `daterange(baslangic, bitis, '[]')` + `&&`. Kanalsız iki AKTIF böylece engellenir. |
| Extension | `ExclusionConstraint` / `gist` için **`btree_gist`** gerekir. **DOĞRULANAMADI:** üretim hosting’te `CREATE EXTENSION btree_gist` yetkisi. Dilim 3.0’da doğrula; kurulamazsa: yayın servisinde `select_for_update` + aralık sorgusu (eşdeğer kural, test aynı). |
| Kanal vs kanalsız | Kanallı AKTIF o kanalda baskın; kanalsız diğer kanallara fallback. Matris testle sabitlenir. |
| İmmutability | AKTIF sonrası kalem/tarih değişmez → yeni versiyon. |
| Permission | `manage_sozlesme`. |

### 2.4 PricingService.quote() ve snapshot

**Giriş:** `alici_firma`, `satis_kanali`, `varyant`, isteğe bağlı `teklif_id`; yoksa platform teklif seçimi (§5 ÖNERİ).

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

### 2.5–2.7 K-011 / K-012 / K-019

Önceki ADR metni geçerli: taş rename; merkezi dönüşüm; stale kur sessiz fiyat yok; manuel kur audit. B-04/B-05 ÖNERİ §5.

### 2.8 Alıcı görünürlük

§5 B-02 ÖNERİ: varsayılan yalnız toplam; kırılım hukuk onaysız açılmaz; servis payı ayrı görünür satır olmaz (toplama gömülü / gizli_mi).

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
| 1 | Teklif alanları; CASCADE→PROTECT; eşleşme boş bırakılır (quote engeli) |
| 2 | K-007: `nulls_distinct=False` **veya** partial unique seti |
| 3 | K-008: `btree_gist` + exclusion (`COALESCE` kanal) **veya** servis kilidi; extension **DOĞRULANAMADI** ise servis yolu |
| 4 | Taş rename; PriceQuote + Line; quote UPDATE trigger |
| Reverse | Çakışmada dur; satır silme yok |

Staging envanteri dilim 3.0 (**DOĞRULANAMADI** bu tur).

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| TTL / kur tipi / servis payı sayısal değeri | Konfig; yoksa quote yok |
| Vergi | Faz 3’te yok; proforma (B-06 ertelendi — ürün sahibi kararı) |
| Eşleşme boş | Quote yok (otomatik onaylama yok) |

---

## 5. ÜRÜN SAHİBİ KARARI GEREKİR — ÖNERİ (onay gerekir)

| ID | Konu | ÖNERİ (onay gerekir) |
|----|------|----------------------|
| B-02 | Alıcıya görünen kalem | Varsayılan **yalnız toplam** (+ isteğe bağlı gram başı). Kırılım konfigle; **hukuk onayı olmadan kırılım açılmaz**. Servis payı **ayrı satır görünmez**. |
| B-03 | Quote TTL | **Kanal bazlı** (B2B≠B2C). TTL ≤ ilgili kur gözleminin max gecikmesi. Sayı finans belirler. Değer yoksa quote yok. |
| B-04 | Kur sağlayıcı | Aynı anda **tek aktif provider**; otomatik fallback yok. Manuel: neden + dört göz + audit. Max gecikme konfig. |
| B-05 | Kur tipi | Alıcı ve tedarikçi tarafı için **ayrı tipler** (ör. satış/alış); ikisi de snapshot’a. Seçim finansın. |
| — | Çoklu YAYINDA teklif | Alıcı seçmez (kör havuz). Sıra: `oncelik` ↓, sonra en düşük maliyet, sonra deterministik eşitlik bozucu (ör. `teklif.id`). Seçilen quote’a yazılır. |
| — | Servis payı kaynağı | ALICI sözleşme kalemi + eksikse global konfig; ikisi yoksa quote yok. |
| — | C sınıfı eşleşme istisnası | **Yok.** |
| B-06 | Vergi/KDV | **ERTELENDİ** (ürün sahibi kararı, 2026-11-08): Faz 3 proforma; KDV/vergi yok; mali müşavir şimdilik gerekmez. Vergi motoru ihtiyacında yeniden açılır. |

---

## 6. DIŞ DOĞRULAMA GEREKİR

| ID | Konu |
|----|------|
| B-01 | Platform hukuki rol |
| B-01 | **Gizli (faturaya yedirilen, görünmeyen) platform hizmet payı** — B2B/B2C şeffaflık ve fatura uyumu. **B-06 ertelemesi bunu kapatmaz** (proforma toplamı yine hizmet payını içerebilir; hukuk görüşü açık kalır). |
| — | Kur sağlayıcı lisans |
| — | TRY dışı yuvarlama muhasebesi |
| — | `btree_gist` üretim yetkisi (K-008) |

---

## 7. Kabul testleri (§12.3)

Önceki tablo + ekler:

| Ek | Test |
|----|------|
| — | Üç fiyat modeli için quote kalem/toplam (birim test + servis) |
| — | `eslestirme_durumu=''` → quote reddi |
| — | Versiyon: onay transaction’ında eski PASIF / yeni YAYINDA atomik |
| — | Quote UPDATE trigger reddi |
| — | K-007 NULL ayar tekilliği; K-008 iki kanalsız AKTIF reddi |

---

## 8. Dilimler

1. **3.0** Kabul + staging envanter + `btree_gist` kontrolü  
2. **3.1** Teklif yaşam döngüsü + versiyon swap + CASCADE→PROTECT + eşleşme kapısı  
3. **3.2** K-007/K-008  
4. **3.3** Kur politikası  
5. **3.4** Üç model hesap + CurrencyConversion  
6. **3.5** quote + trigger immutability  
7. **3.6** kör havuz + K-011  
8. **3.7** PriceLock arayüzü → Faz 4  

---

## 9. Non-goals

Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`, **KDV/vergi hesaplama ve resmi e-fatura/e-arşiv üretimi (Faz 3 dışı)**.

### Operasyon notu (ADR-0006 O3)

Üretimde fail audit **sidecar** ayrı DB bağlantısı açar; yoğun reddedilen istekte bağlantı sayısını izleyin. TestCase FK fallback üretim yolunu birebir kanıtlamaz; TransactionTestCase kalıcılık kanıtı zorunlu kalır.

---

## 10. Onay checklist

- [ ] Üç fiyat modeli + eşleşme boş=quote yok + versiyon swap  
- [ ] K-007/K-008 NULL-safe + btree_gist notu  
- [ ] ALICI vs TEDARIKCI sözleşme rolü  
- [ ] Quote trigger zorunlu  
- [ ] §5 ÖNERİler / §6 hukuk gizli hizmet (B-01)  
- [x] B-06 vergi/KDV: **ertelendi** (ürün sahibi kararı — proforma; mali müşavir şimdilik yok)  
- [ ] Durum: **Kabul edildi** (yalnız ürün sahibi)
