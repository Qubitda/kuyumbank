# Kuyumbank — Veri sözlüğü

> **Otomatik üretilir** (`python scripts/docs_sync.py`). Elle düzenlemeyin; açıklama için modeldeki `help_text` / docstring güncellenir.
> Kaynak: Django model meta. Migration / DB şema için kod/DB kazanır.

## `firmalar`

### AuditOlay

Kritik işlem denetim kaydı — silinmez, güncellenmez (AUD-001).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `actor` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `actor_firma` | ForeignKey | firmalar.Firma (SET_NULL) | null |  |
| `action` | CharField | max 64 |  |  |
| `entity_type` | CharField | max 64 | blank |  |
| `entity_id` | CharField | max 64 | blank |  |
| `success` | BooleanField |  |  |  |
| `detail` | JSONField |  | blank |  |
| `reason` | CharField | max 255 | blank |  |
| `ip_address` | GenericIPAddressField |  | null |  |
| `changes` | JSONField |  | blank |  |
| `created_at` | DateTimeField |  | blank |  |

### Firma

Firma(id, ad, unvan, firma_kodu, vergi_no, vergi_dairesi, telefon, eposta, alici_mi, tedarikci_mi, platform_mu, onay_durumu, aktif, olusturma_zamani, guncelleme_zamani)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `ad` | CharField | max 150 |  |  |
| `unvan` | CharField | max 200 | blank |  |
| `firma_kodu` | CharField | max 32 | benzersiz | Değişmez iş anahtarı. Platform için PLATFORM. |
| `vergi_no` | CharField | max 11 | null, benzersiz |  |
| `vergi_dairesi` | CharField | max 80 | blank |  |
| `telefon` | CharField | max 20 | blank |  |
| `eposta` | CharField | max 254 | blank |  |
| `alici_mi` | BooleanField |  |  |  |
| `tedarikci_mi` | BooleanField |  |  |  |
| `platform_mu` | BooleanField |  |  |  |
| `onay_durumu` | CharField | max 10, choices |  |  |
| `aktif` | BooleanField |  |  |  |
| `olusturma_zamani` | DateTimeField |  | blank |  |
| `guncelleme_zamani` | DateTimeField |  | blank |  |

**Kısıtlar:** `tek_platform_firmasi` (UniqueConstraint)

### FirmaAdresi

FirmaAdresi(id, firma, tip, il, ilce, adres, varsayilan)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (CASCADE) |  |  |
| `tip` | CharField | max 10, choices |  |  |
| `il` | CharField | max 50 |  |  |
| `ilce` | CharField | max 50 | blank |  |
| `adres` | TextField |  |  |  |
| `varsayilan` | BooleanField |  |  |  |

### FirmaBankaHesabi

FirmaBankaHesabi(id, firma, banka_adi, iban, para_birimi, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (CASCADE) |  |  |
| `banka_adi` | CharField | max 80 |  |  |
| `iban` | CharField | max 34 |  |  |
| `para_birimi` | CharField | max 10 |  |  |
| `aktif` | BooleanField |  |  |  |

### HarcamaLimiti

HarcamaLimiti(id, firma, org_birimi, donem, tutar, para_birimi, aktif, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `org_birimi` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null | Null = firma geneli. |
| `donem` | CharField | max 16, choices |  |  |
| `tutar` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `aktif` | BooleanField |  |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `harcamalimiti_tutar_pozitif` (CheckConstraint); `harcamalimiti_donem_gecerli` (CheckConstraint)

### Kullanici

Sistem kullanıcısı: tek firma + tek iş rolü (ADR-0003).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `password` | CharField | max 128 |  |  |
| `last_login` | DateTimeField |  | null |  |
| `is_superuser` | BooleanField |  |  | Bu kullanıcıya ayrı ayrı izin atamadan tüm izinlerin verilip verilmeyeceğini belirler. |
| `username` | CharField | max 150 | benzersiz | Zorunlu. 150 karakter ya da daha az olmalı. Sadece harfler, rakamlar ve @/./+/-/_ karakterleri ku... |
| `first_name` | CharField | max 150 | blank |  |
| `last_name` | CharField | max 150 | blank |  |
| `email` | CharField | max 254 | blank |  |
| `is_staff` | BooleanField |  |  | Kullanıcının bu yönetici sitesine oturum açıp açamayacağını belirler. |
| `is_active` | BooleanField |  |  | Bu kullanıcının etkin olarak işlem görüp görmediğini belirler. Hesapları silmek yerine bunun işar... |
| `date_joined` | DateTimeField |  |  |  |
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `rol` | CharField | max 30, choices |  |  |
| `groups` | ManyToManyField | auth.Group | blank | Bu kullanıcının ait olduğu gruplar. Bir kullanıcı kendi gruplarının her birine verilmiş olan tüm ... |
| `user_permissions` | ManyToManyField | auth.Permission | blank | Bu kullanıcı için belirli izinler. |

### OnayTalebi

OnayTalebi(id, firma, org_birimi, order, durum, tutar, para_birimi, gerekce, olusturan, karar_veren, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `org_birimi` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null |  |
| `order` | ForeignKey | siparis.Order (PROTECT) | null |  |
| `durum` | CharField | max 16, choices |  |  |
| `tutar` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `gerekce` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `karar_veren` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `onaytalebi_durum_gecerli` (CheckConstraint); `onaytalebi_tutar_pozitif` (CheckConstraint)

### OrgBirimi

OrgBirimi(id, firma, parent, kod, ad, aktif, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Tenant sınırı; org firma dışına taşamaz (OH-1). |
| `parent` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null |  |
| `kod` | CharField | max 32 |  |  |
| `ad` | CharField | max 128 |  |  |
| `aktif` | BooleanField |  |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `orgbirimi_firma_kod_uniq` (UniqueConstraint)

### OrgUyeligi

OrgUyeligi(id, kullanici, org_birimi, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kullanici` | ForeignKey | firmalar.Kullanici (CASCADE) |  |  |
| `org_birimi` | ForeignKey | firmalar.OrgBirimi (CASCADE) |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `orguyeligi_kullanici_org_uniq` (UniqueConstraint)

### OutboxMessage

OutboxMessage(id, event_type, payload, durum, attempts, last_error, created_at, processed_at)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `event_type` | CharField | max 64 |  |  |
| `payload` | JSONField |  | blank |  |
| `durum` | CharField | max 16, choices |  |  |
| `attempts` | PositiveIntegerField |  |  |  |
| `last_error` | CharField | max 255 | blank |  |
| `created_at` | DateTimeField |  | blank |  |
| `processed_at` | DateTimeField |  | null |  |

**Kısıtlar:** `outbox_durum_gecerli` (CheckConstraint)

### WebhookDelivery

WebhookDelivery(id, outbox, endpoint_key, idempotency_key, durum, attempts, last_error, response_code, created_at, delivered_at)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `outbox` | ForeignKey | firmalar.OutboxMessage (CASCADE) |  |  |
| `endpoint_key` | CharField | max 64 |  | Hedef anahtar (fake/erp/crm); URL/secret yok. |
| `idempotency_key` | CharField | max 128 |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `attempts` | PositiveIntegerField |  |  |  |
| `last_error` | CharField | max 255 | blank |  |
| `response_code` | PositiveSmallIntegerField |  | null |  |
| `created_at` | DateTimeField |  | blank |  |
| `delivered_at` | DateTimeField |  | null |  |

**Kısıtlar:** `webhook_delivery_idempotent_uniq` (UniqueConstraint); `webhook_delivery_durum_gecerli` (CheckConstraint)

## `fiyatlama`

### ContractReleaseConsumption

Append-only release tüketimi (F5-041b) — sipariş satırına bağlanır.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `plan` | ForeignKey | fiyatlama.ContractReleasePlan (PROTECT) |  |  |
| `order_line` | ForeignKey | siparis.OrderLine (PROTECT) |  |  |
| `yon` | CharField | max 16, choices |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `contractreleaseconsumption_miktar_pozitif` (CheckConstraint); `contractreleaseconsumption_yon_gecerli` (CheckConstraint); `contractreleaseconsumption_tek_tuketim_per_plan_line` (UniqueConstraint); `contractreleaseconsumption_tek_iade_per_plan_line` (UniqueConstraint)

### ContractReleaseEvent

Append-only dönemsel serbest bırakma kaydı.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `plan` | ForeignKey | fiyatlama.ContractReleasePlan (PROTECT) |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `donem_baslangic` | DateField |  |  |  |
| `donem_bitis` | DateField |  |  |  |
| `aciklama` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `contractreleaseevent_miktar_pozitif` (CheckConstraint); `contractreleaseevent_tarih_sirasi` (CheckConstraint)

### ContractReleasePlan

ContractReleasePlan(id, sozlesme, varyant, birim, toplam_taahhut, durum, aciklama, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `sozlesme` | ForeignKey | fiyatlama.FiyatSozlesmesi (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `toplam_taahhut` | DecimalField | 18,6 |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `aciklama` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `contractreleaseplan_taahhut_pozitif` (CheckConstraint); `contractreleaseplan_birim_gecerli` (CheckConstraint); `contractreleaseplan_durum_gecerli` (CheckConstraint)

### FiyatBatchIslek

FiyatBatchIslek(id, tip, durum, filtre, ozet, olusturan, olusturma_tarihi, yayin_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `tip` | CharField | max 16, choices |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `filtre` | JSONField |  | blank |  |
| `ozet` | JSONField |  | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `yayin_tarihi` | DateTimeField |  | null |  |

**Kısıtlar:** `fiyatbatch_tip_gecerli` (CheckConstraint); `fiyatbatch_durum_gecerli` (CheckConstraint)

### FiyatBatchSatir

FiyatBatchSatir(id, islek, varyant, onceki_sabit_fiyat, yeni_sabit_fiyat, delta_yuzde, sonuc, neden)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `islek` | ForeignKey | fiyatlama.FiyatBatchIslek (CASCADE) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `onceki_sabit_fiyat` | DecimalField | 14,2 | null |  |
| `yeni_sabit_fiyat` | DecimalField | 14,2 | null |  |
| `delta_yuzde` | DecimalField | 10,4 | null |  |
| `sonuc` | CharField | max 16, choices |  |  |
| `neden` | CharField | max 255 | blank |  |

**Kısıtlar:** `fiyatbatchsatir_islek_varyant_uniq` (UniqueConstraint)

### FiyatSozlesmesi

Firma bazlı fiyat sözleşmesi.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `kontrat_tipi` | CharField | max 16, choices |  |  |
| `satis_kanali` | ForeignKey | tanimlar.SatisKanali (PROTECT) | null | Boş = tüm kanallar (fallback). |
| `gecerlilik_baslangic` | DateField |  |  |  |
| `gecerlilik_bitis` | DateField |  |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `olusturan_kullanici` | ForeignKey | firmalar.Kullanici (PROTECT) |  |  |
| `onaylayan_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `versiyon` | PositiveIntegerField |  |  |  |
| `onceki_versiyon` | ForeignKey | fiyatlama.FiyatSozlesmesi (PROTECT) | null |  |
| `notlar` | TextField |  | blank |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `sozlesme_tarih_sirasi` (CheckConstraint); `sozlesme_firma_tip_versiyon_kanalsiz_uniq` (UniqueConstraint); `sozlesme_firma_tip_kanal_versiyon_uniq` (UniqueConstraint); `sozlesme_aktif_tarih_cakisma` (ExclusionConstraint)

### FiyatSozlesmesiKalemi

Sözleşme kalemi: metal + (opsiyonel) ayar bazında marj/işçilik tanımı.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `sozlesme` | ForeignKey | fiyatlama.FiyatSozlesmesi (CASCADE) |  |  |
| `metal` | ForeignKey | tanimlar.KiymetliMetal (PROTECT) | null | Takı ailesi gibi metal dışı durumlar için boş bırakılabilir. |
| `ayar` | ForeignKey | tanimlar.AyarMilyem (PROTECT) | null | Boş = tüm ayarlar (fallback). |
| `marj_tipi` | CharField | max 16, choices |  |  |
| `marj_degeri` | DecimalField | 14,4 |  |  |
| `iscilik` | DecimalField | 14,2 |  | Parça başına işçilik. Marj yüzde ise tabanı etkiler. |
| `islcilik_dahil_mi` | BooleanField |  |  | Yüzde marjda taban: metal + işçilik olsun mu? |
| `sira` | PositiveIntegerField |  |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `kalem_marj_tipi_gecerli` (CheckConstraint); `kalem_sozlesme_metal_ayar_uniq` (UniqueConstraint)

### PriceCalculationLog

Her hesap ve kilit buraya yazılır. Kırılım SADECE burada durur;

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `sozlesme` | ForeignKey | fiyatlama.FiyatSozlesmesi (PROTECT) |  |  |
| `kalem` | ForeignKey | fiyatlama.FiyatSozlesmesiKalemi (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (SET_NULL) | null |  |
| `gram` | DecimalField | 12,4 | null |  |
| `milyem` | DecimalField | 8,4 | null |  |
| `saf_birim_fiyat` | DecimalField | 18,4 | null |  |
| `para_birimi` | CharField | max 3 |  |  |
| `kur_tipi` | CharField | max 32 | blank |  |
| `kur_degeri` | DecimalField | 14,6 | null |  |
| `tas_bedeli` | DecimalField | 14,2 |  |  |
| `metal_bedeli` | DecimalField | 18,6 |  |  |
| `iscilik` | DecimalField | 14,2 |  |  |
| `marj` | DecimalField | 18,6 |  |  |
| `toplam` | DecimalField | 18,6 |  |  |
| `kaynak` | CharField | max 16, choices |  |  |
| `kilit_bitis` | DateTimeField |  | null |  |
| `notlar` | TextField |  | blank |  |
| `hesap_zamani` | DateTimeField |  | blank |  |

### PriceLock

Kabul edilmiş PriceQuote fiyatının kilit başlığı (proforma kilit).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `quote` | OneToOneField | fiyatlama.PriceQuote (PROTECT) | benzersiz |  |
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Denormalize tenant scope; quote.alici_firma ile eşit olmalı. |
| `toplam_vergisiz` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `kilit_zamani` | DateTimeField |  |  |  |
| `gecerlilik_sonu` | DateTimeField |  |  | Quote penceresi ile aynı; uzatılamaz (L-04). |
| `durum` | CharField | max 16, choices |  |  |
| `idempotency_key` | CharField | max 64 | null | İsteğe bağlı istemci anahtarı; firma içinde unique. |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `pricelock_toplam_vergisiz_negatif_degil` (CheckConstraint); `pricelock_durum_gecerli` (CheckConstraint); `pricelock_kilit_le_gecerlilik` (CheckConstraint); `pricelock_firma_idempotency_uniq` (UniqueConstraint)

### PriceQuote

Alıcıya sunulan vergisiz fiyat teklifinin değişmez başlığı.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `satis_kanali` | ForeignKey | tanimlar.SatisKanali (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `teklif` | ForeignKey | fiyatlama.TedarikciTeklif (PROTECT) |  |  |
| `teklif_versiyon` | PositiveIntegerField |  |  |  |
| `fiyat_modeli` | CharField | max 16 |  |  |
| `alici_sozlesme` | ForeignKey | fiyatlama.FiyatSozlesmesi (PROTECT) |  |  |
| `alici_sozlesme_versiyon` | PositiveIntegerField |  |  |  |
| `alici_kalem` | ForeignKey | fiyatlama.FiyatSozlesmesiKalemi (PROTECT) |  |  |
| `tedarikci_sozlesme` | ForeignKey | fiyatlama.FiyatSozlesmesi (PROTECT) | null |  |
| `tedarikci_sozlesme_versiyon` | PositiveIntegerField |  | null |  |
| `tedarikci_kalem` | ForeignKey | fiyatlama.FiyatSozlesmesiKalemi (PROTECT) | null |  |
| `para_birimi` | CharField | max 3 |  |  |
| `toplam_vergisiz` | DecimalField | 18,2 |  |  |
| `gram` | DecimalField | 12,4 | null |  |
| `gecerlilik_sonu` | DateTimeField |  |  |  |
| `hesap_zamani` | DateTimeField |  |  |  |
| `quote_ttl_saniye` | PositiveIntegerField |  |  |  |
| `alici_kur_tipi` | CharField | max 16 |  |  |
| `tedarikci_kur_tipi` | CharField | max 16 |  |  |
| `metal_kuru_alici` | ForeignKey | tanimlar.MetalKuru (PROTECT) | null |  |
| `metal_kuru_tedarikci` | ForeignKey | tanimlar.MetalKuru (PROTECT) | null |  |
| `doviz_gozlem_idler` | JSONField |  | blank |  |
| `hesap_girdisi` | JSONField |  | blank |  |
| `belge_turu` | CharField | max 16, choices |  |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `pricequote_toplam_vergisiz_negatif_degil` (CheckConstraint); `pricequote_ttl_pozitif` (CheckConstraint); `pricequote_belge_proforma` (CheckConstraint)

### PriceQuoteLine

Quote kalem satırı — uygulama + DB immutability.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `quote` | ForeignKey | fiyatlama.PriceQuote (CASCADE) |  |  |
| `kalem_tipi` | CharField | max 16, choices |  |  |
| `tutar` | DecimalField | 18,2 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `meta` | JSONField |  | blank |  |

**Kısıtlar:** `pricequoteline_tutar_negatif_degil` (CheckConstraint); `pricequoteline_quote_kalem_uniq` (UniqueConstraint)

### TedarikciTeklif

TedarikciTeklif(id, varyant, tedarikci, tedarikci_kodu, versiyon, onceki_teklif, gecerlilik_baslangic, gecerlilik_bitis, fiyat_modeli, gram, gram_tolerans, birim_fiyat, para_birimi, iscilik_override, temin_tipi, uretim_suresi_gun, oncelik, durum, onaylayan, onay_zamani, eslestirme_durumu, eslestirme_guveni, eslestiren_kullanici, eslestirme_kaniti, esdegerlik_seviyesi, hedef_urun, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `tedarikci` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `tedarikci_kodu` | CharField | max 64 | blank |  |
| `versiyon` | PositiveIntegerField |  |  |  |
| `onceki_teklif` | ForeignKey | fiyatlama.TedarikciTeklif (SET_NULL) | null |  |
| `gecerlilik_baslangic` | DateField |  | null |  |
| `gecerlilik_bitis` | DateField |  | null |  |
| `fiyat_modeli` | CharField | max 16, choices |  |  |
| `gram` | DecimalField | 12,4 | null |  |
| `gram_tolerans` | DecimalField | 6,4 |  |  |
| `birim_fiyat` | DecimalField | 18,4 | null |  |
| `para_birimi` | CharField | max 3 |  |  |
| `iscilik_override` | DecimalField | 12,2 | null |  |
| `temin_tipi` | CharField | max 16, choices |  |  |
| `uretim_suresi_gun` | PositiveIntegerField |  | null |  |
| `oncelik` | PositiveIntegerField |  |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `onaylayan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `onay_zamani` | DateTimeField |  | null |  |
| `eslestirme_durumu` | CharField | max 16, choices | blank |  |
| `eslestirme_guveni` | CharField | max 16, choices | blank |  |
| `eslestiren_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `eslestirme_kaniti` | JSONField |  | blank |  |
| `esdegerlik_seviyesi` | CharField | max 16, choices | blank |  |
| `hedef_urun` | ForeignKey | urunler.Urun (SET_NULL) | null | Eşleştirme önerisinin hedef katalog ürünü (ADR-0005). |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `teklif_yayinda_kodlu_uniq` (UniqueConstraint); `teklif_yayinda_kodsuz_uniq` (UniqueConstraint); `teklif_fiyat_modeli_alanlari_dolu` (CheckConstraint); `teklif_gecerlilik_tarih_sirasi` (CheckConstraint)

### TeklifTasMaliyeti

Teklife bağlı taş maliyet satırı (K-011).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `teklif` | ForeignKey | fiyatlama.TedarikciTeklif (CASCADE) |  | related_name=taslar: fiyat motoru ve admin uyumluluğu (K-011). |
| `tas_grubu` | CharField | max 16, choices |  |  |
| `adet` | PositiveIntegerField |  |  |  |
| `toplam_karat` | DecimalField | 10,4 |  |  |
| `toplu_mu` | BooleanField |  |  |  |
| `bedel` | DecimalField | 14,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `renk_derecesi` | CharField | max 8 | blank |  |
| `berraklik` | CharField | max 8 | blank |  |
| `kesim` | CharField | max 16 | blank |  |
| `sertifika_kurumu` | CharField | max 32 | blank |  |
| `sertifika_no` | CharField | max 64 | blank |  |
| `tas_turu` | CharField | max 64 | blank |  |
| `mense` | CharField | max 64 | blank |  |
| `islem` | CharField | max 64 | blank |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

## `finans`

### CariHesap

Ledger projeksiyonu. Doğrudan edit yok; yalnız cari_servisi.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Hesap sahibi (alıcı). |
| `karsi_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Karşı taraf (interim: platform). |
| `para_birimi` | CharField | max 3 |  |  |
| `bakiye` | DecimalField | 18,2 |  |  |
| `kredi_limiti` | DecimalField | 18,2 |  | 0 = limit kapalı (aşım kontrolü yok). >0 → max borç. |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `carihesap_firma_karsi_pb_uniq` (UniqueConstraint); `carihesap_kredi_limiti_negatif_degil` (CheckConstraint)

### HedgeEntry

İşaretli gram: + uzun / − kısa hedge; FX open_has'tan düşülür.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `grams` | DecimalField | 18,4 |  |  |
| `metal_kodu` | CharField | max 16 | blank |  |
| `idempotency_key` | CharField | max 64 | benzersiz |  |
| `aciklama` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `hedgeentry_grams_sifir_degil` (CheckConstraint)

### LedgerEntry

LedgerEntry(id, firma, karsi_firma, tutar, para_birimi, yon, hareket_tipi, referans_tip, referans_id, contra_of, idempotency_key, aciklama, olusturan, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Hesap sahibi (bakiyesi etkilenen firma). |
| `karsi_firma` | ForeignKey | firmalar.Firma (PROTECT) | null | Karşı taraf; U-005 netleşene kadar genelde platform (F5-K5). |
| `tutar` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `yon` | CharField | max 8, choices |  |  |
| `hareket_tipi` | CharField | max 16, choices |  |  |
| `referans_tip` | CharField | max 64 | blank |  |
| `referans_id` | CharField | max 64 | blank |  |
| `contra_of` | ForeignKey | finans.LedgerEntry (PROTECT) | null |  |
| `idempotency_key` | CharField | max 64 |  |  |
| `aciklama` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `ledgerentry_tutar_pozitif` (CheckConstraint); `ledgerentry_yon_gecerli` (CheckConstraint); `ledgerentry_firma_idempotency_uniq` (UniqueConstraint)

### PaymentIntent

PaymentIntent(id, order, alici_firma, tutar, para_birimi, durum, idempotency_key, ledger_entry, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Denormalize tenant; order.alici_firma ile eşit. |
| `tutar` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `idempotency_key` | CharField | max 64 |  |  |
| `ledger_entry` | ForeignKey | finans.LedgerEntry (PROTECT) | null |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `paymentintent_tutar_pozitif` (CheckConstraint); `paymentintent_durum_gecerli` (CheckConstraint); `paymentintent_firma_idempotency_uniq` (UniqueConstraint); `paymentintent_order_basarili_uniq` (UniqueConstraint)

### PaymentWebhookEvent

PaymentWebhookEvent(id, provider, event_id, event_type, payload, payment_intent, sonuc, detail, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `provider` | CharField | max 32 |  |  |
| `event_id` | CharField | max 128 |  |  |
| `event_type` | CharField | max 64 |  |  |
| `payload` | JSONField |  | blank |  |
| `payment_intent` | ForeignKey | finans.PaymentIntent (SET_NULL) | null |  |
| `sonuc` | CharField | max 16, choices |  |  |
| `detail` | CharField | max 255 | blank |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `paymentwebhook_provider_event_uniq` (UniqueConstraint)

### TedarikciHakEdis

Oran/üretim tutarı v1'de sabitlenmez (tutar null olabilir).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `quality_inspection` | ForeignKey | kalite.QualityInspection (PROTECT) |  |  |
| `tedarikci_firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `gram` | DecimalField | 18,4 |  | FX unpaid_supplier HAS payı (F5-K6). |
| `tutar` | DecimalField | 18,2 | null | Oran politikası sonrası; v1 null (F5-022). |
| `para_birimi` | CharField | max 3 | blank |  |
| `vade_tarihi` | DateTimeField |  |  |  |
| `hak_edis_tarihi` | DateTimeField |  | null |  |
| `idempotency_key` | CharField | max 64 |  |  |
| `aciklama` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `tedarikcihakedis_idempotency_uniq` (UniqueConstraint); `tedarikcihakedis_insp_tedarikci_uniq` (UniqueConstraint); `tedarikcihakedis_durum_gecerli` (CheckConstraint); `tedarikcihakedis_gram_negatif_degil` (CheckConstraint)

## `kalite`

### QualityInspection

QualityInspection(id, order, order_line, durum, shipment_blok, notlar, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `order_line` | ForeignKey | siparis.OrderLine (PROTECT) | null | V1 sipariş bazlı; satır rezerv (F6-K cevap 2). |
| `durum` | CharField | max 16, choices |  |  |
| `shipment_blok` | BooleanField |  |  | FAIL → True; sevkiyat create engeli (F6-010 / F6-K6). |
| `notlar` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `qualityinspection_durum_gecerli` (CheckConstraint)

### QualityMeasurement

QualityMeasurement(id, inspection, order_line, birim, beklenen, olculen, sapma_abs, tolerans_pct, tolerans_abs, izin_verilen_sapma, sonuc, override_uygulandi, override_gerekce, quote_gram, olusturan, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `inspection` | ForeignKey | kalite.QualityInspection (PROTECT) |  |  |
| `order_line` | ForeignKey | siparis.OrderLine (PROTECT) |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `beklenen` | DecimalField | 18,6 |  |  |
| `olculen` | DecimalField | 18,6 |  |  |
| `sapma_abs` | DecimalField | 18,6 |  |  |
| `tolerans_pct` | DecimalField | 8,4 |  |  |
| `tolerans_abs` | DecimalField | 18,6 |  |  |
| `izin_verilen_sapma` | DecimalField | 18,6 |  |  |
| `sonuc` | CharField | max 8, choices |  |  |
| `override_uygulandi` | BooleanField |  |  |  |
| `override_gerekce` | CharField | max 255 | blank |  |
| `quote_gram` | DecimalField | 12,4 | null | F6-K2 zincir kanıtı: PriceLock.quote.gram (GRAM satırında). |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `qualitymeasurement_beklenen_pozitif` (CheckConstraint); `qualitymeasurement_olculen_negatif_degil` (CheckConstraint); `qualitymeasurement_sapma_negatif_degil` (CheckConstraint); `qualitymeasurement_izin_negatif_degil` (CheckConstraint); `qualitymeasurement_pct_negatif_degil` (CheckConstraint); `qualitymeasurement_abs_negatif_degil` (CheckConstraint); `qualitymeasurement_birim_gecerli` (CheckConstraint); `qualitymeasurement_sonuc_gecerli` (CheckConstraint)

## `lojistik`

### ProofOfDelivery

ProofOfDelivery(id, shipment, teslim_alan, notlar, belgeler_ref, olusturan, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `shipment` | OneToOneField | lojistik.Shipment (PROTECT) | benzersiz |  |
| `teslim_alan` | CharField | max 120 |  |  |
| `notlar` | CharField | max 255 | blank |  |
| `belgeler_ref` | CharField | max 255 | blank | Harici belge/storage anahtarı; dosya binary yok (F6-022). |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

### ReturnLine

ReturnLine(id, return_request, order_line, miktar, birim)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `return_request` | ForeignKey | lojistik.ReturnRequest (PROTECT) |  |  |
| `order_line` | ForeignKey | siparis.OrderLine (PROTECT) |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `birim` | CharField | max 8, choices |  |  |

**Kısıtlar:** `returnline_request_orderline_uniq` (UniqueConstraint); `returnline_miktar_pozitif` (CheckConstraint); `returnline_birim_gecerli` (CheckConstraint)

### ReturnRequest

ReturnRequest(id, order, shipment, durum, sebep, stok_iade_yapildi, finans_mahsup_yapildi, notlar, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `shipment` | ForeignKey | lojistik.Shipment (PROTECT) |  | İade için teslim edilmiş sevkiyat (F6-030). |
| `durum` | CharField | max 16, choices |  |  |
| `sebep` | CharField | max 255 |  |  |
| `stok_iade_yapildi` | BooleanField |  |  | F6-031: ONAYLANDI sonrası ledger IADE yazıldı mı. |
| `finans_mahsup_yapildi` | BooleanField |  |  | F5-023: mahsup ledger yazıldı mı (ödeme iadesi yok). |
| `notlar` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `returnrequest_durum_gecerli` (CheckConstraint)

### Shipment

Shipment(id, order, durum, takip_no, notlar, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `takip_no` | CharField | max 64 | blank | F6-021 carrier port doldurur; v1 elle/boş. |
| `notlar` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `shipment_durum_gecerli` (CheckConstraint)

## `belgeler`

### Document

Document(id, firma, tip, baslik, storage_key, content_type, byte_size, metadata, olusturan, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Tenant sahibi; client firma_id güvenilmez. |
| `tip` | CharField | max 32, choices |  |  |
| `baslik` | CharField | max 120 |  |  |
| `storage_key` | CharField | max 255 |  | Harici object key / URI; dosya binary bu tabloda yok (K-014). |
| `content_type` | CharField | max 64 | blank |  |
| `byte_size` | PositiveIntegerField |  | null |  |
| `metadata` | JSONField |  | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `document_tip_gecerli` (CheckConstraint); `document_storage_key_dolu` (CheckConstraint)

### TasSertifikaBelgesi

Tam olarak bir taş satırına (katalog veya teklif) bağlanır.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `document` | OneToOneField | belgeler.Document (PROTECT) | benzersiz |  |
| `urun_tasi` | ForeignKey | urunler.UrunTasi (PROTECT) | null |  |
| `teklif_tas` | ForeignKey | fiyatlama.TeklifTasMaliyeti (PROTECT) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `tassertifikabelgesi_tek_hedef` (CheckConstraint)

## `siparis`

### Cart

Firma başına tek sepet. Stok düşürmez; checkout’ta lock+rezervasyon (F4-040).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `alici_firma` | OneToOneField | firmalar.Firma (PROTECT) | benzersiz | Tenant sınırı (ADR-0003). Org scope: sube (ADR-0015 OH-3). |
| `sube` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null | Opsiyonel org/şube; tenant değil. |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

### CartLine

Fiyat: PriceQuote FK (referans). Snapshot/kilit F4-040/051’de.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `cart` | ForeignKey | siparis.Cart (CASCADE) |  |  |
| `price_quote` | ForeignKey | fiyatlama.PriceQuote (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `cartline_miktar_pozitif` (CheckConstraint); `cartline_birim_gecerli` (CheckConstraint); `cartline_cart_varyant_uniq` (UniqueConstraint)

### CheckoutAttempt

CheckoutAttempt(id, alici_firma, cart, idempotency_key, durum, sonuc, hata_mesaji, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `cart` | ForeignKey | siparis.Cart (SET_NULL) | null |  |
| `idempotency_key` | CharField | max 64 |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `sonuc` | JSONField |  | blank | Başarıda lock/rezervasyon satır özeti (kör: tedarikçi adı yok). |
| `hata_mesaji` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `checkout_firma_idempotency_uniq` (UniqueConstraint); `checkout_durum_gecerli` (CheckConstraint)

### Order

Order(id, alici_firma, sube, checkout_attempt, durum, idempotency_key, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Tenant sınırı (ADR-0003). Org scope ayrı: sube (ADR-0015). |
| `sube` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null | Opsiyonel org/şube (OH-3); tenant değil. |
| `checkout_attempt` | OneToOneField | siparis.CheckoutAttempt (PROTECT) | benzersiz |  |
| `durum` | CharField | max 16, choices |  |  |
| `idempotency_key` | CharField | max 64 |  |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `order_durum_gecerli` (CheckConstraint); `order_firma_idempotency_uniq` (UniqueConstraint)

### OrderLine

Kur değişimi satır tutarını etkilemez — snapshot alanları sabit.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `order` | ForeignKey | siparis.Order (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `price_lock` | OneToOneField | fiyatlama.PriceLock (PROTECT) | benzersiz | L-11: sipariş satırı kilide bağlanır. |
| `stock_reservation` | OneToOneField | stok.StockReservation (PROTECT) | benzersiz |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `snapshot_birim_fiyat_vergisiz` | DecimalField | 18,2 |  |  |
| `snapshot_satir_tutari_vergisiz` | DecimalField | 18,2 |  |  |
| `para_birimi` | CharField | max 3 |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `orderline_miktar_pozitif` (CheckConstraint); `orderline_birim_gecerli` (CheckConstraint); `orderline_birim_fiyat_negatif_degil` (CheckConstraint); `orderline_satir_tutar_negatif_degil` (CheckConstraint)

### RFQ

RFQ(id, alici_firma, sube, baslik, talep_tipi, durum, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  |  |
| `sube` | ForeignKey | firmalar.OrgBirimi (PROTECT) | null |  |
| `baslik` | CharField | max 200 |  |  |
| `talep_tipi` | CharField | max 16, choices |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `rfq_durum_gecerli` (CheckConstraint); `rfq_talep_tipi_gecerli` (CheckConstraint)

### RFQEslestirme

Platform aracılı eşleştirme önerisi (kör havuz; tedarikçi kimliği yok).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `rfq_line` | ForeignKey | siparis.RFQLine (CASCADE) |  |  |
| `onerilen_varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `skor` | PositiveSmallIntegerField |  |  |  |
| `kanit` | JSONField |  | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `rfqeslestirme_durum_gecerli` (CheckConstraint); `rfqeslestirme_line_varyant_onerildi_uniq` (UniqueConstraint); `rfqeslestirme_line_onaylandi_uniq` (UniqueConstraint)

### RFQLine

RFQLine(id, rfq, aciklama, miktar, birim, varyant)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `rfq` | ForeignKey | siparis.RFQ (CASCADE) |  |  |
| `aciklama` | CharField | max 255 |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `birim` | CharField | max 8 |  |  |
| `varyant` | ForeignKey | urunler.Varyant (SET_NULL) | null |  |

**Kısıtlar:** `rfqline_miktar_pozitif` (CheckConstraint)

### RFQMessage

Platform aracılı mesaj; alıcı↔tedarikçi kimliği yok (kör).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `rfq` | ForeignKey | siparis.RFQ (CASCADE) |  |  |
| `govde` | TextField |  |  |  |
| `gonderen_rol` | CharField | max 32 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

### RFQRevizyon

F10-022 — özel üretim/tasarım revizyon geçmişi (append-only; kör rol).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `rfq` | ForeignKey | siparis.RFQ (CASCADE) |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `ozet` | CharField | max 500 |  |  |
| `gonderen_rol` | CharField | max 32 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `rfqrevizyon_rfq_sira_unique` (UniqueConstraint); `rfqrevizyon_sira_pozitif` (CheckConstraint)

## `stok`

### StockBalance

StockBalance(id, warehouse, teklif, varyant, birim, on_hand, reserved, blocked, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `warehouse` | ForeignKey | stok.Warehouse (PROTECT) |  |  |
| `teklif` | ForeignKey | fiyatlama.TedarikciTeklif (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `on_hand` | DecimalField | 18,6 |  |  |
| `reserved` | DecimalField | 18,6 |  |  |
| `blocked` | DecimalField | 18,6 |  |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `stockbalance_wh_teklif_birim_uniq` (UniqueConstraint); `stockbalance_birim_gecerli` (CheckConstraint); `stockbalance_negatif_degil` (CheckConstraint)

### StockMovement

StockMovement(id, warehouse, teklif, varyant, birim, miktar, tip, neden, olusturan, olusturma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `warehouse` | ForeignKey | stok.Warehouse (PROTECT) |  |  |
| `teklif` | ForeignKey | fiyatlama.TedarikciTeklif (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  | Denormalize: teklif.varyant ile eşit olmalı. |
| `birim` | CharField | max 8, choices |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `tip` | CharField | max 24, choices |  |  |
| `neden` | CharField | max 255 | blank |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  |  |  |

**Kısıtlar:** `stockmovement_miktar_sifir_degil` (CheckConstraint); `stockmovement_birim_gecerli` (CheckConstraint)

### StockReservation

StockReservation(id, warehouse, teklif, varyant, birim, miktar, durum, gecerlilik_sonu, alici_firma, idempotency_key, olusturan, olusturma_tarihi, kapanma_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `warehouse` | ForeignKey | stok.Warehouse (PROTECT) |  |  |
| `teklif` | ForeignKey | fiyatlama.TedarikciTeklif (PROTECT) |  |  |
| `varyant` | ForeignKey | urunler.Varyant (PROTECT) |  |  |
| `birim` | CharField | max 8, choices |  |  |
| `miktar` | DecimalField | 18,6 |  |  |
| `durum` | CharField | max 16, choices |  |  |
| `gecerlilik_sonu` | DateTimeField |  |  |  |
| `alici_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Rezervasyonu yapan alıcı firma (tenant). |
| `idempotency_key` | CharField | max 64 | null |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `kapanma_tarihi` | DateTimeField |  | null |  |

**Kısıtlar:** `stockreservation_miktar_pozitif` (CheckConstraint); `stockreservation_birim_gecerli` (CheckConstraint); `stockreservation_durum_gecerli` (CheckConstraint); `stockreservation_wh_idempotency_uniq` (UniqueConstraint)

### Warehouse

Warehouse(id, kod, ad, sahip_firma, sahip_tipi, aktif, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 32 |  |  |
| `ad` | CharField | max 120 |  |  |
| `sahip_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Platform veya tedarikçi firma; alıcı-only ve konsinye yok. |
| `sahip_tipi` | CharField | max 16, choices |  |  |
| `aktif` | BooleanField |  |  |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `warehouse_firma_kod_uniq` (UniqueConstraint); `warehouse_sahip_tipi_gecerli` (CheckConstraint)

## `tanimlar`

### AyarMilyem

AyarMilyem(id, metal, fiyat_kaynagi, ayar_degeri, ayar_kodu, milyem)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `metal` | ForeignKey | tanimlar.KiymetliMetal (PROTECT) |  |  |
| `fiyat_kaynagi` | CharField | max 16, choices |  | ADR-0018: MIRAS → KurPolitikasi; CANLI/MANUEL override. |
| `ayar_degeri` | PositiveIntegerField |  |  | Altın için karat (14, 22), Gümüş için saflık derecesi (925) giriniz. |
| `ayar_kodu` | CharField | max 15 |  |  |
| `milyem` | DecimalField | 4,3 |  | Has metal oranını ondalık girin. Örn: 14K Altın için 0.585, 925 Gümüş için 0.925 |

**Kısıtlar:** `benzersiz_metal_ayar_kodu` (UniqueConstraint); `benzersiz_metal_milyem_orani` (UniqueConstraint)

### DovizKuru

DovizKuru(id, para_birimi, saglayici, kur_tipi, zaman, alinma_zamani, kur, kaynak, manuel_neden, girilme_zamani, giren_kullanici, onaylayan_kullanici, onay_zamani)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `para_birimi` | CharField | max 10, choices |  |  |
| `saglayici` | ForeignKey | tanimlar.KurSaglayici (PROTECT) |  |  |
| `kur_tipi` | CharField | max 16, choices |  |  |
| `zaman` | DateTimeField |  |  |  |
| `alinma_zamani` | DateTimeField |  |  |  |
| `kur` | DecimalField | 14,4 |  |  |
| `kaynak` | CharField | max 10, choices |  |  |
| `manuel_neden` | TextField |  | blank |  |
| `girilme_zamani` | DateTimeField |  | blank |  |
| `giren_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `onaylayan_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `onay_zamani` | DateTimeField |  | null |  |

**Kısıtlar:** `doviz_kuru_pozitif` (CheckConstraint); `benzersiz_doviz_kur_tipi_zaman` (UniqueConstraint)

### FiyatGrubu

Fiyat sözleşmesinin işçilik şartını bağladığı küçük ürün grubu listesi.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 20 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### KiymetliMetal

KiymetliMetal(id, kod, ad, gram_bazli)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 10 | benzersiz |  |
| `ad` | CharField | max 50 |  |  |
| `gram_bazli` | BooleanField |  |  |  |

### KurAlertKurali

KurAlertKurali(id, metal, kur_tipi, yon, esik_fiyat, aktif, son_tetik_gozlem, olusturan, olusturma_tarihi, guncelleme_tarihi)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `metal` | ForeignKey | tanimlar.KiymetliMetal (CASCADE) |  |  |
| `kur_tipi` | CharField | max 16, choices |  |  |
| `yon` | CharField | max 8, choices |  |  |
| `esik_fiyat` | DecimalField | 14,4 |  | TL/gr eşik; 0 yasak. |
| `aktif` | BooleanField |  |  |  |
| `son_tetik_gozlem` | ForeignKey | tanimlar.MetalKuru (SET_NULL) | null |  |
| `olusturan` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `olusturma_tarihi` | DateTimeField |  | blank |  |
| `guncelleme_tarihi` | DateTimeField |  | blank |  |

**Kısıtlar:** `kuralert_esik_pozitif` (CheckConstraint); `kuralert_yon_gecerli` (CheckConstraint)

### KurPolitikasi

Tek satır beklenir (`anahtar=default`); servis get_or_create ile okur.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `anahtar` | CharField | max 16 | benzersiz |  |
| `alici_kur_tipi` | CharField | max 16, choices |  |  |
| `tedarikci_kur_tipi` | CharField | max 16, choices |  |  |
| `fiyat_kaynagi` | CharField | max 16, choices |  |  |
| `feed_health` | CharField | max 24, choices |  |  |
| `feed_banner` | CharField | max 255 | blank |  |
| `sok_esigi_yuzde` | DecimalField | 6,2 |  |  |
| `capraz_makas_esigi_yuzde` | DecimalField | 6,2 |  |  |
| `min_marj_pct` | DecimalField | 6,2 |  |  |
| `max_batch_satir` | PositiveIntegerField |  |  |  |
| `guncelleme` | DateTimeField |  | blank |  |

### KurSaglayici

KurSaglayici(id, kod, ad, aktif, max_gecikme_saniye, olusturma, guncelleme)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 32 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `aktif` | BooleanField |  |  |  |
| `max_gecikme_saniye` | PositiveIntegerField |  |  | Piyasa zamanı ile alınma/now arasındaki üst sınır; aşılırsa gözlem stale. |
| `olusturma` | DateTimeField |  | blank |  |
| `guncelleme` | DateTimeField |  | blank |  |

**Kısıtlar:** `kur_saglayici_max_gecikme_pozitif` (CheckConstraint); `tek_aktif_kur_saglayici` (UniqueConstraint)

### MetalKuru

MetalKuru(id, metal, saglayici, kur_tipi, zaman, alinma_zamani, saf_birim_fiyat, kaynak, manuel_neden, girilme_zamani, giren_kullanici, onaylayan_kullanici, onay_zamani)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `metal` | ForeignKey | tanimlar.KiymetliMetal (PROTECT) |  |  |
| `saglayici` | ForeignKey | tanimlar.KurSaglayici (PROTECT) |  |  |
| `kur_tipi` | CharField | max 16, choices |  |  |
| `zaman` | DateTimeField |  |  |  |
| `alinma_zamani` | DateTimeField |  |  |  |
| `saf_birim_fiyat` | DecimalField | 14,4 |  |  |
| `kaynak` | CharField | max 10, choices |  |  |
| `manuel_neden` | TextField |  | blank |  |
| `girilme_zamani` | DateTimeField |  | blank |  |
| `giren_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `onaylayan_kullanici` | ForeignKey | firmalar.Kullanici (SET_NULL) | null |  |
| `onay_zamani` | DateTimeField |  | null |  |

**Kısıtlar:** `metal_kuru_fiyat_pozitif` (CheckConstraint); `benzersiz_metal_kur_tipi_zaman` (UniqueConstraint)

### SatisKanali

SatisKanali(id, kod, ad, sira, aktif, quote_ttl_saniye)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 20 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |
| `quote_ttl_saniye` | PositiveIntegerField |  | null | ADR-0008 B-03: kanal bazlı quote geçerliliği. Boşsa quote üretilmez (3.5). |

**Kısıtlar:** `satis_kanali_quote_ttl_pozitif` (CheckConstraint)

## `urunler`

### Berraklik

Sıra önemli: FL en yüksek, I1 en düşük. `sira` alanını bozma.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### Kategori

E-ticaret Kategori Ağacı Modeli.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `slug` | SlugField | max 100 | null, benzersiz | Boş bırakılırsa isimden otomatik üretilir. SEO dostu URL'ler için zorunludur. |
| `ust` | ForeignKey | urunler.Kategori (PROTECT) | null | Eğer boşsa bu bir ana kategoridir. |
| `fiyat_grubu` | ForeignKey | tanimlar.FiyatGrubu (PROTECT) | null | Ana kategoride zorunlu. Alt kategoride boş bırakılırsa üst kategorinin grubu miras alınır. |
| `sira` | PositiveIntegerField |  |  | Menüde küçük olan sayı önce listelenir. |
| `aktif` | BooleanField |  |  |  |
| `dahili` | BooleanField |  |  | İşaretliyse kategori vitrine ve API'ye çıkmaz, sadece platform içi muhasebe/raporlamada kullanılır. |
| `one_cikan` | BooleanField |  |  | Menünün en üstünde veya ana sayfada popüler başlıklar olarak vurgulanır. |
| `gorsel` | FileField |  | null | Kategori sayfalarının tepesinde veya mega menülerde gösterilecek yüksek çözünürlüklü resim. |
| `ikon` | CharField | max 50 | null | Mobil menülerde kategori adının yanında çıkacak ikon kodu (Örn: fa-gem, fas fa-tshirt). |
| `seo_baslik` | CharField | max 150 | null | Tarayıcı sekmesinde görünecek başlık. Boşsa kategori adı kullanılır. |
| `seo_aciklama` | TextField |  | null | Kategori sayfasının en altında listelenecek, arama motorlarını besleyen rehber yazı. |
| `pazaryeri_kategorisi` | CharField | max 255 | null | Pazaryeri kategori ağacıyla birebir eşleştirme için (Örn: Takı & Mücevher > Kolye). |

### KesimKalitesi

KesimKalitesi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### Koleksiyon

Koleksiyon(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### KopcaTipi

KopcaTipi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### MihlamaTipi

MihlamaTipi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### OlcuDegeri

Ölçü değeri (yüzük numarası, bilezik boyu, zincir uzunluğu...).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `tip` | CharField | max 15, choices |  |  |
| `sayisal_deger` | DecimalField | 5,2 |  | Örn: 14.00, 19.00, 45.00 |
| `deger` | CharField | max 20 |  | Örn: 14 No, 19 cm, 45 cm |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |
| `entegrasyon_kodu` | CharField | max 50 | null |  |

**Kısıtlar:** `benzersiz_olcu_tip_sayisal` (UniqueConstraint); `olcu_sayisal_deger_pozitif` (CheckConstraint)

### OzelGun

OzelGun(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### Renk

Metalin rengi (sarı, beyaz, rose...). Varyant ekseni.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### RenkDerecesi

RenkDerecesi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### SertifikaKurumu

SertifikaKurumu(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### Stil

Stil(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### TasKesimi

TasKesimi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### TasMensei

Doğal / laboratuvar üretimi / simülant. Yasal etiketleme için ayrı tutulur.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### TasTipi

Taş tipi. `degerli=True` olan tipler (pırlanta, safir vb.)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |
| `degerli` | BooleanField |  |  | Pırlanta, safir gibi değerli taşlarda karat girişini zorunlu kılar. |

### Teknik

Teknik(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### Urun

Müşterinin vitrinde gördüğü model (ör. "Tek taş yüzük").

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `platform_kodu` | CharField | max 20 | benzersiz, blank | Otomatik üretilir. Müşteriye ve API'ye bu kod gider. |
| `olusturan_firma` | ForeignKey | firmalar.Firma (PROTECT) |  | Denetim alanı. Alıcıya hiçbir yüzeyde gösterilmez (ADR-0005 K6). |
| `kimlik_sinifi` | CharField | max 1, choices |  |  |
| `kimlik_anahtari` | CharField | max 255 | blank | A/B: sertifika/parça veya marka+model(+GTIN). C: platform spec anahtarı. |
| `ad` | CharField | max 150 |  |  |
| `aciklama` | TextField |  | blank |  |
| `kategori` | ForeignKey | urunler.Kategori (PROTECT) |  |  |
| `ayar` | ForeignKey | tanimlar.AyarMilyem (PROTECT) |  | Metal buradan belirlenir. Çelik için Ayarsız seçilir. |
| `fiyat_tipi` | CharField | max 10, choices |  |  |
| `fiyat_kaynagi` | CharField | max 16, choices |  | ADR-0018 CP-1: ürün → ayar → politika. |
| `temin_tipi` | CharField | max 15, choices |  |  |
| `termin_gun` | PositiveIntegerField |  | null |  |
| `renk_ekseni` | BooleanField |  |  | İşaretliyse her varyantın rengi zorunlu (sarı/beyaz/rose gibi). |
| `olcu_tipi` | CharField | max 15, choices | blank | Boşsa ürün bedensizdir. Doluysa her varyantın bu tipte bir ölçüsü olmalı. |
| `koleksiyon` | ForeignKey | urunler.Koleksiyon (PROTECT) | null |  |
| `hedef_kitle` | CharField | max 10, choices | blank |  |
| `yas_grubu` | ForeignKey | urunler.YasGrubu (PROTECT) | null |  |
| `yuzey` | CharField | max 10, choices | blank |  |
| `zincir_tipi` | ForeignKey | urunler.ZincirTipi (PROTECT) | null |  |
| `kopca_tipi` | ForeignKey | urunler.KopcaTipi (PROTECT) | null |  |
| `slug` | SlugField | max 160 | benzersiz, blank | Küçük harf, tireli ve Türkçe karaktersiz benzersiz sayfa adresi. Boş bırakılırsa otomatik üretilir. |
| `meta_baslik` | CharField | max 70 | blank | Google arama sonuçlarındaki mavi başlık. Boş bırakılırsa otomatik oluşturulur. |
| `meta_aciklama` | TextField |  | blank | Google sonuçlarındaki özet metin. En fazla 160 karakter olmalıdır. |
| `canonical_url` | CharField | max 200 | null | Kopya içerik algoritmasını önlemek için asıl ürünün tam internet adresi. |
| `gorsel_alt_metni` | TextField |  | blank | Görsellerin arama motorları tarafından indekslenmesi için açıklama metinleri. |
| `onay_durumu` | CharField | max 15, choices |  |  |
| `red_nedeni` | TextField |  | blank |  |
| `yayin_durumu` | CharField | max 10, choices |  |  |
| `olusturan_kullanici` | ForeignKey | firmalar.Kullanici (PROTECT) | null |  |
| `onaylayan_kullanici` | ForeignKey | firmalar.Kullanici (PROTECT) | null |  |
| `onay_zamani` | DateTimeField |  | null |  |
| `olusturma_zamani` | DateTimeField |  | blank |  |
| `guncelleme_zamani` | DateTimeField |  | blank |  |
| `teknikler` | ManyToManyField | urunler.Teknik | blank |  |
| `stiller` | ManyToManyField | urunler.Stil | blank |  |
| `ozel_gunler` | ManyToManyField | urunler.OzelGun | blank |  |

**Kısıtlar:** `urun_yayin_icin_onay` (CheckConstraint); `urun_onayli_icin_onaylayan_ve_zaman` (CheckConstraint); `urun_kimlik_ab_anahtar_uniq` (UniqueConstraint)

### UrunKanal

Ürünün hangi satış kanalında yayında olduğu.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `urun` | ForeignKey | urunler.Urun (CASCADE) |  |  |
| `kanal` | ForeignKey | tanimlar.SatisKanali (PROTECT) |  |  |
| `aktif` | BooleanField |  |  |  |

**Kısıtlar:** `benzersiz_urun_kanal` (UniqueConstraint)

### UrunTasi

Ürüne ait bir taş satırı. Birden fazla taş varsa birden fazla satır girilir.

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `urun` | ForeignKey | urunler.Urun (CASCADE) |  |  |
| `tas_tipi` | ForeignKey | urunler.TasTipi (PROTECT) |  |  |
| `adet` | PositiveIntegerField |  |  |  |
| `karat` | DecimalField | 7,3 | null | Toplam taş ağırlığı |
| `bedel` | DecimalField | 14,2 |  |  |
| `kesim` | ForeignKey | urunler.TasKesimi (PROTECT) | null |  |
| `mihlama_tipi` | ForeignKey | urunler.MihlamaTipi (PROTECT) | null |  |
| `mensei` | ForeignKey | urunler.TasMensei (PROTECT) | null |  |
| `berraklik` | ForeignKey | urunler.Berraklik (PROTECT) | null |  |
| `renk_derecesi` | ForeignKey | urunler.RenkDerecesi (PROTECT) | null |  |
| `kesim_kalitesi` | ForeignKey | urunler.KesimKalitesi (PROTECT) | null |  |
| `sertifika_kurumu` | ForeignKey | urunler.SertifikaKurumu (PROTECT) | null |  |
| `sertifika_no` | CharField | max 50 | blank |  |

**Kısıtlar:** `urun_tasi_adet_pozitif` (CheckConstraint); `urun_tasi_bedel_negatif_degil` (CheckConstraint)

### Varyant

Sepete eklenen, stoku ve ağırlığı olan satış birimi (SKU).

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `urun` | ForeignKey | urunler.Urun (CASCADE) |  |  |
| `sku` | CharField | max 20 | benzersiz, blank |  |
| `tedarikci_sku` | CharField | max 50 | blank |  |
| `renk` | ForeignKey | urunler.Renk (PROTECT) | null |  |
| `beden` | ForeignKey | urunler.OlcuDegeri (PROTECT) | null |  |
| `gram` | DecimalField | 10,3 | null |  |
| `gram_bandi_min` | DecimalField | 10,3 | null | Boşsa settings VARYANT_GRAM_BANDI_ORAN ile hesaplanır (ADR-0005 K3). |
| `gram_bandi_max` | DecimalField | 10,3 | null |  |
| `sabit_fiyat` | DecimalField | 14,2 | null | Yalnızca fiyat tipi 'Sabit fiyat' olan ürünlerde. |
| `ek_bedel` | DecimalField | 14,2 |  | Kutu, sertifika, gravür gibi kalemlerin toplamı. |
| `benzersiz_parca` | BooleanField |  |  | Tek adet, tekrar üretilmeyen parça (ör. sertifikalı tek taş). |
| `aktif` | BooleanField |  |  |  |

**Kısıtlar:** `benzersiz_varyant_renk_beden` (UniqueConstraint); `benzersiz_varyant_beden_renksiz` (UniqueConstraint); `benzersiz_varyant_renk_bedensiz` (UniqueConstraint); `benzersiz_varyant_eksensiz` (UniqueConstraint); `varyant_gram_pozitif` (CheckConstraint); `varyant_sabit_fiyat_pozitif` (CheckConstraint); `varyant_ek_bedel_negatif_degil` (CheckConstraint)

### YasGrubu

YasGrubu(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |

### ZincirTipi

ZincirTipi(id, kod, ad, sira, aktif)

| Alan | Tip | Hedef / boyut | Bayrak | Not |
|------|-----|---------------|--------|-----|
| `kod` | CharField | max 30 | benzersiz |  |
| `ad` | CharField | max 80 |  |  |
| `sira` | PositiveIntegerField |  |  |  |
| `aktif` | BooleanField |  |  |  |
