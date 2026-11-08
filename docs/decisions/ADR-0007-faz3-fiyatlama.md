# ADR-0007 — Faz 3a: Tedarikçi teklifi yaşam döngüsü ve sözleşme kuralları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08 (revizyon: Faz 3a/3b bölünmesi)  
**Bağlı:** ADR-0005, ADR-0006 (Kabul); kanonik rapor K-006…K-008; §9.3 (teklif); §12.3 (teklif/sözleşme maddeleri)  
**Etki analizi:** [`docs/architecture/faz3-etki-analizi.md`](../architecture/faz3-etki-analizi.md)  
**Onay:** Ürün sahibi, 2026-11-08

**Kapsam notu:** Faz 3b kararları [`ADR-0008-faz3b-kur-fiyatlama-quote.md`](ADR-0008-faz3b-kur-fiyatlama-quote.md) içindedir; **3.3+ kodu ADR-0008 Kabul olmadan başlamaz.**  
**Uygulama:** Dilim **3.1** uygulandı — [`faz3-1-uygulama-raporu.md`](../architecture/faz3-1-uygulama-raporu.md). Dilim **3.2** (K-007/K-008) açık.

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/) (`UniqueConstraint.nulls_distinct`).

---

## 1. Bağlam

Faz 2 katalog ownership’i ayırdı. *(Analiz/Kabul anı:)* teklif durum servisi yoktu; K-007/K-008 (NULL-safe unique/exclusion) eksik. ADR-0006: teklif `durum` admin salt okunur; `approve_teklif` / `manage_sozlesme` Faz 3’e ertelenmişti. Bu ADR yalnız **dilim 3.0–3.2** (teklif yaşam döngüsü + sözleşme kuralları) içindir.

---

## 2. Kararlar (bağlayıcı)

### 2.1 Tedarikçi teklifi yaşam döngüsü

| Madde | Karar |
|-------|--------|
| Sahiplik | Teklif `tedarikci_id == kullanici.firma_id`; firma `tedarikci_mi=True`. Client `tedarikci_id` güvenilmez. |
| Katalog bağ | Platform `Varyant` (ADR-0005). Eski “ürün.tedarikci == teklif.tedarikci” **geçersiz**. |
| Eşleştirme kapısı | **Zorunlu:** `eslestirme_durumu == onaylandi` ve `hedef_urun` tutarlı. `eslestirme_durumu` boş (`''`) veya dolu ama `onaylandi` değil → **“eşleştirme bekliyor”** → fiyat motorunda / quote’ta **kullanılmaz** (genel hata). C sınıfı / elle istisna **yok**. (Quote üretimi ADR-0008.) |
| Faz 2 taslak teklifler | Migration ile gelen tekliflerde `eslestirme_durumu=''`: eşleşme kapısından geçmez. Operasyon: `teklif_eslestir_oner` → platform `eslestirmeyi_onayla`. Backfill otomatik `onaylandi` **yapılmaz**. |
| Durum makinesi | `TASLAK → ONAY_BEKLIYOR → YAYINDA ↔ PASIF`; yalnız servis + perm + audit. |
| `approve_teklif` | Platform + permission; dört göz (ADR-0006 O5). |
| Versiyon geçişi | Yayınlı teklifte fiyat/gram/model değişimi → **yeni satır/versiyon** `ONAY_BEKLIYOR` (veya taslak); onaylanana kadar **eski YAYINDA kalır**. Yenisi onaylanınca **tek `domain_atomic`**: önce eski → PASIF, sonra yeni → YAYINDA (`select_for_update`). Fiyatsız boşluk yok. İleriye dönük: quote/sipariş eski `teklif_id`/`versiyon` taşır — ADR-0008. |
| Geçerlilik | `gecerlilik_baslangic` / `gecerlilik_bitis` YAYINDA için zorunlu; süresi dolmuş → fiyat motorunda kullanılmaz (quote yok — ADR-0008). |
| Aktif çakışma | Aynı `tedarikci + varyant + tedarikci_kodu` (boş kodda `tedarikci+varyant`) için **bir** YAYINDA; partial unique + servis. Çoklu YAYINDA (farklı kod) seçim sırası → ADR-0008 §5. |
| FK | `varyant` CASCADE → **PROTECT**; aktif teklif varken varyant silinemez. |
| Admin | Durum readonly; action → servis. |

#### Netleştirme (anlam değişmez)

1. **Versiyon swap sırası:** Önce eski teklif → PASIF, sonra yeni teklif → YAYINDA; tek `domain_atomic` içinde; ilgili satırlar `select_for_update` ile kilitlenir. Gerekçe: “aktif çakışma” partial unique’i ertelenmemiş kısıttır; sıra ters olursa ara ifade kısıtı ihlal eder.
2. **Eşleştirme kapısı (3a):** Yalnız saf bir uygunluk koşulu (selector / predicate); quote çağrısı yok. Quote tarafındaki gerçek reddi testi ADR-0008’e aittir; §7’deki ilgili test 3a’da **predicate** testidir.
3. **Versiyon alanları:** `versiyon` ve önceki teklife bağ ADR’de adlandırılmamıştır; uygulama sırasında geri dönüşü kolay en küçük çözüm seçilir ve uygulama raporunda **VARSAYIM** olarak listelenir (alan adı uydurma yok).

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
| Extension | `ExclusionConstraint` / `gist` için **`btree_gist`** gerekir. Yerel: `btree_gist` 1.8 **DOĞRULANDI** (CREATE EXTENSION OK). **DOĞRULANAMADI:** üretim hosting yetkisi (hosting henüz yok). Kurulamazsa: yayın servisinde `select_for_update` + aralık sorgusu (eşdeğer kural, test aynı). |
| Kanal vs kanalsız | Kanallı AKTIF o kanalda baskın; kanalsız diğer kanallara fallback. Matris testle sabitlenir. |
| İmmutability | AKTIF sonrası kalem/tarih değişmez → yeni versiyon. |
| Permission | `manage_sozlesme`. |

### 2.9 Vergi

§2.9 → ADR-0008 §2.9 (kanonik rapor Sapma kaydı bu atıfı kullanır).

---

## 3. Migration ve veri taşıma

| Adım | İçerik |
|------|--------|
| 1 | Teklif alanları; CASCADE→PROTECT; eşleşme boş bırakılır (kapı; quote engeli ADR-0008) |
| 2 | K-007: `nulls_distinct=False` **veya** partial unique seti |
| 3 | K-008: `btree_gist` + exclusion (`COALESCE` kanal) **veya** servis kilidi; extension **DOĞRULANAMADI** ise servis yolu |
| Reverse | Çakışmada dur; satır silme yok |

Dilim 3.0: staging yok (uzak DB yok, yalnız yerel PostgreSQL); yerel `btree_gist` 1.8 doğrulandı (CREATE EXTENSION OK); üretim yetkisi **DOĞRULANAMADI** — hosting henüz yok. Adım 4 (PriceQuote / trigger) → ADR-0008.

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| Eşleşme boş | Fiyat motorunda kullanılmaz; otomatik onaylama yok |
| §2.9 Vergi / TTL / kur | ADR-0008 |

---

## 5. ÜRÜN SAHİBİ KARARI GEREKİR — ÖNERİ (onay gerekir)

Çoklu YAYINDA teklif seçim sırası → ADR-0008 §5 (3b; quote seçimi).

B-02…B-06 ve servis payı → ADR-0008 §5.

---

## 6. DIŞ DOĞRULAMA GEREKİR

| ID | Konu |
|----|------|
| — | `btree_gist` üretim yetkisi (K-008) |

B-01 (hukuk / gizli hizmet payı) ve diğer dış doğrulamalar → ADR-0008 §6.

---

## 7. Kabul testleri (§12.3 teklif/sözleşme)

| Ek | Test |
|----|------|
| — | `eslestirme_durumu=''` → predicate reddi (kapı; quote uygulaması ADR-0008) |
| — | Versiyon: onay transaction’ında önce eski PASIF, sonra yeni YAYINDA (`select_for_update`) |
| — | K-007 NULL ayar tekilliği; K-008 iki kanalsız AKTIF reddi |
| — | Teklif sahiplik / durum makinesi / CASCADE→PROTECT |

---

## 8. Dilimler

1. **3.0** Kabul; staging yok (uzak DB yok); yerel `btree_gist` 1.8 doğrulandı; üretim yetkisi DOĞRULANAMADI  
2. **3.1** Teklif yaşam döngüsü + versiyon swap + CASCADE→PROTECT + eşleşme predicate — **uygulandı**  
3. **3.2** K-007/K-008 — **uygulandı**  

Dilim **3.3–3.7** → ADR-0008.

---

## 9. Non-goals

Kur politikası, üç model quote hesabı, `PriceQuote` / trigger, alıcı görünürlük, KDV/vergi, e-fatura (ADR-0008 / Faz 4+). Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`.

### Operasyon notu (ADR-0006 O3)

Üretimde fail audit **sidecar** ayrı DB bağlantısı açar; yoğun reddedilen istekte bağlantı sayısını izleyin. TestCase FK fallback üretim yolunu birebir kanıtlamaz; TransactionTestCase kalıcılık kanıtı zorunlu kalır.

---

## 10. Onay checklist

- [x] Eşleşme kapısı (boş = kullanılmaz) + versiyon swap atomik *(dilim 3.1)*  
- [x] K-007/K-008 NULL-safe + btree_gist notu *(dilim 3.2)*  
- [x] CASCADE→PROTECT + teklif durum servisi kapsamı *(dilim 3.1)*  
- [x] Durum: **Kabul edildi** (yalnız ürün sahibi)
