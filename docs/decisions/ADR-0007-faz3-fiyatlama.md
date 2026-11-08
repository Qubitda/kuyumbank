# ADR-0007 — Faz 3a: Tedarikçi teklifi yaşam döngüsü ve sözleşme kuralları

**Durum:** Taslak  
**Tarih:** 2026-11-08 (revizyon: Faz 3a/3b bölünmesi)  
**Bağlı:** ADR-0005, ADR-0006 (Kabul); kanonik rapor K-006…K-008; §9.3 (teklif); §12.3 (teklif/sözleşme maddeleri)  
**Etki analizi:** [`docs/architecture/faz3-etki-analizi.md`](../architecture/faz3-etki-analizi.md)  
**Onay:** Ürün sahibi onayı bekleniyor (agent Kabul işaretlemez)

**Kapsam notu:** Faz 3b kararları [`ADR-0008-faz3b-kur-fiyatlama-quote.md`](ADR-0008-faz3b-kur-fiyatlama-quote.md) içindedir; **3.3+ kodu ADR-0008 Kabul olmadan başlamaz.**

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/) (`UniqueConstraint.nulls_distinct`).

---

## 1. Bağlam

Faz 2 katalog ownership’i ayırdı. Teklif durum servisi yok; K-007/K-008 (NULL-safe unique/exclusion) eksik. ADR-0006: teklif `durum` admin salt okunur; `approve_teklif` / `manage_sozlesme` Faz 3’e ertelenmişti. Bu ADR yalnız **dilim 3.0–3.2** (teklif yaşam döngüsü + sözleşme kuralları) içindir.

---

## 2. Kararlar (bağlayıcı taslak)

### 2.1 Tedarikçi teklifi yaşam döngüsü

| Madde | Karar |
|-------|--------|
| Sahiplik | Teklif `tedarikci_id == kullanici.firma_id`; firma `tedarikci_mi=True`. Client `tedarikci_id` güvenilmez. |
| Katalog bağ | Platform `Varyant` (ADR-0005). Eski “ürün.tedarikci == teklif.tedarikci” **geçersiz**. |
| Eşleştirme kapısı | **Zorunlu:** `eslestirme_durumu == onaylandi` ve `hedef_urun` tutarlı. `eslestirme_durumu` boş (`''`) veya dolu ama `onaylandi` değil → **“eşleştirme bekliyor”** → fiyat motorunda / quote’ta **kullanılmaz** (genel hata). C sınıfı / elle istisna **yok**. (Quote üretimi ADR-0008.) |
| Faz 2 taslak teklifler | Migration ile gelen tekliflerde `eslestirme_durumu=''`: eşleşme kapısından geçmez. Operasyon: `teklif_eslestir_oner` → platform `eslestirmeyi_onayla`. Backfill otomatik `onaylandi` **yapılmaz**. |
| Durum makinesi | `TASLAK → ONAY_BEKLIYOR → YAYINDA ↔ PASIF`; yalnız servis + perm + audit. |
| `approve_teklif` | Platform + permission; dört göz (ADR-0006 O5). |
| Versiyon geçişi | Yayınlı teklifte fiyat/gram/model değişimi → **yeni satır/versiyon** `ONAY_BEKLIYOR` (veya taslak); **eski YAYINDA kalır**. Yenisi onaylanınca **tek `domain_atomic`**: yeni → YAYINDA, eski → PASIF. Fiyatsız boşluk yok. İleriye dönük: quote/sipariş eski `teklif_id`/`versiyon` taşır — ADR-0008. |
| Geçerlilik | `gecerlilik_baslangic` / `gecerlilik_bitis` YAYINDA için zorunlu; süresi dolmuş → fiyat motorunda kullanılmaz (quote yok — ADR-0008). |
| Aktif çakışma | Aynı `tedarikci + varyant + tedarikci_kodu` (boş kodda `tedarikci+varyant`) için **bir** YAYINDA; partial unique + servis. Çoklu YAYINDA (farklı kod): alıcı seçmez — §5 ÖNERİ. |
| FK | `varyant` CASCADE → **PROTECT**; aktif teklif varken varyant silinemez. |
| Admin | Durum readonly; action → servis. |

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

Staging envanteri dilim 3.0 (**DOĞRULANAMADI** bu tur). Adım 4 (PriceQuote / trigger) → ADR-0008.

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| Eşleşme boş | Fiyat motorunda kullanılmaz; otomatik onaylama yok |
| §2.9 Vergi / TTL / kur | ADR-0008 |

---

## 5. ÜRÜN SAHİBİ KARARI GEREKİR — ÖNERİ (onay gerekir)

| ID | Konu | ÖNERİ (onay gerekir) |
|----|------|----------------------|
| — | Çoklu YAYINDA teklif | Alıcı seçmez (kör havuz). Sıra: `oncelik` ↓, sonra en düşük maliyet, sonra deterministik eşitlik bozucu (ör. `teklif.id`). Seçilen teklif ADR-0008 quote’a yazılır. |

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
| — | `eslestirme_durumu=''` → fiyat motoru / quote reddi (kapı; quote uygulaması ADR-0008) |
| — | Versiyon: onay transaction’ında eski PASIF / yeni YAYINDA atomik |
| — | K-007 NULL ayar tekilliği; K-008 iki kanalsız AKTIF reddi |
| — | Teklif sahiplik / durum makinesi / CASCADE→PROTECT |

---

## 8. Dilimler

1. **3.0** Kabul + staging envanter + `btree_gist` kontrolü  
2. **3.1** Teklif yaşam döngüsü + versiyon swap + CASCADE→PROTECT + eşleşme kapısı  
3. **3.2** K-007/K-008  

Dilim **3.3–3.7** → ADR-0008.

---

## 9. Non-goals

Kur politikası, üç model quote hesabı, `PriceQuote` / trigger, alıcı görünürlük, KDV/vergi, e-fatura (ADR-0008 / Faz 4+). Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`.

### Operasyon notu (ADR-0006 O3)

Üretimde fail audit **sidecar** ayrı DB bağlantısı açar; yoğun reddedilen istekte bağlantı sayısını izleyin. TestCase FK fallback üretim yolunu birebir kanıtlamaz; TransactionTestCase kalıcılık kanıtı zorunlu kalır.

---

## 10. Onay checklist

- [ ] Eşleşme kapısı (boş = kullanılmaz) + versiyon swap atomik  
- [ ] K-007/K-008 NULL-safe + btree_gist notu  
- [ ] CASCADE→PROTECT + teklif durum servisi kapsamı  
- [ ] Durum: **Kabul edildi** (yalnız ürün sahibi)
