# Faz 1 — Son teknik inceleme (kod öncesi)

**Durum:** İnceleme tamam — uygulama için hâlâ ayrı yetki gerekir  
**Tarih:** 2026-11-08  
**Bağlayıcı:** ADR-0003 · [`faz1-kimlik-gecis-tasarimi.md`](faz1-kimlik-gecis-tasarimi.md)  
**Korunan ilkeler:** (1) `firma` NOT NULL herkes için (2) sessiz tenant aşımı yok (3) tek rol + merkezi permission eşlemesi  

Bu belge kod/migration/model **yazmaz**. Geçiş, rol/yetki, superuser sınırı ve geri dönüş risklerini netleştirir.

Kanıt etiketleri: **DOĞRULANDI** / **DOĞRULANAMADI** / **PLANLAMA BULGUSU**.

---

## 0. Mevcut geliştirme DB anlık durumu

Salt okunur sorgu + `audit_user_assignments` (2026-11-08):

| Metrik | Değer | Sınıf |
|--------|--------|-------|
| `Firma` sayısı | 0 | DOĞRULANDI |
| `platform_mu=True` | 0 | DOĞRULANDI |
| `Kullanici` sayısı | 1 (`admin`, id=1) | DOĞRULANDI |
| `firma_id IS NULL` | 1 | DOĞRULANDI |
| `is_superuser` + null firma | 1 | DOĞRULANDI |
| Boş `rol` | 1 | DOĞRULANDI |
| Audit komutu | “Sorunlu kullanıcı: 1” — NOT NULL’a geçilmemeli | DOĞRULANDI |

**Sonuç:** Bu ortamda Faz 1’in ilk zorunlu veri adımı: Platform firmasını oluştur → `admin`’i bağla + kanonik rol ver → sonra `firma` NOT NULL. Üretim/staging sayıları **DOĞRULANAMADI** (bu oturumda yok); aynı audit komutu orada da kapı kontrolüdür.

---

## 1. Kullanıcı ve firma geçiş senaryoları

### 1.1 Senaryo kataloğu

| ID | Durum | Aksiyon (sıra) | NOT NULL öncesi kapı |
|----|--------|----------------|----------------------|
| S1 | Platform firması yok | Seed/create: tek `platform_mu=True`, `firma_kodu=PLATFORM` (veya sabit kod), `aktif=True`, `onay_durumu=onayli` | Platform firma var |
| S2 | Superuser / staff, `firma=NULL`, `rol` boş (mevcut `admin`) | Platform firmasına bağla; rol: `platform_super` veya `platform_admin` (operasyon seçer; varsayılan öneri aşağıda) | `firma_id` dolu + geçerli platform rolü |
| S3 | Kullanıcı `firma=NULL`, iş rolü dolu | Rol tipine göre hedef firma bulunamazsa **dur**; otomatik uydurma yok | Manuel eşleme + audit |
| S4 | Kullanıcı dolu firma + geçerli rol | Dokunma | — |
| S5 | Platform rolü, `firma.platform_mu=False` | Ya firmayı düzelt (yanlış) ya kullanıcıyı Platform firmasına taşı | Tip uyumu |
| S6 | Alıcı rolü, `alici_mi=False` | Firma tipi veya rol düzelt | Tip uyumu |
| S7 | Tedarikçi rolü, `tedarikci_mi=False` | Aynı | Tip uyumu |
| S8 | Geçersiz / boş rol kodu | Kanonik listeye map veya atama zorunlu | `rol ∈ ALL_ROLES` |
| S9 | Pasif firma (`aktif=False`) kullanıcısı | `firma` NOT NULL yine zorunlu; login/ops ayrı engel (uygulama) | FK dolu |
| S10 | Birden fazla platform firması denemesi | DB constraint zaten engeller | Mevcut constraint |

### 1.2 Önerilen varsayılan (S2 — mevcut admin)

**PLANLAMA BULGUSU (operasyon onayı ile sabitlenir):** Geliştirme `admin` → Platform firması + `platform_super` + `is_superuser` kalabilir; fakat tenant bypass `is_superuser` ile değil, permission + audit ile yürür. Alternatif: `platform_admin` + superuser bayrağı yalnız Django sistem komutları için.

### 1.3 Kapı komutları (uygulama zamanı — şimdi çalıştırma zorunluluğu yok)

```text
1. audit_user_assignments  → problems == 0
2. COUNT(firma_id IS NULL) == 0
3. COUNT(platform_mu=True) == 1
4. Her kullanıcının rolü kanonik listede ve firma tipi ile uyumlu
5. Sonra AlterField null=False
```

Mevcut audit çıktısı kapıyı **kapatır** (problems=1).

---

## 2. Sekiz platform rolü — kesin kodlar ve yetki çerçevesi

### 2.1 Kanonik kodlar (değişmez — ADR-0003-01)

| Kod | Görünen ad | Odak |
|-----|------------|------|
| `platform_super` | Platform: Super | Üst yönetim, kırık cam / geniş yetki seti |
| `platform_admin` | Platform: Admin | Firma onayı, kullanıcı/rol yönetimi, yapılandırma |
| `platform_ops` | Platform: Ops | Sipariş/operasyon akışı, teklif onayı (sınırlı) |
| `platform_finance` | Platform: Finans | Sözleşme, tahsilat/ödeme, maliyet görünümü |
| `platform_catalog` | Platform: Katalog | Ürün oluşturma/onay/yayın |
| `platform_quality` | Platform: Kalite | QC işlemleri |
| `platform_logistics` | Platform: Lojistik | Sevkiyat / teslimat operasyonu |
| `platform_support` | Platform: Destek | Salt okunur / sınırlı destek işlemleri (dar set) |

Firma rolleri (`alici_*`, `tedarikci_*`) bu tabloya **karışmaz**.

### 2.2 Permission yerleştirme (ADR-0003-04)

Faz 1’de tanımlanacak minimum permission’lar (Django `app_label.codename`; rapor §5.1 isimleri modele uyarlanır):

| Mantıksal izin | Model / app | Faz 1 öncelik |
|----------------|-------------|----------------|
| Firma onay / yönet | `firmalar.Firma` | Yüksek |
| Kullanıcı/rol yönet | `firmalar.Kullanici` | Yüksek |
| Ürün oluştur / güncelle / submit / approve | `urunler.Urun` | Yüksek (K-004 submit) |
| Teklif / sözleşme / fiyat | `fiyatlama.*` | Orta (seed iskeleti; endpoint yoksa bile matriste) |
| Sipariş / stok / QC / sevkiyat | İlerideki modeller | Düşük — placeholder kod **eklenmez**; matris satırı “sonraki faz” |

Rol kontrolü uygulama koduna dağılmaz: yalnız `has_perm` / merkezi `YetkiServisi` + seed matrisi.

### 2.3 Rol → yetki matrisi (Faz 1 çekirdek)

Rapor §7 sütunları Super / Ops / Catalog / Finance içindi. Eksik roller **PLANLAMA BULGUSU** olarak §7 + rol odağından türetilir; uygulama seed’i bu tabloyu tek kaynak yapar.

Gösterim: E = evet, H = hayır, S = sınırlı (kendi kapsamı / dar).

| İşlem (Faz 1 ilgili) | super | admin | ops | finance | catalog | quality | logistics | support |
|----------------------|:----:|:-----:|:---:|:-------:|:-------:|:-------:|:---------:|:-------:|
| Firma onayı | E | E | H | H | H | H | H | H |
| Platform kullanıcı/rol yönetimi | E | E | S | H | H | H | H | H |
| Tenant-genel liste (açık perm + audit) | E | E | S | S | S | S | S | S |
| Ürün oluşturma (platform adına) | E | S | S | H | E | H | H | H |
| Ürün onay / yayın | E | S | H | H | E | H | H | H |
| `onaya_gonder` (tedarikçi kaydı — K-004) | H* | H* | H* | H | H* | H | H | H |
| Teklif onayı (platform) | E | S | E | H | S | H | H | H |
| Fiyat sözleşmesi | E | S | H | E | H | H | H | H |
| QC | E | H | S | H | H | E | H | H |
| Lojistik / sevkiyat | E | H | S | H | H | H | E | H |
| Destek salt okuma | E | E | S | S | S | S | S | E |

\*Platform’un tedarikçi adına submit’i: Faz 1’de **varsayılan H**. Gerekirse ayrı `acting_as` + audit (rapor K-004); sessiz bypass yok. Tedarikçi kullanıcıları kendi `tedarikci_*` + `submit` perm ile gönderir.

**Alıcı/tedarikçi yöneticileri:** Yukarıdaki platform sütunlarının hiçbiri “E” sayılmaz — ayrı firma matrisi (rapor §7 alıcı/tedarikçi sütunları). `alici_yonetici` ≠ `platform_admin`.

### 2.4 Merkezi seed sözleşmesi

```text
ROLE_PERMISSION_MATRIX = {
  "platform_super": [...],
  "platform_admin": [...],
  ...
  "alici_yonetici": [...],
  ...
}
seed_roles()  # idempotent: Group get_or_create, permissions set() eşitle
```

Tekrar çalıştırma çoğaltmaz. Matris dışı `if rol ==` yasak.

---

## 3. Eski üç platform rolünün eşlenmesi

| Eski kod (DOĞRULANDI: `kullanici.py` L21–24) | Kanonik | Veri geçişi | Kullanıcı rename? |
|-----------------------------------------------|---------|-------------|-------------------|
| `platform_super` | `platform_super` | Kimlik — string aynı | Hayır |
| `platform_admin` | `platform_admin` | Kimlik | Hayır |
| `platform_ops` | `platform_ops` | Kimlik | Hayır |

| Yeni kod | Eski karşılık | Geçiş |
|----------|---------------|--------|
| `platform_finance` | Yok | Choices + boş Group/seed; kullanıcı ataması manuel |
| `platform_catalog` | Yok | Aynı |
| `platform_quality` | Yok | Aynı |
| `platform_logistics` | Yok | Aynı |
| `platform_support` | Yok | Aynı |

**DOĞRULANDI (bu DB):** Hiçbir kullanıcıda eski platform rol string’i yok (tek kullanıcı rolü boş). Bu ortamda eşleme migration’ı veri satırı güncellemez; yalnızca choices/seed genişler.

**Üretimde eski 3 kodlu kullanıcı varsa:** UPDATE gerekmez (kodlar kanonikte). Yalnız Group sync + permission seed yeter. Karşılıksız eski kod **yok** → silme planı gerekmez.

Alıcı/tedarikçi 10 rol: Faz 1’de kod değişmez (ADR-0003-01 sonuç).

---

## 4. Superuser vs platform yöneticisi — yetki sınırı

| Konu | `is_superuser` | `platform_admin` / `platform_super` (iş rolü) |
|------|----------------|-----------------------------------------------|
| `firma` FK | Zorunlu (Platform firması) | Zorunlu (Platform firması) |
| Tenant scope | Otomatik aşamaz | Yalnız açık permission ile (+ audit) |
| Django admin tüm modellere erişim | Django varsayılanı geniş; **proje politikası:** domain servis + `get_queryset` scope yine uygulanır; sessiz “her şeyi gör” iş kuralı sayılmaz | Permission + scope |
| Firma onayı, rol atama | İş izni yoksa yapamaz (servis `has_perm`) | Matris gereği E |
| `createsuperuser` | Teknik hesap açar; hemen firma+rol atama komutu zorunlu | — |
| Break-glass | Ayrı prosedür: neden + audit + mümkünse zaman sınırlı | Tercihen iş rolleriyle çöz |

### Kesin kurallar (korunacak üç ilke)

1. Superuser firmasız olamaz.  
2. Superuser tenant sınırını sessizce aşamaz.  
3. Yetki kararı rol string’ine dağılmaz; permission matrisi merkezidir — `platform_super` bile matristen okunur (süper set = matris satırı, sihirli if değil).

### Anti-pattern (yasak)

```text
if user.is_superuser: return allow
if user.rol == "platform_admin": ...
if user.rol in ("platform_ops", ...): ...
```

İzin verilen:

```text
YetkiServisi.require(user, "urunler.approve_urun")
scope_queryset(...)
```

---

## 5. Migration geri dönüş ve veri kaybı

### 5.1 Adım risk matrisi

| Adım | İleri | Geri dönüş | Veri kaybı riski |
|------|-------|------------|------------------|
| A1 `firma_kodu` null ekle | Additive | Kolonu drop | Yok |
| A2 backfill `firma_kodu` | Data | Yeniden üretilebilir | Düşük — yanlış kod operasyonel |
| A3 `firma_kodu` NOT NULL + unique | Constraint | Önce null aç | Orta — çakışan kod varsa migrate fail (güvenli fail) |
| B1 rol choices genişlet | AlterField | Eski 3 kod geçerli kalır | Yok |
| B2 `Meta.permissions` | migrate permissions | Permission satırları kalabilir; zararsız | Yok |
| B3 seed Groups | Data/command | Group silinebilir | Düşük |
| C2 kullanıcı `firma` backfill | Data | Yedekten restore | **Yüksek** — yanlış firmaya bağlama | 
| C3 `firma` NOT NULL | AlterField | null=True’ya dönüş migrate; NULL satır yoksa kolay | **Yüksek kapı** — NULL varken migrate **başarısız olmalı** (veri silinmez) |
| C4 bypass kaldırma | Kod | Revert commit | Davranış değişimi; veri silinmez |
| E1 K-004 sahiplik | Kod | Revert | Yok |

### 5.2 Bilinçli “yapılmayacaklar” (veri güvenliği)

- NULL firma satırlarını silerek NOT NULL’a zorlamak **yasak**.
- Firmasız kullanıcıya rastgele firma atamak **yasak**.
- Platform firmasını çoğaltmak **yasak** (constraint).
- Permission seed’i destructive `clear()` ile tüm auth permission’ları silmek **yasak** — yalnız rol gruplarının M2M set’i.
- Production’da migrate bu inceleme onayı + ayrı talimat olmadan **yasak**.

### 5.3 Geri dönüş runbook (özet)

1. C3 sonrası acil: yeni migration ile `null=True` (tercihen) veya backup restore — NULL kullanıcı yeniden oluşmasın diye uygulama kuralı gevşetilmezse tutarsızlık olur; geri dönüşte uygulama bypass’ı da revert edilir.  
2. A3 unique ihlali: çakışan `firma_kodu` düzeltilmeden ileri yok.  
3. Seed bozukluğu: idempotent seed’i tekrar çalıştır; Group permission set’ini matristen eşitle.

### 5.4 Bu geliştirme DB’si için somut sıra

```text
1. Platform firması oluştur (0 → 1)
2. admin → platform firma + platform_super (veya admin) + rol
3. audit_user_assignments → 0 problem
4. (opsiyonel) firma_kodu A1–A3
5. choices + permissions + seed
6. firma NOT NULL
7. bypass kaldırma + K-004 + test matrisi
```

Adımlar 1–2 şu an **DOĞRULANDI** gereksinim (aksi halde C3 imkânsız).

---

## 6. İnceleme sonucu ve açık operasyonel seçimler

### Sabit (değiştirilmeden korunur)

- ADR-0003-01…05  
- Üç ilke: NOT NULL, sessiz tenant aşımı yok, tek rol + merkezi perm  
- Kod/migration/model: ayrı yetki olmadan yok  

### Uygulama başlamadan operasyonun seçmesi gerekenler (mimari değil, atama)

| # | Seçim | Öneri |
|---|--------|--------|
| O1 | `admin` rolü `platform_super` mi `platform_admin` mi? | Geliştirme: `platform_super`; prod break-glass prosedürü ayrı |
| O2 | Platform `firma_kodu` string’i | `PLATFORM` |
| O3 | Platform adına `onaya_gonder` | Faz 1’de kapalı (H*); gerekirse sonraki ADR |
| O4 | §2.3’teki S/E hücreleri seed’e birebir mi? | Evet — sapma ADR güncellemesi ister |

### Hazırlık kontrol listesi (kod öncesi)

- [x] ADR-0003  
- [x] Faz 1 tasarım güncel  
- [x] Teknik inceleme (bu dosya)  
- [x] Yerel DB boş firma / firmasız superuser tespit  
- [ ] O1–O4 operasyon onayı  
- [ ] “Faz 1 kodunu uygula” açık talimatı  

**Sonuç:** Tasarım kontrollü uygulamaya hazır; kodlama için hâlâ **ayrı yetki** bekleniyor.
