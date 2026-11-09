# ADR-0005 — Katalog platform ownership

> **Arşiv notu:** Bu ADR metni 2026-11-09 tarihinde `KUYUMBANK_MASTER.md` §6.3 arşivinden taşındı; içerik değiştirilmedi. Artık var olmayan dosyalara giden bağlantılar düz metne çevrildi. Güncel karar durumu: [README](README.md).

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onay:** Ürün sahibi — 2026-11-08 (K1–K6 bağlayıcı)  
**Bağlı:** K-006, K-010, K-011, K-014 (kapsam dışı), K-015, K-016; `faz2-etki-analizi.md`; Faz 1.1 audit kalıbı  
**Önkoşul:** Faz 1.1 GO

---

## 1. Bağlam

Mevcut modelde `Urun.tedarikci` katalog ürününü tek tedarikçiye bağlar. Kör havuz ve çoklu tedarikçi teklifi (rapor §5.2 / K-006) bunu reddeder. Faz 1 K-004 sahipliği `urun.tedarikci_id` üzerinden doğrulanıyordu; bu ADR ile sahiplik yeniden tanımlanır.

---

## 2. Karar ve gerekçe (K1–K6)

| No | Karar | Gerekçe |
|----|-------|---------|
| **K1** | Kimlik sınıfları: **A**=seri/sertifikalı (sertifika no veya parça no), **B**=markalı/model kodlu (marka+model, varsa GTIN), **C**=jenerik kalıp. İlk sürümde A ve B otomatik kesin eşleşme; C elle onaylı. | Farklı tekilleştirme güveni; yanlış birleştirmeyi sınırlar. |
| **K2** | C sınıfında “aynı ürün” = platform standart modeli (spec). Kimlik: kategori/tip, metal, ayar, kalıp ailesi, ölçü sınıfı, içi dolu/boş, taş var/yok, yüzey/renk. Kimlik **değil:** tedarikçi, üretici markası, tedarikçi SKU. **Ayar sert kimlik** (14K ≠ 18K). | Kör havuz + kalıp ailesi birleşimi; ayar karışması engeli. |
| **K3** | Gramaj kimlik değil; **varyant boyutu** (gram bandı parametreli). Teklifler toplam fiyatla değil **gram-başı işçilik + milyem** ile normalize edilip karşılaştırılır. | Aynı kalıbın farklı gramları ayrı varyant; adil teklif kıyası. |
| **K4** | Görsel eşdeğerlik: B2B’de fotoğraf **temsili**, ürün “belirtilen özelliklerde”; B2C’de sipariş anında **tek teklife kilitleme** + QC’de kalıp uyumu. Kalite toleransları (gram, ölçü, kalıp) **konfigürasyon parametresi**. Hukuki tolerans doğrulaması → **DIŞ DOĞRULAMA GEREKİR**. | Operasyonel esneklik; hukuki metin ajan tarafından uydurulmaz. |
| **K5** | Eşleştirme: tedarikçi teklif/nitelik **önerir**; karar yalnız `platform_catalog` (+ `approve_urun` / eşleştirme permission). **Şüphede ayır.** Her eşleştirme/ayırma/birleştirme **audit’li ve geri alınabilir**. | Platform kontrolü; yanlış birleştirme geri alınabilir. |
| **K6** | Katalog ürünü **platforma** aittir. `Urun.tedarikci` **kaldırılır**; yerine denetim amaçlı `olusturan_firma` (alıcıya hiçbir yüzeyde gösterilmez). Tedarikçi, onaydan önce yalnız kendi önerdiği **taslağı** düzenler (K-004 yeni tanım); onaydan sonra ürün işlemi yok, yalnız `TedarikciTeklif` / SupplierOffer. | K-006; kör havuz; çoklu teklif. |

### Kabul edilmeyen alternatifler (kısa)

| Alternatif | Neden reddedildi |
|------------|------------------|
| Katalogda `Urun.tedarikci` kalsın (yeniden adlandırılmış “ana kaynak”) | Kör havuz sızıntı riski; çoklu teklif modeli bulanık kalır (K6). |
| Tedarikçi doğrudan onaylı `Urun` yazar | Platform sahipliği ve eşleştirme denetimi zayıf (K5/K6). |
| C sınıfında otomatik birleştirme (ilk sürüm) | Yanlış birleştirme maliyeti yüksek; elle onay zorunlu (K1). |
| Gramajı ürün kimliğine dahil etmek | Aynı kalıp farklı gram = ayrı varyant olmalı (K3). |
| B2C’de “temsili fotoğrafla rastgele teklif” | Sipariş anında tek teklif kilidi + QC şart (K4). |

---

## 3. Veri modeli taslağı (alan düzeyi, kodsuz)

### 3.1 `Urun`

| Alan | Not |
|------|-----|
| `tedarikci` | **Kaldırılır** (migration + veri taşıma). |
| `tedarikci_urun_kodu` | Teklife / öneriye taşınır; üründen kaldırılır veya boş bırakılıp kullanılmaz. |
| `olusturan_firma` | FK `Firma`, PROTECT; denetim; alıcı API/admin listelerinde yok. |
| `kimlik_sinifi` | `A` / `B` / `C` |
| `kimlik_anahtari` | Normalize string; sınıf A/B’de unique (aktif kayıtlar); C’de platform spec anahtarı. |
| Mevcut | `platform_kodu`, onay/yayın, kategori, ayar, SEO, vitrin alanları kalır. |

**Çakışma:** `onay_servisi` K-004 `urun.tedarikci_id` → `olusturan_firma_id` + durum=taslak/reddedildi.  
**Etki analizi:** `faz2-etki-analizi.md` B1 satırları `urun.py`, `onay_servisi`, admin, testler.

### 3.2 `Varyant`

| Alan | Not |
|------|-----|
| `gram` | Mevcut; kimlik değil. |
| `gram_bandi_min` / `gram_bandi_max` | Parametreli bant (opsiyonel ilk dilimde settings sabiti + alan). Teklif gramı bant dışıysa **ayrı varyanta** düşer (K3). |
| `tedarikci_sku` | Teklife taşınır; varyantta kaldırılır veya kullanılmaz. |
| `stok` | Otomatik `TedarikciTeklif.stok_adet` ile **toplanmaz** (§13.2). |

### 3.3 `TedarikciTeklif` (SupplierOffer)

| Alan | Not |
|------|-----|
| Mevcut | `varyant`, `tedarikci`, fiyat/stok/termin/durum kalır. |
| `eslestirme_durumu` | `onerildi` / `onaylandi` / `reddedildi` / `ayrildi` |
| `eslestirme_guveni` | `kesin` / `manuel` / `cikarim` |
| `eslestiren_kullanici` | FK user (platform) |
| `eslestirme_kaniti` | JSON (sertifika no, model kodu, spec hash, not) |
| `esdegerlik_seviyesi` | `birebir` / `esdeger` |

K-006: teklif `tedarikci_id == kullanici.firma_id`; başka firmanın varyantına yazma IDOR engeli serviste.

### 3.4 Eşleştirme geçmişi / audit

- Her `eslestir` / `onayla` / `reddet` / `birlestir` / `ayir` → `AuditOlay` (Faz 1.1 kalıbı).
- İsteğe bağlı `EslestirmeOlay` tablosu (entity snapshot + reverse pointer); ilk sürümde `AuditOlay.detail` yeterli olabilir — servis sözleşmesi geri alınabilirliği garanti eder.

---

## 4. Servis sözleşmeleri (imza + kurallar, kodsuz)

Ortak kurallar: `transaction.atomic` ürün/teklif yazımıyla; **fail audit atomic dışı** (Faz 1.1); permission her çağrıda; idempotency: aynı girdi + aynı hedef durumda no-op + tek success audit.

```
teklif_eslestir_oner(teklif, kullanici, hedef_urun|None, kanit) -> teklif
  - require: manage_own_teklif + teklif.tedarikci_id == kullanici.firma_id
  - A/B: otomatik aday + guven=kesin öneri; C: guven=manuel, durum=onerildi
  - ayar/kimlik çelişkisi → ValidationError + fail audit
  - şüphe → ayır / önerme

eslestirmeyi_onayla(teklif, kullanici) -> teklif
  - require: platform firma + approve_urun (veya eşleştirme perm)
  - durum onerildi → onaylandi; audit success

eslestirmeyi_reddet(teklif, kullanici, neden) -> teklif
  - platform + neden zorunlu; audit

urunleri_birlestir(kaynak_urun, hedef_urun, kullanici) -> hedef
  - yalnız platform_catalog; aynı kimlik_sinifi + uyumlu anahtar
  - 14K/18K birleşmez; audit + geri alınabilir işaret

urunu_ayir(urun_veya_teklif, kullanici, neden) -> yeni_urun|teklif
  - platform; şüphe veya yanlış birleştirme geri alma; audit
```

---

## 5. K-004 yeni karşılığı ve tenant scope

### K-004 (Faz 2)

1. **Taslak / reddedildi:** `onaya_gonder` yalnız `urun.olusturan_firma_id == kullanici.firma_id` + `submit_urun`.
2. **Onaylı ürün:** tedarikçi ürün alanını değiştirmez / onaya göndermez; yalnız kendi `TedarikciTeklif` kayıtları.
3. Platform `approve_urun` / `publish_urun` katalogda; eşleştirme onayı platform_catalog.

### `katalog_tenant` (tek nokta)

| Önce (Faz 1.1) | Sonra (Faz 2) |
|----------------|---------------|
| `scope_urun_queryset` → `tedarikci_id=firma` | Platform `view_all_tenants`: tüm katalog. Tedarikçi: **onay öncesi** `olusturan_firma_id=firma` taslaklar; onaylı katalog **okuma** politikası ayrı (teklif ekleme için varyant listesi platform yayınına bağlı — detay uygulama PR’ında). |
| İlişkili `urun__tedarikci_id` | `urun__olusturan_firma_id` (taslak scope) |
| Teklif scope | Yeni/existing `scope_teklif_queryset`: `tedarikci_id=firma` (zorunlu) |

Alıcı yüzeylerinde `olusturan_firma` / tedarikçi kimliği **yok** (`user_may_see_tedarikci_identity` false).

---

## 6. Veri taşıma planı

1. **Kapı sorguları (migrate öncesi):**  
   - `Urun` sayısı, `tedarikci` null/dolu, varyant/teklif sayıları  
   - `Varyant.stok` vs eşleşen `TedarikciTeklif.stok_adet` farkları (otomatik toplanmaz)  
   - `kimlik_anahtari` çakışma adayları  
2. Her `Urun` için: `olusturan_firma = eski tedarikci`; taslak `TedarikciTeklif` (veya eşdeğer) oluşturulur — stok kopyalanmaz otomatik.  
3. `tedarikci` / `tedarikci_urun_kodu` kaldırılır (çok adımlı migration: ekle → doldur → NOT NULL → kaldır).  
4. **Geri dönüş:** migration reverse + yedek; production migrate ayrı onay.  
5. Yerel envanter (2026-11-08): Urun=0 → taşıma riski düşük (**DOĞRULANDI** etki analizinde). Staging/üretim: **DOĞRULANAMADI**.

---

## 7. Faz 2 kapsamı ve iş kartı sırası

| Sıra | Kart | Kapsam |
|------|------|--------|
| 1 | **K-015** | SEO sabit marka → settings/parametre; `save()` içinde “Örnek Kuyumculuk” kalkar; güvenli teknik fallback |
| 2 | **K-016** | Kategori alt ağaç derinliği + `kategori_tasi` servisi; `yeni_üst_derinlik + alt_ağaç_yüksekliği <= 3` |
| 3 | **K-006 / ownership** | Bu ADR model + K-004 + selector + teklif eşleştirme iskeleti |
| — | **K-014 medya** | Object storage kararı yok → **kapsam DIŞI** |

Non-goals: stok üçlüsü (Faz 4), PriceQuote (Faz 3), DRF (Faz 7), onaysız WIP refactor.

---

## 8. Kabul testleri (§12.2 / §12.3 eşlemesi)

| Test | Rapor |
|------|-------|
| Tenant/IDOR: tedarikçi başka firmanın taslağını güncelleyemez | §12.2.2, güvenlik |
| Tedarikçi yalnız kendi taslağını onaya gönderir (yeni K-004) | §12.2.2 |
| Yanlış birleştirmeyi geri alma (`urunu_ayir`) | K5 |
| Aynı sınıf-A sertifika no ile çift kayıt engeli | K1 |
| Ayar farklı ürünler eşleşemez (14K≠18K) | K2 |
| Gram bandı dışı teklif ayrı varyanta düşer | K3 |
| Teklif yalnız kendi tedarikçisi | §12.3.1–2 |
| Alıcı yüzeyinde tedarikçi/`olusturan_firma` yok | §12.3.14 |
| Kategori derinlik + taşıma | §12.2.9 |
| SEO’da sabit örnek marka yok | K-015 |

---

## 9. ÜRÜN SAHİBİ KARARI GEREKİR (açık kalanlar)

| Madde | Not |
|-------|-----|
| Tekilleştirme **güven eşiği** (çıkarım skoru → otomatik mi?) | İlk sürüm: A/B kesin, C elle; skor eşiği sonraya |
| Onaylı katalogda tedarikçinin **varyant görünürlük** kapsamı (tüm aktif mi, yalnız teklif verdiği mi?) | Uygulama PR’ında netleştirilir; şüphede daralt |
| `EslestirmeOlay` ayrı tablo mu, yalnız `AuditOlay` mı? | İlk sürüm AuditOlay yeterli varsayılanı |

---

## 10. DIŞ DOĞRULAMA GEREKİR

| Madde | Not |
|-------|-----|
| Hukuki **tolerans** metni (gram/ölçü/kalıp sapması) | Avukat / regülasyon |
| B2C **eşdeğerlik / temsili görsel** tüketici metni | Hukuk + ürün |
| Object storage / CDN seçimi (K-014) | Altyapı; medya bu ADR kapsamı dışı |

---

## 11. Onay checklist

- [x] K1–K6 bağlayıcı kabul  
- [x] `Urun.tedarikci` kaldır + `olusturan_firma`  
- [x] K-004 yeni sahiplik yazıldı  
- [x] Medya (K-014) kapsam dışı  
- [x] Durum: **Kabul edildi**
