# KUYUMBANK
# İş Analizi ve Teknik Analiz Raporu

**Doküman türü:** Ürün gereksinimleri + teknik çözüm şartnamesi  
**Sürüm:** 1.0  
**Analiz tarihi:** 08.11.2026  
**İncelenen kaynak:** Kullanıcının yüklediği `backend(django).zip`  
**Hedef okuyucu:** Ürün müdürü, yazılım mimarı, backend/frontend geliştiricileri, QA/test ekibi, operasyon yöneticisi  
**Karar:** Mevcut kod, alan modeli ve katalog/fiyatlama prototipi olarak değerlidir; ancak üretim ortamında kullanılabilecek tamamlanmış bir pazar yeri backend'i değildir.

---

## 0. Bu doküman nasıl kullanılmalı?

Bu doküman bir fikir notu değildir. Geliştirme işlerini açmak, veri modelini yeniden düzenlemek, API'leri geliştirmek ve testleri yazmak için hazırlanmış bir uygulama şartnamesidir.

Dokümanda dört bilgi türü birbirinden ayrılmıştır:

- **Mevcut kod bulgusu:** ZIP içindeki kaynakta doğrudan görülen durum.
- **Risk:** Mevcut durumun üretimde oluşturacağı teknik veya ticari sonuç.
- **Hedef karar:** Yeni geliştirmede uygulanması gereken çözüm.
- **İş kararı / yapılandırma:** Ticari veya hukuki onay gerektiren, kod içinde varsayılmaması gereken parametre.

Geliştirici, bu dokümanda açıkça tanımlanmış varsayılanları yeniden ürün kararı olarak tartışmaya açmamalı; doğrudan uygulamalıdır. Hukuki, vergi ve muhasebe etkisi olan konular ise kodda sabitlenmemeli, yapılandırılabilir tutulmalı ve ilgili uzman onayıyla canlıya alınmalıdır.

### 0.1 İnceleme sınırı ve doğrulama seviyesi

ZIP içinde 94 Python kaynak dosyası, yaklaşık 4.794 Python satırı, dört ana Django uygulaması (`firmalar`, `tanimlar`, `urunler`, `fiyatlama`) ve altı migration dosyası bulunmaktadır. Projede Django admin, model katmanı, bazı domain servisleri, seed komutları ve sınırlı testler vardır.

ZIP içinde aşağıdakiler bulunmamaktadır:

- REST API view, serializer, permission ve endpoint katmanı.
- Sepet, RFQ, sipariş, ödeme, tahsilat, iade, stok rezervasyonu, sevkiyat, kalite kontrol ve lojistik modülleri.
- Bildirim, e-posta/SMS kuyruğu, zamanlanmış görev ve entegrasyon servisleri.
- Ürün fotoğraf/video yönetimi için ürün medya modeli ve medya sunucu yapılandırması.
- Mimari karar kaydı, iş akışı diyagramı, API dokümanı, README veya kurulum/dağıtım dosyaları.
- Otomatik CI/CD ve test pipeline tanımı.

Kaynak dosyalar üzerinde statik inceleme yapıldı ve Python `compileall` sözdizimi kontrolü başarılı oldu. Bu, uygulamanın çalıştığını veya testlerin geçtiğini kanıtlamaz. İnceleme ortamında Django ve Django REST Framework kurulu olmadığı için `manage.py check`, migration kontrolü, veritabanı testi ve test paketi çalıştırılmadı. ZIP içindeki `.env` dosyasının içeriği rapora alınmamış ve hiçbir gizli değer paylaşılmamıştır.

**Önemli güvenlik notu:** ZIP içinde `config/.env` dosyası bulunuyor. Bu dosya kaynak kod deposuna ve paylaşılabilir arşivlere girmemelidir. İçinde gerçek parola, SECRET_KEY, veritabanı veya entegrasyon bilgisi bulunmuş olma ihtimali varsa bu değerler sızmış kabul edilerek döndürülmelidir. `.env.example` yalnızca boş/örnek değerlerle tutulmalıdır.

---

# 1. Yönetici özeti

## 1.1 Mevcut durum

Mevcut backend'in güçlü tarafları:

1. Firma, kullanıcı, rol, ürün, varyant, kategori, metal/ayar, kur ve fiyat sözleşmesi kavramları ayrı uygulamalara ayrılmış.
2. Ürün ile varyant ayrımı doğru yönde kurulmuş. Gram, renk ve ölçü gibi satış birimini etkileyen niteliklerin varyantta tutulması mantıklı.
3. Para hesaplarında `Decimal` kullanılması ve yuvarlamanın en sonda yapılması doğru bir başlangıç.
4. Ürün onay/yayın akışı için ayrı servis yazılmış; bazı geçişlerde transaction ve `select_for_update()` kullanılmış.
5. PostgreSQL'e uygun unique/check constraint'ler eklenmiş.
6. Kullanıcı başına tek firma ve tek rol hedefi model açıklamalarında açıkça belirtilmiş.

Buna rağmen mevcut sistemin ana eksikleri kritiktir:

- İşlevsel bir uygulama API'si yok; yalnızca Django admin üzerinden yönetilebilen bir domain iskeleti var.
- Firma bazlı veri izolasyonu ve gerçek rol/yetki denetimi uçtan uca uygulanmış değil.
- Ürün onay servisinde ürünün sahibi olan tedarikçi ile işlemi yapan kullanıcının ilişkisi doğrulanmıyor.
- `is_superuser` iş kurallarını atlamak ve platform yetkisi almak için kullanılıyor; bu, tek firmaya bağlı kullanıcı ilkesini deliyor.
- Tedarikçi teklifleri, ürünün tedarikçisi, stok ve fiyat sözleşmeleri arasında tutarlı bir ilişki kurulmamış.
- Fiyat çözümleme ile fiyat hesaplama birbirine bağlanmış, tamamlanmış ve değişmez bir fiyat teklifi/price-lock akışı haline getirilmemiş.
- Fiyat sözleşmesi kalemlerinde genel kural ve ayara özel kural davranışı kodun farklı bölümlerinde çelişiyor.
- Sipariş, stok rezervasyonu, finans, kalite, sevkiyat ve lojistik akışları yok.
- Ürün görseli, stüdyo çekimi ve medya varyantları için model yok.
- Testler temel model kurallarını kapsıyor; yetki, tenant izolasyonu, eşzamanlılık, fiyat bütünlüğü ve uçtan uca süreçleri kapsamıyor.

**Sonuç:** Mevcut yapıyı olduğu gibi genişletmek doğru değildir. Firma/kullanıcı ve katalog alanlarının bir bölümü iyileştirilerek korunmalı; fiyatlama alanı yeniden bütünleştirilmeli; teklif, sipariş, stok, finans, kalite, lojistik, medya ve API katmanları yeni domain modülleri olarak tasarlanmalıdır.

## 1.2 Ürün ve iş modeli için temel hedef

Kuyumbank, tedarikçilerin birbirini ve alıcıların gerçek tedarikçi kimliğini görmediği; platformun katalog, fiyatlama, sipariş, kalite kontrol, lojistik ve finans koordinasyonunu yönettiği kapalı devre bir ticaret platformu olarak ele alınmalıdır.

Bu hedefin teknik sonucu:

- Alıcı, yalnızca platform ürününü, kendi fiyatını, kendi siparişini ve kendisine ait belgeleri görür.
- Tedarikçi, yalnızca kendi tekliflerini, kendisine atanan üretim/tedarik işlerini ve kendi finansal hak edişlerini görür.
- Platform, tüm firmaları ve işlemleri yetkili operasyon ekranlarından görür.
- Tedarikçi kimliği, alış fiyatı, tedarikçi iç SKU'su, maliyet ve platform marjı alıcıya açılmaz.
- Aynı katalog ürünü birden fazla tedarikçiden temin edilebilir. Bu nedenle katalog ürünü ile tedarikçi teklifi birbirinden ayrılmalıdır.
- Fiyat, teklif anındaki metal kuru, milyem, işçilik, taş, döviz kuru, servis bedeli ve marj parametrelerinin değişmez bir anlık görüntüsüne dayanmalıdır.
- Sipariş verildiğinde fiyat ve ürün/teklif koşulları snapshot olarak saklanmalıdır; sonraki kur veya sözleşme değişiklikleri geçmiş siparişi değiştirmemelidir.

---

# 2. Mevcut backend envanteri

| Uygulama | Mevcut sorumluluk | Değerlendirme |
|---|---|---|
| `firmalar` | Firma, kullanıcı, adres, banka hesabı, rol-grup servisi | Temel doğru; yetki ve tenant izolasyonu eksik |
| `tanimlar` | Metal, ayar/milyem, metal kuru, döviz kuru, fiyat grubu, satış kanalı | Başlangıç için uygun; veri geçerliliği ve kur kaynağı/kalitesi eksik |
| `urunler` | Kategori, ürün, varyant, taş, ölçü, katalog referansları, kanal, ürün onayı | Katalog çekirdeği var; tedarikçi-katalog ayrımı ve medya eksik |
| `fiyatlama` | Tedarikçi teklifi, fiyat sözleşmesi, sözleşme kalemi, fiyat hesap fonksiyonu, hesap logu | Kavramlar var fakat birbirine bağlanmamış ve ticari akış tamamlanmamış |
| `config` | Django ayarları ve yalnızca admin URL'si | API/uygulama katmanı henüz yok |

## 2.1 Mevcut modeller

### Firma ve kimlik

- `Firma`
- `Kullanici`
- `FirmaAdresi`
- `FirmaBankaHesabi`

### Tanımlar

- `KiymetliMetal`
- `AyarMilyem`
- `MetalKuru`
- `DovizKuru`
- `FiyatGrubu`
- `SatisKanali`

### Katalog

- `Kategori`
- `Urun`
- `Varyant`
- `UrunKanal`
- `UrunTasi`
- `OlcuDegeri`
- Koleksiyon, renk, yaş grubu, teknik, stil, özel gün, zincir tipi, kopça tipi, taş tipi, taş kesimi, mıhlama tipi, taş menşei, sertifika kurumu, berraklık, renk derecesi ve kesim kalitesi referansları.

### Fiyatlama

- `TedarikciTeklif`
- `UrunTasi` (fiyatlama uygulamasında ikinci bir taş modeli)
- `FiyatSozlesmesi`
- `FiyatSozlesmesiKalemi`
- `PriceCalculationLog`

## 2.2 Mevcut uygulama sınırı

`config/urls.py` yalnızca `admin/` yolunu tanımlıyor. ZIP'te API view, serializer, permission, API URL veya frontend entegrasyonu bulunmuyor. `requirements.txt` içinde Django ve `django-import-export` gibi bağımlılıklar var; Django REST Framework, Celery ve Redis bağımlılıkları yok.

Bu nedenle mevcut backend'in şu anki teslim seviyesi **admin tabanlı domain prototipi** olarak tanımlanmalıdır; çalışan ticaret platformu veya API backend'i olarak tanımlanmamalıdır.

---

# 3. Kritik mevcut kod bulguları ve zorunlu düzeltmeler

Aşağıdaki maddeler geliştirme önceliğine göre sıralanmıştır. P0 maddeleri çözülmeden gerçek firma kullanıcılarına açılım yapılmamalıdır.

## P0 — Canlıya çıkışı engelleyen konular

### K-001 — API ve uygulama katmanı bulunmuyor

**Kanıt:** `config/urls.py` içinde yalnızca Django admin URL'si vardır. ZIP'te `views.py`, `serializers.py`, `permissions.py`, API router veya API endpoint modülü yoktur. `requirements.txt` içinde DRF yoktur.

**Risk:** Frontend veya mobil uygulamanın bağlanacağı sözleşme yoktur. İş kuralları admin formlarına bağımlı kalır; admin dışından güvenli ve tutarlı işlem yapılamaz.

**Karar:**
- Django REST Framework eklenmelidir.
- API `/api/v1/` altında sürümlenmelidir.
- View katmanı ince olmalı; iş kuralları domain servislerinde çalışmalıdır.
- Serializer yalnızca veri doğrulama/temsil yapmalı; fiyat, sipariş, stok ve yetki kararı serializer içine gömülmemelidir.
- Her endpoint için request/response örneği, hata kodu ve yetki matrisi yazılmalıdır.

### K-002 — Firma bazlı tenant izolasyonu yok

**Kanıt:** Mevcut ZIP'te API queryset filtrelemesi veya nesne seviyesinde permission sınıfı yoktur. `Firma` ve `Kullanici` modellerinin bulunması tek başına veri izolasyonu sağlamaz.

**Risk:** Bir firma kullanıcısı başka firmaya ait ürün, teklif, sipariş, adres, banka hesabı veya finansal kayda erişebilir. Kapalı devre iş modelinin en kritik güvenlik sınırı ihlal edilir.

**Karar:**
- Kullanıcının iş verisi sorguları varsayılan olarak `request.user.firma_id` üzerinden scope edilmelidir.
- Platform erişimi açık ve ayrı bir permission ile verilmelidir.
- İstemciden gelen `firma_id`, `tedarikci_id`, `alici_id` güvenilir kabul edilmemelidir. Sunucu bunları oturum kullanıcısı ve işlem bağlamından belirlemelidir.
- Her tenant-owned tabloda firma ilişkisi bulunmalı veya sahiplik ilişkisi kesin ve denetlenebilir olmalıdır.
- ID tahminiyle erişim (IDOR) testleri zorunlu olmalıdır.
- Alıcı ve tedarikçi API cevaplarında karşı taraf firma kimliği, iç kod, maliyet ve iletişim bilgisi bulunmamalıdır.

### K-003 — `is_superuser` firma/rol zorunluluğunu deliyor

**Kanıt:** `firmalar/models/kullanici.py` içindeki `save()` yalnızca `is_superuser=False` ise `full_clean()` çalıştırıyor. Dolayısıyla superuser için firma ve rol zorunlu değil. `urunler/services/onay_servisi.py` içindeki `platform_kullanicisi_mi()` da `is_superuser=True` ise platform yetkisi veriyor.

**Risk:** “Her kullanıcı yalnızca bir firmaya bağlı olsun” kuralı teknik olarak garanti edilmiyor. Django superuser kavramı iş rolü yerine kullanılıyor. Teknik yönetici hesabı, normal iş süreçlerinde platform kullanıcısı gibi işlem yapabiliyor.

**Karar:**
- İş kullanıcısı olan her `Kullanici` için `firma NOT NULL` ve tek `rol` zorunlu olmalıdır.
- Platform personeli de `Kuyumbank Platform` firmasına bağlanmalıdır.
- `is_superuser`, normal platform yetkilendirmesinde kullanılmamalıdır. Yalnızca acil durum/teknik yönetim hesabı için ayrı ve kontrollü tutulmalıdır.
- `createsuperuser` akışı için ayrı yönetim komutu veya zorunlu platform firma/rol ataması yapılmalıdır. Firma/rolsüz superuser üretim veritabanına yazılamamalıdır.
- Platform işlemleri `platform_super`, `platform_admin`, `platform_ops` gibi iş rollerinin granular izinleriyle kontrol edilmelidir.

### K-004 — Ürün onaya gönderme işleminde sahiplik/rol doğrulaması yok

**Kanıt:** `urunler/services/onay_servisi.py` içindeki `onaya_gonder(urun, kullanici)` fonksiyonunda `kullanici` parametresi kullanılmıyor. Fonksiyon, ürünü gönderen kullanıcının ürünün bağlı olduğu tedarikçi firmaya ait olup olmadığını veya rolünün bu işleme izin verip vermediğini doğrulamıyor.

**Risk:** Servis doğrudan çağrıldığında başka tedarikçinin ürününü onaya göndermek mümkün olabilir. Admin action'ın görünür olması da iş yetkisi kontrolünün yerine geçmez.

**Karar:**
- `onaya_gonder` işlemi `tedarikci_sahip`, `tedarikci_yonetici` veya açıkça yetkilendirilmiş ürün/katalog rolü tarafından yapılmalıdır.
- `urun.tedarikci_id == kullanici.firma_id` doğrulanmalıdır.
- Ürün oluşturma ve güncellemede de aynı sahiplik kontrolü uygulanmalıdır.
- Platform personelinin tedarikçi adına işlem yapması gerekiyorsa bu işlem `acting_as`/operasyon nedeni ile audit kaydına yazılmalıdır.
- Servis, kullanıcı parametresi olmadan çağrılamamalıdır.

### K-005 — Rol grupları güvenilir bir yetki sistemi haline getirilmemiş

**Kanıt:** `rol_servisi.py` rol grubu oluşturup kullanıcıya ekliyor; fakat ZIP'te rol gruplarına permission atayan bir kurulum/seed mekanizması görünmüyor. `KullaniciAdmin` standart `UserAdmin` üzerinden kaydetme yapıyor; `assign_user_role()` servisini çağıran özel `save_model` veya `save_related` görünmüyor. Sinyal dosyası da yok.

**Risk:** Admin üzerinden rol değiştiğinde grup üyeliği senkron kalmayabilir. Grup oluşturulsa bile gruba izin atanmadıysa rol grubu gerçek yetki sağlamaz.

**Karar:**
- Tek rol yazma noktası `assign_user_role()` olmalıdır.
- Admin kayıt akışı bu servisi kullanmalıdır.
- API kullanıcı/rol yönetimi de aynı servisi çağırmalıdır.
- Rol-permission matrisi kodla/seed ile kurulmalı ve test edilmelidir.
- Rol grubu yalnızca senkron mekanizması olarak kalmalı; yetki kararları açık permission kodlarıyla yapılmalıdır.
- Kullanıcıya doğrudan `user_permissions` atanması kapatılmalı; acil istisnalar audit edilmelidir.

### K-006 — Tedarikçi teklifi ile ürün sahibi arasındaki ilişki doğrulanmıyor

**Kanıt:** `TedarikciTeklif` hem `varyant` hem `tedarikci` alanı tutuyor; fakat `clean()` içinde `tedarikci == varyant.urun.tedarikci` doğrulaması yok. Veritabanı constraint'i de bu çapraz tablo kuralını garanti etmiyor.

**Risk:** Bir tedarikçi başka tedarikçiye ait varyanta teklif girebilir. Mevcut model aynı zamanda aynı katalog ürününün birden fazla tedarikçiden temin edilmesini doğru şekilde modelleyemiyor.

**Karar:**
- Katalog ürünü platform kataloğuna ait olmalı; tedarikçiye ait olmamalıdır.
- Tedarikçi ile katalog varyantı arasındaki ticari ilişki `SupplierOffer`/`TedarikciTeklif` üzerinden kurulmalıdır.
- Her teklif kendi tedarikçisine, varyanta, tedarikçi SKU'suna, fiyat koşuluna, stok/termin bilgisine ve geçerlilik dönemine sahip olmalıdır.
- Aynı varyant için birden fazla tedarikçinin aktif teklifi desteklenmelidir.
- Teklifin tedarikçi firması `kullanici.firma_id` ile kontrol edilmelidir.
- Mevcut `Urun.tedarikci` alanı ya kaldırılmalı ya da yalnızca “ilk/ana kaynak” gibi farklı ve açık bir iş anlamına dönüştürülmelidir. Varsayılan öneri: katalog ürününden kaldırılmasıdır.

### K-007 — Fiyat sözleşmesi kalemlerinde çelişkili kural

**Kanıt:** `FiyatSozlesmesiKalemi` açıklaması ve `clean()` metodu aynı metal için hem genel (`ayar=None`) hem ayara özel kalemin aynı sözleşmede bulunmasını engelliyor. Buna karşılık `sozlesme_cozumleme.py` açıklaması ve çözümleme mantığı ayara özel kalemin genel kaleme üstün gelmesini hedefliyor.

**Risk:** İş kuralı ile veri doğrulaması aynı şeyi söylemiyor. Geliştirici hangi davranışı uygulayacağını tahmin etmek zorunda kalır.

**Karar:**
- Sözleşme kalemlerinde aynı metal için genel kural ve birden fazla ayara özel kural birlikte bulunabilmelidir.
- Aynı sözleşme + metal + ayar kombinasyonu tekil olmalıdır.
- Genel kural (`ayar IS NULL`) yalnızca fallback olmalıdır.
- Çözümleme sırası: aktif sözleşme → kanal spesifikliği → ayar spesifikliği → sözleşme versiyonu → açık ve deterministik eşitlik kontrolü.
- Aynı öncelikte birden fazla sonuç varsa fiyat döndürülmemeli, `PricingRuleAmbiguity` hatası üretilmelidir.
- DB unique constraint ve servis testleri bu kararla uyumlu güncellenmelidir.

### K-008 — Fiyat sözleşmelerinde aktif tarih aralığı çakışması engellenmiyor

**Kanıt:** `FiyatSozlesmesi` başlangıç/bitiş tarih sırası ve versiyon tekilliği kontrol ediyor; ancak aynı firma + kontrat tipi + kanal için birden fazla `AKTIF` sözleşmenin tarih aralıklarının çakışmasını engelleyen bir kural görünmüyor.

**Risk:** Aynı gün ve kanal için birden fazla sözleşme geçerli olabilir. Çözümleme motoru sürpriz sonuç veya çoklu eşleşme üretebilir.

**Karar:**
- Aynı firma + kontrat tipi + kanal kapsamındaki aktif sözleşmelerin geçerlilik aralıkları çakışmamalıdır.
- Kanalı boş sözleşme tüm kanallar için fallback ise, kanal bazlı sözleşmelerle çakışma önceliği kesin tanımlanmalıdır.
- Aktif sözleşme yayınlama işlemi transaction içinde çakışma kontrolü yapmalıdır.
- PostgreSQL'de mümkünse tarih aralığı exclusion constraint; değilse kilitli servis kontrolü kullanılmalıdır.
- Sözleşme versiyonu yayınlandıktan sonra değiştirilemez; yeni versiyon açılır.

### K-009 — Fiyat hesaplama, teklif, sözleşme ve fiyat kilidi tek akış değil

**Kanıt:** `fiyatlama/services/fiyat_hesaplama.py` saf bir hesap fonksiyonu. Sözleşme çözümleyici ayrı dosyada. `TedarikciTeklif` ayrı model. `PriceCalculationLog` hesap girdilerinin ve çıktılarının bir kısmını tutuyor. Bunları uçtan uca birleştiren fiyatlama orkestrasyon servisi yok.

**Risk:** Aynı ürün farklı noktalarda farklı fiyatlanabilir. Alıcıya gösterilen fiyat ile siparişe yazılan fiyat arasında fark oluşabilir. Geçmiş fiyatın neden oluştuğu kanıtlanamayabilir.

**Karar:**
- Tek giriş noktası `PricingService.quote()` olmalıdır.
- Servis; varyant, tedarikçi teklifi, metal kuru, döviz kuru, ayar/milyem, sözleşme, kanal ve tarih bağlamını çözer.
- Hesaplama sonucu `PriceQuote` ve `PriceQuoteLine` tablolarına snapshot olarak yazılır.
- Snapshot; tüm hesap girdilerini, para birimini, kur zamanını/kaynağını, kural/sözleşme versiyonunu, tedarikçi teklif versiyonunu, ara kalemleri, toplamı ve geçerlilik sonunu saklar.
- Sipariş oluşturulurken geçerli quote kilitlenir; sipariş satırına fiyat snapshot'ı kopyalanır.
- Sonraki kur veya sözleşme değişiklikleri geçmiş siparişi değiştirmez.
- Fiyat kilidi süresi ve kur yenileme davranışı yapılandırılabilir olmalıdır.

### K-010 — Stok ve rezervasyon modeli yok; iki ayrı stok kaynağı var

**Kanıt:** `Varyant.stok` ve `TedarikciTeklif.stok_adet` ayrı ayrı stok tutuyor. Birbirine bağlanan, rezerve eden veya hareket kaydı oluşturan stok servisi yok.

**Risk:** İki alan farklılaşabilir. Aynı ürün eşzamanlı siparişlerde birden fazla alıcıya satılabilir. Hazır ürün, siparişe özel üretim ve benzersiz parça stokları doğru yönetilemez.

**Karar:**
- Ticari stok kaynağı tedarikçi + teklif/varyant seviyesinde tanımlanmalıdır.
- `InventoryBalance`, `InventoryMovement`, `StockReservation` modelleri kurulmalıdır.
- Sipariş/checkout sırasında stok transaction ve satır kilidi ile rezerve edilmelidir.
- Rezervasyonun son kullanma zamanı olmalı; ödeme/teyit gelmezse otomatik bırakılmalıdır.
- Benzersiz parçada aynı anda yalnızca bir aktif rezervasyon/sipariş bulunmalıdır.
- `Varyant.stok` yalnızca katalogdan türetilen toplam gösterim olacaksa hesaplanan alan olmalı; ikinci bağımsız stok kaynağı olarak kullanılmamalıdır.

## P1 — İlk ticari sürümden önce tamamlanması gerekenler

### K-011 — İki farklı `UrunTasi` modeli var

**Kanıt:** `urunler.UrunTasi` katalog ürünü taşlarını; `fiyatlama.UrunTasi` ise tedarikçi teklifine bağlı taş kalemlerini temsil ediyor. Alanları, para birimi yaklaşımı ve doğrulamaları farklı.

**Risk:** İsim çakışması ve kavramsal karışıklık. Ürün kataloğundaki taş özellikleri ile teklif maliyetindeki taş bedeli ayrımı açık değil. Fiyat motoru hangi modelden hangi değeri alacağını tek bir domain sözleşmesinde tanımlamıyor.

**Karar:**
- Katalog taş tanımı `ProductStone` (`UrunTasi`) olarak kalabilir.
- Tedarikçi teklifindeki maliyet satırı `OfferStoneCost` (`TeklifTasMaliyeti`) olarak yeniden adlandırılmalıdır.
- Katalog taş özellikleri ile tedarikçi maliyet satırı arasında gerekiyorsa referans ilişkisi kurulmalıdır.
- Her iki modelin `adet`, karat, bedel, para birimi, sertifika ve değerli taş doğrulamaları ayrı ve açık olmalıdır.
- Teklif taş bedeli, teklif para birimine bağlı olmalıdır; katalog vitrin bedeli doğrudan fiyat hesabına sızmamalıdır.

### K-012 — Para birimi ve fiyat alanları tutarlı değil

**Kanıt:** `Varyant.sabit_fiyat` TL olarak tanımlanmış. `urunler.UrunTasi.bedel` TL olarak açıklanmış. `TedarikciTeklif` ve fiyatlama taş modeli para birimi tutuyor. `MetalKuru` TL/gr, `DovizKuru` döviz/TL tutuyor. Ancak hesap fonksiyonu para birimi dönüşümü yapmıyor ve sonuç para birimini taşımıyor.

**Risk:** USD/EUR tekliflerin TL fiyatla karışması, taş bedelinin yanlış kurla çevrilmesi veya farklı para birimlerinin toplanması mümkün.

**Karar:**
- Tüm parasal alanlar açık `currency`/ISO 4217 kodu taşımalıdır.
- Para birimleri arası dönüşüm yalnızca merkezi `CurrencyConversionService` üzerinden yapılmalıdır.
- Kur kaynağı, kur zamanı, kur tipi (alış/satış/efektif/platform) ve kullanılan kur değeri quote snapshot'ına yazılmalıdır.
- Aynı hesapta farklı para birimleri doğrudan toplanmamalıdır.
- Hassasiyet ve yuvarlama politikası para birimine göre merkezi tanımlanmalıdır.

### K-013 — Fiyat logu denetlenebilir fiyat snapshot'ı için yetersiz

**Kanıt:** `PriceCalculationLog` sözleşme, kalem, varyant, gram, milyem, saf birim fiyat, kur ve bazı çıktı alanlarını tutuyor; ancak marj tipi/değeri, teklif referansı/versiyonu, satış kanalı, taş satırlarının snapshot'ı, ek bedel, servis bedeli ve tüm yuvarlama/para birimi bağlamı eksik.

**Risk:** Bir sipariş fiyatının geçmişte neden o tutarda olduğu eksiksiz yeniden üretilemez.

**Karar:**
- `PriceCalculationLog` teknik olay/audit kaydı olarak kalabilir.
- Ticari fiyatın esas kaydı ayrı ve değişmez `PriceQuote` snapshot'ı olmalıdır.
- Quote içinde tüm girdiler ve kalemler JSON snapshot + sorgulanabilir normalize alanlarla saklanmalıdır.
- Quote sonradan update edilmemeli; düzeltme yeni quote üretmelidir.

### K-014 — Ürün görseli ve stüdyo çekimi yönetimi eksik

**Kanıt:** `Kategori` modelinde `ImageField` var. `Urun` ve `Varyant` üzerinde ürün fotoğrafı/video/çekim seti modeli yok. Settings'te `MEDIA_ROOT` ve `MEDIA_URL` görünmüyor.

**Risk:** Kuyumbank'ın ürün stüdyo çekimi, görsel onayı, farklı açı, video, varyant görseli ve CDN ihtiyacı veri modelinde karşılanmıyor.

**Karar:**
- `ProductMedia` modeli eklenmelidir.
- Medya; ürün veya varyanta bağlanabilmeli, tür (image/video/360), sıra, kapak, açı, çözünürlük, alt metin, onay durumu, çekim oturumu ve storage key taşımalıdır.
- Dosya binary içeriği veritabanında tutulmamalı; object storage + CDN kullanılmalıdır.
- Yüklenen dosyada MIME, boyut, uzantı ve zararlı içerik kontrolü yapılmalıdır.
- Ürün yayına alınmadan önce gerekli görsel seti kuralı uygulanmalıdır.

### K-015 — SEO metinlerinde örnek marka sabitlenmiş

**Kanıt:** `Kategori.save()` ve `Urun.save()` otomatik SEO metninde `Örnek Kuyumculuk` ifadesi ve sabit pazarlama metinleri üretiyor.

**Risk:** Gerçek marka kimliği olmayan, ürün/firma bağlamına uymayan ve merkezi yönetilemeyen içerik oluşur.

**Karar:**
- Marka adı ve SEO şablonları ayar/CMS üzerinden yönetilmelidir.
- Model `save()` içinde pazarlama metni üretmemelidir.
- SEO alanları boşsa yalnızca güvenli teknik fallback uygulanmalı; içerik üretimi ayrı içerik servisi veya admin editörü üzerinden yapılmalıdır.
- Şablon metinleri `Örnek Kuyumculuk` ile bırakılmamalıdır.

### K-016 — Kategori ağacı doğrulaması alt ağaç derinliğini garanti etmiyor

**Kanıt:** `Kategori.clean()` yeni/taşınan kategorinin üst zincirine bakarak kendi derinliğini kontrol ediyor. Bir üst kategorinin altında zaten alt kategoriler varken üst kategoriyi daha derin bir seviyeye taşımak, alt ağacın toplam derinliğini 3'ü aşırabilir. `save()` `full_clean()` çağırmıyor; DB'de de derinlik constraint'i yok.

**Risk:** Kategori ağacı 3 seviye sınırını aşabilir.

**Karar:**
- Kategori taşıma servisi yazılmalıdır.
- Servis, taşınacak düğümün en derin alt dalını da hesaplayarak `yeni_üst_derinliği + alt_ağaç_derinliği <= 3` kuralını uygulamalıdır.
- Kategori ağacı güncellemesi transaction içinde yapılmalıdır.
- Ürün kullanılan kategorilerde silme yerine pasifleştirme tercih edilmelidir.
- `slug` çakışmasında otomatik benzersiz slug üretimi yapılmalıdır.

### K-017 — Model doğrulaması tutarsız uygulanıyor

**Kanıt:** Bazı modeller `save()` içinde `full_clean()` çağırıyor (`FiyatSozlesmesi`, `FiyatSozlesmesiKalemi`); bazıları çağırmıyor (`Urun`, `Kategori`, `Varyant`, `OlcuDegeri`, `MetalKuru`). `clean()` metodu tek başına `objects.create()` veya `save()` çağrısında otomatik çalışmaz.

**Risk:** Admin formu, shell, management command, API ve toplu import farklı doğrulama davranışı üretebilir. Model `clean()` kuralları DB seviyesinde garanti değildir.

**Karar:**
- Doğrulama üç katmana ayrılmalıdır:
  1. Serializer/form: kullanıcıya anlaşılır hata.
  2. Domain service: iş akışı ve çapraz model doğrulaması.
  3. DB constraint: mümkün olan tüm yapısal invariant'lar.
- `save()` içine her yerde körlemesine `full_clean()` eklenmemelidir; toplu işlemler ve performans düşünülmelidir.
- İş kuralı servis dışında atlanabiliyorsa DB constraint veya kontrollü repository/service sınırıyla engellenmelidir.
- Kritik alanlarda `QuerySet.update()` ile iş kuralı atlama kapısı bırakılmamalıdır. Durum güncellemeleri yalnızca servis içinde ve audit kaydıyla yapılmalıdır.

### K-018 — `FirmaAdresi` ve `FirmaBankaHesabi` veri kuralları eksik

**Kanıt:** Firma adreslerinde varsayılan adres tekilliği yok. Banka IBAN alanında normalizasyon, doğrulama ve firma bazlı tekillik görünmüyor.

**Risk:** Bir firmada birden fazla varsayılan fatura/sevk adresi olabilir; IBAN hatalı veya tekrar girilmiş olabilir.

**Karar:**
- Varsayılan adres tekilliği `firma + adres tipi` kapsamında sağlanmalıdır.
- IBAN normalize edilerek (boşluksuz, büyük harf) saklanmalı; checksum doğrulaması yapılmalıdır.
- Aynı firmanın aynı IBAN'ı ikinci kez eklenememelidir.
- Banka hesap bilgileri yalnızca finans rolü ve platform finans yetkisi tarafından görüntülenmelidir.
- IBAN API response'larında ihtiyaca göre maskelenmelidir.

### K-019 — Kur verisinin kaynağı ve geçerlilik politikası eksik

**Kanıt:** `MetalKuru` ve `DovizKuru` manuel/API/WebSocket kaynak alanı tutuyor; ancak veri sağlayıcı kimliği, kaynak referansı, alınma zamanı, kalite/geçerlilik süresi, gecikme ve başarısızlık durumu modeli görünmüyor.

**Risk:** Eski veya hatalı kurla fiyat gösterilebilir. Aynı zaman damgasında kayıt çakışması operasyonu durdurabilir.

**Karar:**
- `RateProvider`, `RateObservation` veya eşdeğer bir kur alma katmanı kurulmalıdır.
- `zaman` (piyasa zamanı) ile `alınma_zamanı` (sisteme geliş) ayrı tutulmalıdır.
- Kurun geçerlilik süresi ve maksimum veri gecikmesi yapılandırılmalıdır.
- Güncel kur yoksa fiyatlama “son bilinen kur” ile sessizce devam etmemeli; açık uyarı veya fiyat üretmeme davranışı uygulanmalıdır.
- Manuel kur girişi kullanıcı, neden ve onay bilgisiyle audit edilmelidir.

### K-020 — Test kapsamı kritik iş kurallarını kapsamıyor

**Kanıt:** Ürün/varyant ve temel fiyat hesaplama testleri var. Firma/rol yetkileri, tenant izolasyonu, teklif sahipliği, sözleşme çakışması, fiyat snapshot, stok rezervasyonu ve sipariş akışına ilişkin testler yok.

**Risk:** En önemli ticari ve güvenlik kuralları regresyonla bozulabilir.

**Karar:** Bölüm 12'deki kabul testleri tamamlanmadan ilgili modül “Done” sayılmamalıdır.

## P2 — Kalite ve sürdürülebilirlik

### K-021 — Admin tek yönetim arayüzü gibi kullanılıyor

Admin ilk veri yönetimi için uygundur; ancak operasyon iş akışlarının tamamı admin action'larına bağlanmamalıdır. Admin, API ile aynı domain servislerini kullanan bir backoffice arayüzü olarak kalmalıdır.

### K-022 — Audit trail eksik

Ürün onayı, fiyat sözleşmesi, kur değişimi, kullanıcı rolü, banka hesabı, teklif, sipariş ve finans hareketleri için kim/ne zaman/önceki değer/yeni değer/neden kaydı yok. `PriceCalculationLog` genel audit sisteminin yerine geçmez.

### K-023 — Soft delete ve pasifleştirme politikası standart değil

Ticari geçmişi olan ürün, teklif, firma ve sözleşmeler fiziksel olarak silinmemelidir. İşlem geçmişi referansları korunmalı; pasifleştirme, arşivleme ve iptal durumları tanımlanmalıdır.

### K-024 — Kurulum ve dağıtım dokümantasyonu yok

README, `.env.example`, Docker/compose, health check, CI, migration prosedürü, yedekleme/geri yükleme, log ve izleme tanımları ZIP'te bulunmuyor. Bunlar geliştirme tamamlanmadan eklenmelidir.

---

# 4. Hedef ürün kapsamı ve iş modülleri

Aşağıdaki modüller tek bir Django projesinde **modüler monolit** olarak geliştirilmelidir. İlk sürümde mikroservis mimarisi önerilmez. İş kuralları henüz olgunlaşmamışken mikroservis, dağıtık transaction ve operasyon maliyeti getirir.

| Modül | İş amacı | Öncelik |
|---|---|---|
| Kimlik ve firma | Kullanıcı, firma, rol, davet, onay, erişim | P0 |
| Katalog | Ürün, varyant, kategori, özellik, medya | P0 |
| Tedarik ve teklif | Tedarikçi teklifleri, termin, stok, teklif onayı | P0 |
| Fiyatlama | Metal/döviz kuru, sözleşme, maliyet, servis, marj, fiyat kilidi | P0 |
| B2B RFQ | Alıcının ürün/özel üretim talebi ve platform teklif süreci | P1 |
| Sipariş | Sepet, sipariş, onay, iptal, durum takibi | P1 |
| Stok | Stok hareketi, rezervasyon, serbest bırakma | P1 |
| Kalite kontrol | Kontrol listesi, tutanak, kusur, fotoğraf, karar | P1 |
| Lojistik | Paketleme, sevkiyat, takip, teslimat ve iade | P1 |
| Finans | Tahsilat, ödeme, komisyon/servis, tedarikçi hak edişi | P1 |
| Bildirim | E-posta, SMS, panel içi bildirim | P1 |
| Raporlama | Operasyon, satış, kârlılık, tedarikçi performansı | P2 |
| B2C | Perakende vitrin, tüketici sepeti, ödeme ve iade | P2 |
| Entegrasyon | SAP B1/ERP, muhasebe, kargo, ödeme sağlayıcıları | P2 |

## 4.1 İlk sürüm sınırı

İlk canlı sürümün amacı, bütün ticari senaryoları aynı anda çözmek değil; B2B katalog → tedarikçi teklif → fiyat üretimi → RFQ/sipariş → platform operasyonu → kalite/sevkiyat → finans kaydı zincirini güvenilir biçimde çalıştırmaktır.

İlk sürümde:
- B2B alıcı ve tedarikçi panelleri.
- Platform backoffice.
- Ürün kataloğu ve varyantlar.
- Tedarikçi teklifleri.
- Sözleşme tabanlı fiyatlama ve quote snapshot.
- RFQ ve sipariş.
- Stok rezervasyonu.
- Kalite kontrol ve sevkiyat durumları.
- Temel finans hareketleri ve raporlar.

B2C, gelişmiş kampanya, pazaryeri ve harici entegrasyonlar bu zincir doğrulanmadan ana geliştirme kapsamına alınmamalıdır.

---

# 5. Hedef domain modeli

## 5.1 Kimlik, firma ve rol

### Firma

Önerilen ana alanlar:

- `id`
- `firma_kodu` (benzersiz, değişmez)
- `ad`, `unvan`
- `vergi_no`, `vergi_dairesi`
- `telefon`, `eposta`
- `firma_tipi` veya mevcut bayrakların normalize edilmiş karşılığı
- `onay_durumu`
- `aktif`
- `olusturma_zamani`, `guncelleme_zamani`

Alıcı ve tedarikçi aynı firma olabilir mi sorusu veri modelinde desteklenebilir; ancak her firma rolü ayrı yetki setiyle doğrulanmalıdır. Platform firması tek olmalı ve DB constraint ile korunmalıdır.

### Kullanıcı

- Her kullanıcı tam olarak bir firmaya bağlıdır.
- Kullanıcının tek bir aktif iş rolü vardır.
- Kullanıcı firma değiştirdiğinde eski işlemlerin sahipliği değişmez; yalnızca kullanıcının güncel erişim kapsamı değişir.
- Firma değişikliği yalnızca platform yetkisiyle, gerekçe ve audit kaydıyla yapılır.
- Pasif firma kullanıcısı giriş yapamaz veya iş işlemi gerçekleştiremez.
- Kullanıcı kapatıldığında geçmiş sipariş ve finans kayıtları silinmez.

### Rol ve izin modeli

Roller başlangıçta:

**Platform**
- `platform_super`
- `platform_admin`
- `platform_ops`
- `platform_finance`
- `platform_catalog`
- `platform_quality`
- `platform_logistics`
- `platform_support`

**Alıcı**
- `alici_yonetici`
- `alici_satinalmaci`
- `alici_onaylayici`
- `alici_finans`
- `alici_denetci`

**Tedarikçi**
- `tedarikci_sahip`
- `tedarikci_yonetici`
- `tedarikci_satis`
- `tedarikci_depo`
- `tedarikci_finans`

Mevcut rollerin bir kısmı korunabilir. Ancak yalnızca rol kodu ile tüm yetki kararları verilmemelidir. Permission kodları örnekleri:

- `catalog.product.create`
- `catalog.product.update_own`
- `catalog.product.submit_for_review`
- `catalog.product.approve`
- `offer.create_own`
- `offer.update_own`
- `offer.submit`
- `pricing.quote.view_buyer`
- `pricing.contract.manage`
- `order.create`
- `order.approve`
- `order.cancel`
- `inventory.reserve`
- `quality.inspect`
- `shipment.manage`
- `finance.receivable.view`
- `finance.payable.view`
- `firm.user.manage`

Rol → permission matrisi backend kodunda ve testlerde açıkça tanımlanmalıdır.

## 5.2 Katalog ürünü ve tedarikçi teklifi ayrımı

Bu ayrım projenin en önemli veri modeli kararıdır.

### CatalogProduct (platform kataloğu)

Müşterinin gördüğü ürün modeli. Tedarikçi maliyeti ve tedarikçi kimliği burada tutulmaz.

Örnek alanlar:
- `id`, `platform_code`, `name`, `description`
- `category_id`
- `metal_id`, `purity_id`
- `pricing_type`
- `supply_type`
- `measurement_type`
- `color_axis`
- vitrin özellikleri
- `publication_status`
- `approval_status`
- `created_by`, `approved_by`
- `created_at`, `updated_at`

### ProductVariant

Satılabilir ürün konfigürasyonu:
- `product_id`
- `sku`
- `color_id`
- `size_id`
- `gross_weight`
- `net_weight` (gerekiyorsa)
- `fixed_price` (sabit fiyatlı ürünse)
- `active`

Varyantın benzersizliği ürün + renk + ölçü eksenlerine göre sağlanmalıdır. Eksensiz ürün tek varyantla temsil edilmelidir.

### SupplierOffer (TedarikçiTeklif)

Tedarikçinin aynı katalog varyantını hangi koşulla sağlayacağını temsil eder:

- `id`
- `supplier_company_id`
- `variant_id`
- `supplier_sku`
- `pricing_model`
- `quoted_weight`
- `weight_tolerance`
- `unit_price`
- `currency`
- `workmanship_override`
- `supply_type`
- `available_quantity`
- `lead_time_days`
- `priority`
- `status`
- `valid_from`, `valid_until`
- `version`
- `approved_by`, `approved_at`

Kısıtlar:
- Teklif sahibi firma `tedarikci_mi=True` olmalıdır.
- Teklif, kendi firmasına ait olmalıdır.
- Aynı firma + varyant + tedarikçi SKU kombinasyonu için çakışan aktif teklif oluşmamalıdır.
- Alıcı API'si bu modelin tedarikçi kimliği ve maliyet alanlarını doğrudan görmemelidir.
- Teklif değişikliği yeni versiyon üretmeli; geçmiş sipariş teklif snapshot'ı korunmalıdır.

## 5.3 Kategori ve referans tabloları

Mevcut kategori ve referans tabloları korunabilir. Ancak:

- Kategori derinliği en fazla 3 olmalıdır; taşıma servisi alt ağacı da kontrol etmelidir.
- Kategori fiyat grubu mirası tek bir servis/selector üzerinden çözülmelidir.
- `dahili=True` kategoriler public katalog sorgularında hiçbir koşulda dönmemelidir.
- Pasif kategoriye yeni ürün bağlanmamalıdır.
- Slug otomatik üretimi benzersiz olmalıdır.
- Referans tanımlarında kod tekil, pasif kayıtlar geçmiş ilişkilerde korunabilir olmalıdır.

## 5.4 Fiyatlama domain'i

Fiyatlama en az şu kavramlara ayrılmalıdır:

1. `MetalRate`: metalin saf gram fiyatı, kaynak ve zaman.
2. `CurrencyRate`: döviz dönüşüm kuru, kaynak ve zaman.
3. `PricingContract`: firma/kanal/tip/tarih kapsamlı sözleşme.
4. `PricingRule`: metal/ayar/fiyat grubu/kanal kapsamlı kural.
5. `SupplierOffer`: tedarikçi alış/tedarik fiyatı.
6. `PriceQuote`: alıcıya sunulan teklifin değişmez başlığı.
7. `PriceQuoteLine`: fiyatın kalem bazlı dökümü.
8. `PriceLock`: siparişe bağlanmış fiyatın geçerlilik/ kilit bilgisi.

### Fiyat hesaplama temel formülü

Mevcut kodun desteklediği metal bedeli formülü korunabilir:

`metal_bedeli = gram × milyem × saf_birim_fiyat`

Mevcut marj tipleri:
- `YUZDE`
- `TL_GR`
- `TL_PARCA`

Mevcut kodda yüzde marj tabanı `iscilik_dahil_mi` ile seçiliyor. Bu davranış bir sözleşme parametresi olarak korunabilir.

Hedef toplam fiyat, yapılandırılmış kalemlerden oluşmalıdır:

`toplam = metal + işçilik + taş + ek_bedel + platform_servis + kanal_marjı + vergiler`

Bu formüldeki vergi ve ticari bedellerin hangi aşamada uygulanacağı hukuki/mali uzman tarafından onaylanmalıdır. Kodda oran sabitlenmemelidir.

### Fiyatlama işlem sırası

1. Alıcı firma ve satış kanalı doğrulanır.
2. Ürün ve varyantın yayında olduğu kontrol edilir.
3. Aktif tedarikçi teklifleri bulunur.
4. Tedarikçi teklifinin geçerliliği, stok/termin ve onay durumu kontrol edilir.
5. Metal ve döviz kurları seçilir; maksimum veri gecikmesi kontrol edilir.
6. İlgili fiyat sözleşmesi ve kalemleri deterministik çözülür.
7. Maliyet ve alıcı fiyatı kalem kalem hesaplanır.
8. `PriceQuote` snapshot yazılır.
9. Quote geçerlilik süresi döndürülür.
10. Sipariş anında quote kilitlenir ve sipariş satırına kopyalanır.

Fiyat motoru doğrudan model `save()` içinde çalıştırılmamalıdır. Tek bir domain servisinden çağrılmalıdır.

## 5.5 Sipariş, stok, kalite ve lojistik

Önerilen ana tablolar:

| Model | Sorumluluk |
|---|---|
| `Cart`, `CartLine` | Alıcının geçici sepeti |
| `RFQ`, `RFQLine`, `RFQMessage` | Özel üretim veya toplu alım talebi |
| `Order`, `OrderLine` | Onaylanmış ticari sipariş |
| `OrderStatusHistory` | Sipariş durum geçmişi |
| `StockReservation` | Süreli stok rezervasyonu |
| `InventoryMovement` | Stok giriş/çıkış/rezervasyon/iadeler |
| `QualityInspection`, `InspectionLine`, `InspectionMedia` | Kalite kontrol ve tutanak |
| `Shipment`, `ShipmentPackage`, `ShipmentEvent` | Paket, sevkiyat ve takip |
| `ReturnRequest`, `ReturnLine` | İade/inceleme |
| `Payment`, `PaymentAllocation` | Tahsilat ve siparişe dağıtım |
| `SupplierSettlement` | Tedarikçi hak edişi |
| `LedgerEntry` | Finansal hareket kaydı |

### Sipariş durumları

Önerilen durum makinesi:

`DRAFT → PENDING_APPROVAL → CONFIRMED → SUPPLIER_PROCESSING → QUALITY_CONTROL → PACKING → SHIPPED → DELIVERED`

Yan akışlar:
- `REJECTED`
- `CANCEL_REQUESTED`
- `CANCELLED`
- `QUALITY_FAILED`
- `RETURN_REQUESTED`
- `RETURNED`
- `REFUND_PENDING`
- `REFUNDED`

Durumlar serbest metin olarak değiştirilemez. Her geçiş bir servis tarafından, rol kontrolü, geçiş önkoşulu ve audit kaydıyla yapılmalıdır.

### Stok davranışı

- Sepete ekleme stok düşürmez.
- Checkout sırasında stok rezervasyonu yapılır.
- Rezervasyon TTL dolarsa serbest bırakılır.
- Sipariş kesinleşince rezervasyon satışa dönüşür.
- İptal/iade hareketleri ayrı ledger hareketi oluşturur.
- Stok sayısı doğrudan elle güncellenmez; düzeltme hareketi girilir.
- Siparişe özel üretimde fiziksel stok yerine kapasite/termin rezervasyonu tutulabilir.

## 5.6 Kalite kontrol ve inceleme tutanağı

Kalite kontrol platform operasyonunun sorumluluğunda olmalıdır.

`QualityInspection`:
- sipariş/sipariş satırı
- kontrol tipi
- kontrol eden kullanıcı
- kontrol tarihi
- sonuç (`PASSED`, `FAILED`, `CONDITIONAL`)
- genel not
- imza/ek dosya referansları

`InspectionLine`:
- kontrol kriteri
- beklenen değer
- ölçülen değer
- sonuç
- hata kodu
- açıklama

`InspectionMedia`:
- fotoğraf/video
- çekim zamanı
- dosya hash'i
- ilgili kontrol satırı

Tutanak sonradan sessizce değiştirilmemelidir. Düzeltme yeni revizyon olarak kaydedilmeli; önceki tutanak korunmalıdır.

---

# 6. API şartnamesi

## 6.1 Genel standart

- Base path: `/api/v1/`
- JSON request/response.
- UTF-8.
- Tarihler ISO-8601 ve timezone bilgili.
- Parasal değerler JSON number yerine tercihen string decimal olarak taşınmalı (`"12500.50"`); backend `Decimal` kullanmalı.
- Liste endpoint'leri sayfalı olmalı.
- Filtre/sıralama whitelist üzerinden yapılmalı.
- Hata cevapları tek formatta olmalı.
- İdempotent olması gereken komutlarda `Idempotency-Key` desteklenmeli.
- Her cevapta hassas alanlar rol ve bağlama göre filtrelenmeli.

### Standart hata biçimi

```json
{
  "error": {
    "code": "OFFER_NOT_AVAILABLE",
    "message": "Seçilen teklif bu işlem için uygun değil.",
    "details": {
      "offer_id": ["Teklif pasif veya süresi dolmuş."]
    },
    "trace_id": "..."
  }
}
```

HTTP kodları:
- `400`: alan/iş kuralı doğrulama hatası
- `401`: oturum yok/geçersiz
- `403`: yetki yok
- `404`: nesne yok veya kullanıcı kapsamı dışında
- `409`: durum çakışması, stok/fiyat versiyonu çakışması
- `422`: iş kuralı ihlali (tercihe göre 400 standardına da indirilebilir; projede tek karar kullanılmalı)
- `429`: rate limit
- `500`: beklenmeyen hata; trace id ile loglanmalı

## 6.2 Kimlik ve firma endpoint'leri

| Method | Endpoint | Yetki | İşlev |
|---|---|---|---|
| POST | `/auth/login` | Public | Oturum aç |
| POST | `/auth/logout` | Auth | Oturumu kapat |
| POST | `/auth/refresh` | Auth/token | Token yenileme; token stratejisi seçilirse |
| GET | `/auth/me` | Auth | Kullanıcı, firma, rol ve izinleri döndür |
| GET | `/companies/me` | Auth | Kendi firmasını göster |
| PATCH | `/companies/me` | Firma yöneticisi | İzin verilen firma profil alanlarını güncelle |
| GET | `/companies/me/users` | Firma yöneticisi | Kendi firma kullanıcıları |
| POST | `/companies/me/users/invitations` | Firma yöneticisi | Kullanıcı daveti |
| PATCH | `/companies/me/users/{id}` | Firma yöneticisi | Kendi firma kullanıcısını güncelle |
| POST | `/platform/companies/{id}/approve` | Platform firma onay | Firma onayı |

Kullanıcı oluşturma isteği firma ID'sini serbestçe belirleyememelidir. Firma yöneticisi kendi firmasına kullanıcı ekler; platform personeli ayrı platform endpoint'i kullanır.

## 6.3 Katalog endpoint'leri

| Method | Endpoint | Yetki | İşlev |
|---|---|---|---|
| GET | `/catalog/categories` | Auth/public policy | Aktif ve dahili olmayan kategoriler |
| GET | `/catalog/products` | Alıcı/kanal | Yayındaki ürünler |
| GET | `/catalog/products/{id}` | Alıcı/kanal | Ürün detayı |
| POST | `/supplier/products` | Tedarikçi katalog yetkisi | Ürün taslağı oluştur |
| PATCH | `/supplier/products/{id}` | Ürünün tedarikçisi | Taslağı güncelle |
| POST | `/supplier/products/{id}/submit` | Tedarikçi | Onaya gönder |
| POST | `/platform/products/{id}/approve` | Platform katalog | Onayla |
| POST | `/platform/products/{id}/reject` | Platform katalog | Gerekçeli reddet |
| POST | `/platform/products/{id}/publish` | Platform katalog | Kanalda yayına al |
| POST | `/platform/products/{id}/unpublish` | Platform katalog | Yayından kaldır |
| POST | `/supplier/products/{id}/media` | Ürünün tedarikçisi | Medya ekle |

Public katalog cevabında tedarikçi firma ID/adı, tedarikçi SKU, maliyet, stok kaynağı veya iç not dönülmez.

## 6.4 Tedarikçi teklif endpoint'leri

| Method | Endpoint | Yetki | İşlev |
|---|---|---|---|
| GET | `/supplier/offers` | Tedarikçi | Kendi teklifleri |
| POST | `/supplier/offers` | Tedarikçi satış/yönetici | Teklif oluştur |
| GET | `/supplier/offers/{id}` | Teklif sahibi | Kendi teklif detayı |
| PATCH | `/supplier/offers/{id}` | Teklif sahibi | Taslak teklifi güncelle |
| POST | `/supplier/offers/{id}/submit` | Tedarikçi | Onaya gönder |
| POST | `/platform/offers/{id}/approve` | Platform satın alma/operasyon | Teklifi onayla |
| POST | `/platform/offers/{id}/reject` | Platform satın alma/operasyon | Gerekçeli reddet |
| POST | `/platform/offers/{id}/deactivate` | Platform | Teklifi pasifleştir |

Alıcı tarafında teklif listesi veya detay endpoint'i açılmamalıdır. Alıcıya yalnızca platform tarafından oluşturulmuş `PriceQuote` gösterilmelidir.

## 6.5 Fiyat endpoint'leri

| Method | Endpoint | Yetki | İşlev |
|---|---|---|---|
| POST | `/pricing/quotes` | Alıcı | Varyant için fiyat teklifi oluştur |
| GET | `/pricing/quotes/{id}` | Quote sahibi alıcı / platform | Quote detayı |
| POST | `/pricing/quotes/{id}/lock` | Sipariş oluşturma akışı | Quote'u siparişe kilitle |
| GET | `/platform/pricing/contracts` | Platform finans/pricing | Sözleşme listesi |
| POST | `/platform/pricing/contracts` | Platform pricing | Taslak sözleşme |
| POST | `/platform/pricing/contracts/{id}/activate` | Platform pricing onay | Aktifleştir |
| GET | `/platform/rates/metals` | Platform pricing | Metal kurları |
| POST | `/platform/rates/metals` | Yetkili platform | Manuel kur girişi |
| GET | `/platform/rates/currencies` | Platform pricing | Döviz kurları |
| POST | `/platform/rates/currencies` | Yetkili platform | Manuel kur girişi |

Alıcı quote cevabı örneği:

```json
{
  "id": "quote_uuid",
  "currency": "TRY",
  "valid_until": "2026-11-08T12:30:00+03:00",
  "lines": [
    {"code": "PRODUCT", "label": "Ürün bedeli", "amount": "24500.00"},
    {"code": "SERVICE", "label": "Platform hizmet bedeli", "amount": "750.00"}
  ],
  "total": "25250.00"
}
```

Alıcı cevabında alış fiyatı, tedarikçi kimliği, tedarikçi teklifi ID'si, iç marj oranı ve maliyet kırılımı bulunmaz. Alıcıya gösterilecek fiyat kalemlerinin isimleri ürün/iş kararıyla belirlenir; gizli maliyet kırılımı API'de bulunmamalıdır.

## 6.6 RFQ ve sipariş endpoint'leri

| Method | Endpoint | Yetki | İşlev |
|---|---|---|---|
| POST | `/buyer/rfqs` | Alıcı satın almacı | Talep oluştur |
| GET | `/buyer/rfqs` | Alıcı | Kendi talepleri |
| GET | `/buyer/rfqs/{id}` | Talep sahibi | Talep detayı |
| POST | `/buyer/rfqs/{id}/messages` | Talep sahibi | Talep mesajı |
| POST | `/buyer/orders` | Alıcı satın almacı | Quote snapshot ile sipariş oluştur |
| GET | `/buyer/orders` | Alıcı | Kendi siparişleri |
| GET | `/buyer/orders/{id}` | Alıcı | Sipariş detayı |
| POST | `/buyer/orders/{id}/approve` | Alıcı onaylayıcı | Siparişi onayla |
| POST | `/buyer/orders/{id}/cancel-request` | Alıcı | İptal talebi |
| GET | `/supplier/orders` | Tedarikçi | Kendisine atanmış iş emirleri |
| POST | `/supplier/orders/{id}/accept` | Tedarikçi | İş emrini kabul et |
| POST | `/supplier/orders/{id}/ready` | Tedarikçi | Hazır/üretim tamamlandı |
| GET | `/platform/orders` | Platform operasyon | Tüm siparişler |
| POST | `/platform/orders/{id}/status` | Platform operasyon | Yetkili durum geçişi |

Tedarikçi ekranına alıcı firma adı ve iletişim bilgisi açılmamalıdır; lojistik için gerekli teslimat bilgisi platform kontrollü ve yalnızca görev bazlı paylaşılmalıdır. Alıcıya da tedarikçi kimliği açılmamalıdır.

---

# 7. Yetki matrisi

| İşlem | Platform Super | Platform Ops | Platform Catalog | Platform Finance | Alıcı Yönetici | Alıcı Satınalma | Alıcı Onaylayıcı | Tedarikçi Sahip | Tedarikçi Satış | Tedarikçi Depo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Firma onayı | Evet | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır |
| Kullanıcı/rol yönetimi | Evet | Sınırlı | Hayır | Hayır | Kendi firma | Hayır | Hayır | Kendi firma | Hayır | Hayır |
| Ürün oluşturma | Evet | Sınırlı | Evet | Hayır | Hayır | Hayır | Hayır | Kendi firma | Yetkiliyse | Hayır |
| Ürün onayı/yayın | Evet | Hayır | Evet | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır |
| Tedarikçi teklif girişi | Evet | Sınırlı | Hayır | Hayır | Hayır | Hayır | Hayır | Kendi firma | Kendi firma | Hayır |
| Teklif onayı | Evet | Evet | Sınırlı | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır |
| Fiyat sözleşmesi | Evet | Hayır | Hayır | Evet | Hayır | Hayır | Hayır | Hayır | Hayır | Hayır |
| Fiyat görme | Tümü | Operasyon kapsamı | Katalog kapsamı | Maliyet kapsamı | Kendi satış fiyatı | Kendi satış fiyatı | Kendi satış fiyatı | Kendi teklif maliyeti | Kendi teklif maliyeti | Gerekmez |
| Sipariş oluşturma | Evet | Evet | Hayır | Hayır | Evet | Evet | Hayır | Hayır | Hayır | Hayır |
| Sipariş onayı | Evet | Evet | Hayır | Hayır | Sınırlı | Hayır | Evet | Hayır | Hayır | Hayır |
| Üretim/tedarik durumu | Evet | Evet | Hayır | Hayır | Görüntüleme | Görüntüleme | Görüntüleme | Kendi işi | Kendi işi | Kendi işi |
| Kalite kontrol | Evet | Evet | Hayır | Hayır | Sonuç görüntüleme | Sonuç görüntüleme | Sonuç görüntüleme | Hayır | Hayır | Hayır |
| Tahsilat/ödeme | Evet | Hayır | Hayır | Evet | Kendi hesapları | Hayır | Görüntüleme | Kendi hak edişi | Hayır | Hayır |

Bu tablo başlangıç matrisi olarak uygulanmalıdır. Her yeni endpoint için permission kodu ve tenant kapsamı test edilmelidir.

---

# 8. Güvenlik, gizlilik ve veri izolasyonu

## 8.1 Temel ilkeler

1. Varsayılan erişim reddedilir.
2. Her endpoint authentication ve permission kontrolü yapar.
3. Her nesne sorgusu tenant scope ile başlar.
4. Kullanıcıdan gelen firma/tedarikçi/alıcı ID'si doğrulanmadan kullanılmaz.
5. Platform erişimi açık permission ile verilir.
6. Alıcı ve tedarikçi karşı tarafın kimliğini ve ticari sırlarını görmez.
7. Finansal ve kişisel veriler rol bazlı maskelenir.
8. Kritik işlem audit log üretir.
9. Hassas işlemlerde idempotency ve transaction kullanılır.
10. Uygulama loglarına parola, token, IBAN'ın tamamı veya kişisel veri yazılmaz.

## 8.2 Zorunlu güvenlik testleri

- Alıcı A, Alıcı B'nin siparişini ID değiştirerek okuyamamalı.
- Tedarikçi A, Tedarikçi B'nin teklifini okuyamamalı.
- Tedarikçi A, başka tedarikçinin varyantına teklif yazamamalı.
- Tedarikçi kullanıcısı platform onay endpoint'ini çağıramamalı.
- Alıcı kullanıcısı alış fiyatı/maliyet/marj alanlarına erişememeli.
- Firma pasifse kullanıcı işlem yapamamalı.
- Firma rolü olmayan kullanıcı oluşturulamamalı.
- `is_superuser` iş rolü kontrolünü atlayarak normal sipariş işlemi yapamamalı.
- Admin ve API aynı domain servislerini kullanmalı.
- Dosya yükleme endpoint'i başka tenant'ın medya dosyasını değiştirememeli.

---

# 9. İş kuralları — geliştiricinin uygulayacağı kesin davranışlar

## 9.1 Firma ve kullanıcı

- Her kullanıcı bir firmaya bağlıdır; `firma_id` boş olamaz.
- Her kullanıcının tek bir iş rolü vardır.
- Rol ile firma tipi uyumlu olmalıdır.
- Platform rolleri yalnızca platform firmasına atanabilir.
- Alıcı rolleri alıcı yetkisi bulunan firmalara atanabilir.
- Tedarikçi rolleri tedarikçi yetkisi bulunan firmalara atanabilir.
- Kullanıcı firma değiştirme işlemi platform onayı ve audit gerektirir.
- Kullanıcı rolü değiştiğinde permission cache/session yenilenir.

## 9.2 Ürün

- Ürün taslak olarak açılır.
- En az bir aktif varyant olmadan onaya gönderilemez.
- Gram bazlı ürünün her aktif varyantında gram pozitif olmalıdır.
- Sabit fiyatlı üründe sabit fiyat pozitif olmalıdır.
- Ürünün kategori, metal/ayar ve varyant eksenleri tutarlı olmalıdır.
- Renk ekseni açık ise her varyantta renk zorunludur.
- Ölçü ekseni açık ise her varyantta doğru ölçü tipi zorunludur.
- Onay bekleyen ürün düzenleme politikası tanımlanmalıdır: varsayılan olarak tedarikçi düzenleme yaparsa onay durumu tekrar taslağa döner.
- Onaylı ürünün fiyat/özellik gibi kritik alanları değişirse yeniden onay gerekir.
- Yayın için onaylı ürün ve en az bir aktif kanal gerekir.
- Ürün silinmez; pasifleştirilir/arşivlenir.

## 9.3 Tedarikçi teklifi

- Teklif yalnızca teklif sahibi tedarikçi tarafından oluşturulur/düzenlenir.
- Teklif onaylanmadan fiyat motorunda kullanılmaz.
- Teklif fiyat modeli alan zorunlulukları DB ve servis seviyesinde doğrulanır.
- Teklifin geçerlilik tarihi ve para birimi zorunludur.
- Teklifin stok ve termin bilgisi güncel tutulur.
- Teklif değişikliği yeni versiyon oluşturur; geçmiş quote/sipariş eski versiyona bağlı kalır.
- Teklif pasif veya süresi dolmuşsa yeni quote üretiminde kullanılamaz.

## 9.4 Fiyat

- Fiyat yalnızca merkezi PricingService üzerinden üretilir.
- Ara hesaplar `Decimal` ile yapılır.
- Ara adımlarda yuvarlama yapılmaz; yalnızca tanımlı final kalemlerinde yuvarlama yapılır.
- Metal kuru, döviz kuru ve sözleşme versiyonu quote'a yazılır.
- Kullanılan teklif versiyonu quote'a yazılır.
- Fiyatın geçerlilik sonu olmalıdır.
- Quote süresi dolduysa sipariş oluşturulamaz; yeni quote alınır.
- Sipariş satırı quote snapshot'ını taşır.
- Sonradan değişen kur/sözleşme eski sipariş fiyatını değiştiremez.
- Fiyat hesaplama belirsizse sistem fiyat üretmez; rastgele ilk kaydı seçmez.

## 9.5 Sipariş

- Sipariş, geçerli quote ve stok/termin uygunluğu doğrulanarak oluşturulur.
- Sipariş oluşturma idempotent olmalıdır.
- Aynı idempotency key ile tekrar istek yeni sipariş yaratmamalıdır.
- Alıcı onayı gereken siparişlerde onay olmadan tedarikçiye iş emri açılmaz.
- Tedarikçiye giden iş emri alıcıyı ifşa etmez.
- Siparişin tüm durum değişiklikleri history tablosuna yazılır.
- İptal, iade ve refund ayrı süreçlerdir; sipariş durumunu doğrudan geriye çekmek yasaktır.

---

# 10. Teknik mimari ve kod organizasyonu

## 10.1 Mimari kararı

**Modüler monolit + domain service + PostgreSQL**.

- Tek deploy edilebilir Django backend.
- Her iş alanı kendi Django app'inde.
- Uygulamalar arası doğrudan model içi iş mantığı yerine servis/API sınırı.
- Domain servisleri transaction sınırını yönetir.
- ORM sorguları selector/repository yardımcılarında toplanabilir.
- Async işler ilk aşamada ihtiyaç duyulan yerde Celery + Redis ile eklenir.
- Dosyalar object storage üzerinde tutulur.
- API şeması OpenAPI ile yayınlanır.

## 10.2 Önerilen uygulama dizilimi

```text
backend/
  config/
    settings/
      base.py
      development.py
      production.py
    urls.py
  apps/
    identity/
      models/
      services/
      selectors/
      api/
    companies/
      models/
      services/
      api/
    catalog/
      models/
      services/
      selectors/
      api/
    sourcing/
      models/
      services/
      api/
    pricing/
      models/
      services/
      selectors/
      api/
    commerce/
      models/
      services/
      api/
    inventory/
      models/
      services/
      api/
    quality/
      models/
      services/
      api/
    fulfillment/
      models/
      services/
      api/
    finance/
      models/
      services/
      api/
    media/
      models/
      services/
      api/
    notifications/
    integrations/
    audit/
    reporting/
  tests/
  manage.py
  requirements/
  .env.example
  README.md
```

Mevcut uygulamaları tek seferde çöpe atmak gerekmiyor. `firmalar` → `companies/identity`, `urunler` → `catalog`, `fiyatlama` → `pricing/sourcing`, `tanimlar` → `catalog/pricing reference` sınırlarına kontrollü taşınabilir. Ancak eski modellerin isimleri korunacak diye hatalı ilişki korunmamalıdır.

## 10.3 Servis sınırları

Örnek servisler:

- `CompanyService.create_company()`
- `UserService.invite_user()`
- `UserRoleService.assign_role()`
- `CatalogService.submit_product_for_review()`
- `CatalogService.approve_product()`
- `OfferService.create_offer()`
- `OfferService.approve_offer()`
- `PricingService.create_quote()`
- `PricingService.resolve_contract_rule()`
- `PricingService.lock_quote()`
- `InventoryService.reserve()`
- `OrderService.create_order()`
- `OrderService.transition_status()`
- `QualityService.complete_inspection()`
- `FulfillmentService.create_shipment()`
- `FinanceService.record_payment()`
- `AuditService.record_event()`

Servis metotları kullanıcı/actor bilgisini zorunlu almalı; tenant ve permission doğrulamasını yapmalı; transaction sınırını belirlemelidir.

## 10.4 Transaction ve eşzamanlılık

Aşağıdaki işlemler transaction içinde yapılmalıdır:

- Kullanıcı rolü/firma atama.
- Ürün onay/yayın geçişi.
- Tedarikçi teklif onayı/versiyonlama.
- Fiyat sözleşmesi aktifleştirme.
- Quote kilitleme.
- Stok rezervasyonu.
- Sipariş oluşturma ve onay.
- Ödeme dağıtımı.
- İade ve stok geri girişi.

Stokta yalnızca `select_for_update()` kullanmak yeterli değildir; doğru satır kilidi, koşullu update ve DB constraint birlikte tasarlanmalıdır. Yarış koşulu testleri PostgreSQL üzerinde yapılmalıdır.

## 10.5 Audit ve outbox

`AuditEvent`:
- actor user
- actor company
- action
- entity type/id
- before/after JSON
- reason
- request/trace id
- IP/device metadata (gizlilik politikası sınırları içinde)
- timestamp

Harici bildirim/entegrasyon için transaction sonrası doğrudan HTTP çağrısı yapılmamalıdır. `OutboxEvent` kaydı transaction içinde oluşturulmalı; worker bu olayı güvenli biçimde tüketmelidir.

---

# 11. Altyapı, ayarlar ve operasyon

## 11.1 Ayarlar

- Secret key ve DB parolası yalnızca environment/secret manager üzerinden alınmalı.
- `.env` Git'e ve ZIP'e girmemeli.
- `DEBUG=False` canlıda zorunlu.
- `ALLOWED_HOSTS` açıkça tanımlanmalı.
- HTTPS, secure cookie, HSTS ve reverse proxy ayarları gerçek altyapıya göre doğrulanmalı.
- `CSRF_TRUSTED_ORIGINS`, CORS ve proxy ayarları deployment topolojisine göre açıkça tanımlanmalı.
- `MEDIA_ROOT`/`MEDIA_URL` veya object storage ayarı eklenmeli.
- `STATIC_ROOT` collectstatic için korunmalı.
- PostgreSQL bağlantı havuzu, statement timeout ve backup politikası tanımlanmalı.
- Loglar yapılandırılmış JSON formatında üretilmeli.
- Sentry veya eşdeğer hata izleme; Prometheus/OpenTelemetry veya eşdeğer metrik/trace altyapısı eklenmeli.

## 11.2 Bağımlılıklar

Mevcut bağımlılıklarda Django ve `django-import-export` görülüyor. API için DRF ve OpenAPI şema aracı eklenmelidir. Asenkron görev ihtiyacı başladığında Celery + Redis eklenmelidir. Bunlar eklenmeden “arka plan işi çalışıyor” varsayımı yapılmamalıdır.

## 11.3 Yedekleme ve kurtarma

- PostgreSQL günlük tam yedek + uygun WAL/PITR politikası.
- Medya dosyaları için object storage versioning/backup.
- Yedek geri yükleme testi düzenli yapılmalı.
- Migration öncesi üretim yedeği alınmalı.
- Geri dönüş planı olmayan yıkıcı migration canlıya alınmamalı.

---

# 12. Test ve kabul kriterleri

Her iş kartı aşağıdaki kriterlerden ilgili olanları sağlamadan tamamlanmış sayılmaz.

## 12.1 Kimlik ve tenant testleri

1. Firma atanmamış normal kullanıcı kaydedilemez.
2. Rol atanmamış normal kullanıcı kaydedilemez.
3. Alıcı rolü tedarikçi firmaya atanamaz.
4. Tedarikçi rolü alıcı olmayan firmaya atanamaz.
5. Platform rolü yalnızca platform firmasına atanabilir.
6. Superuser iş kurallarını atlayarak tenant-owned işlem yapamaz.
7. Kullanıcı başka firmanın kullanıcısını listeleyemez/güncelleyemez.
8. Rol değişikliği grup/permission senkronunu günceller.
9. Firma pasif hale geldiğinde kullanıcı işlemleri engellenir.
10. Yetkisiz kullanıcıya 403 veya kapsam dışı nesne için 404 döner.

## 12.2 Katalog testleri

1. Ürün en az bir aktif varyant olmadan onaya gönderilemez.
2. Ürün tedarikçisi yalnızca kendi ürününü güncelleyebilir.
3. Renk ekseni/ölçü ekseni kombinasyonları doğrulanır.
4. Aynı ürün içinde aynı varyant kombinasyonu ikinci kez oluşturulamaz.
5. Onaysız ürün yayınlanamaz.
6. Ürün onaylayan kullanıcı ve onay zamanı zorunludur.
7. Ürün kanal olmadan aktif yayınlanamaz.
8. Dahili kategori public API'de dönmez.
9. Kategori ağacı derinliği 3'ü geçemez; alt ağaç taşıma testi yapılır.
10. Ürün görseli eksikse yayın kuralı doğru çalışır.

## 12.3 Teklif ve fiyatlama testleri

1. Tedarikçi yalnızca kendi teklifini oluşturabilir.
2. Teklif başka tedarikçinin ürün/varyant ilişkisini kullanamaz.
3. Teklif onaysızken quote üretilemez.
4. Teklif süresi dolunca yeni quote üretilemez.
5. Ayara özel kural genel kuralı ezer.
6. Kanal özel kuralı genel kanal kuralını ezer.
7. Aynı öncelikte çakışan kural varsa fiyat üretimi durur.
8. Aktif sözleşme tarih aralıkları çakışamaz.
9. Metal ve döviz kuru snapshot'a yazılır.
10. Kur eskiyse fiyat üretimi durur veya açıkça tanımlı fallback uygular.
11. Hesaplama `Decimal` ile yapılır.
12. Fiyat snapshot'ı sonradan değiştirilemez.
13. Sözleşme/kur değişince eski quote ve sipariş fiyatı değişmez.
14. Alıcı API'sinde tedarikçi kimliği ve maliyet alanı bulunmaz.
15. Farklı para birimlerinin dönüşümü merkezi servis üzerinden yapılır.

## 12.4 Sipariş ve stok testleri

1. Süresi dolmuş quote ile sipariş oluşturulamaz.
2. Aynı idempotency key ikinci siparişi oluşturmaz.
3. Stok yetersizse rezervasyon başarısız olur.
4. Eşzamanlı iki checkout son birimi iki kez rezerve edemez.
5. Benzersiz parça aynı anda tek siparişe bağlanır.
6. Rezervasyon süresi dolunca stok serbest kalır.
7. Sipariş onaylanmadan tedarikçiye iş emri açılmaz.
8. Sipariş durum geçişi yetkisiz aktör tarafından yapılamaz.
9. İptal/iade stok ve finans hareketlerini doğru oluşturur.
10. Geçmiş sipariş fiyat snapshot'ı değişmez.

## 12.5 Kalite, lojistik ve finans testleri

1. Kalite tutanağı yalnızca yetkili kalite kullanıcısı tarafından tamamlanır.
2. Başarısız kalite kontrol sevkiyata izin vermez.
3. Sevkiyat kaydı sipariş satırlarıyla tutarlı olmalıdır.
4. Teslimat olayı aynı kargo webhook'u tekrar geldiğinde çift işlenmemelidir.
5. Ödeme kaydı idempotent olmalıdır.
6. Ödeme dağıtım toplamı ödeme tutarını aşamaz.
7. Tedarikçi hak edişi sipariş ve iade durumlarıyla tutarlı olmalıdır.
8. Finans hareketleri silinemez; ters kayıt ile düzeltilir.
9. Kullanıcı yalnızca yetkili olduğu finans kayıtlarını görür.

## 12.6 Test seviyesi

- Unit: hesaplama, selector, validator, state machine.
- Integration: PostgreSQL constraint, transaction, servisler arası akış.
- API: authentication, permission, schema ve response.
- Security: tenant/IDOR, hassas veri sızıntısı, rol bypass.
- Concurrency: stok rezervasyonu, quote kilidi, ödeme webhook'u.
- E2E: alıcıdan siparişe, tedarikçiden sevkiyata ve platform kalite kontrolüne tam akış.

SQLite üzerinde geçen test, PostgreSQL'e özgü constraint ve kilit davranışını kanıtlamaz. Kritik integration/concurrency testleri PostgreSQL üzerinde koşmalıdır.

---

# 13. Veri geçişi ve mevcut koddan hedef yapıya geçiş

Mevcut veritabanı silinerek başlanmamalıdır. Önce yedek alınmalı, veri envanteri çıkarılmalı, sonra aşamalı migration uygulanmalıdır.

## 13.1 Geçiş sırası

1. **Güvenlik hazırlığı:** `.env` dışarı çıkarılır, secret'lar döndürülür, `.env.example` eklenir.
2. **Veri denetimi:** `audit_user_assignments` komutu çalıştırılır; firma/rolsüz kullanıcılar raporlanır.
3. **Firma/user düzeltmesi:** Her kullanıcıya firma ve geçerli rol atanır; platform admin platform firmasına bağlanır.
4. **Zorunlu firma FK:** Veri temizlendikten sonra `Kullanici.firma` DB seviyesinde `null=False` yapılır.
5. **Yetki servisi:** Rol atama admin ve API'de tek servis üzerinden yürütülür; permission matrisi seed edilir.
6. **Katalog/teklif ayrımı:** Ürün üzerindeki tedarikçi bağımlılığı kaldırılır veya açıkça yeniden tanımlanır; SupplierOffer ilişkisi kurulur.
7. **Fiyatlama yeniden düzenlemesi:** Kural çakışması düzeltilir, teklif/kur/sözleşme/quote zinciri tamamlanır.
8. **Stok ve sipariş:** Rezervasyon, sipariş snapshot ve durum makinesi eklenir.
9. **Kalite/lojistik/finans:** Modüller sipariş akışına bağlanır.
10. **API ve paneller:** API sözleşmeleri tamamlanır, admin aynı servisleri kullanır.
11. **Test ve pilot:** Gerçek firmalara açılmadan önce test firmalarıyla uçtan uca pilot yapılır.

## 13.2 Veri taşıma kuralları

- Mevcut `Urun.platform_kodu` ve `Varyant.sku` değerleri korunmalıdır.
- Tedarikçi ürün kodu ve platform ürün kodu birbirine karıştırılmamalıdır.
- Eski `Urun.tedarikci` alanı SupplierOffer kayıtlarının ilk kaynağını oluşturmak için kullanılabilir; ancak her kayıt için veri doğrulaması yapılmalıdır.
- Mevcut `Varyant.stok` ve `TedarikciTeklif.stok_adet` değerleri karşılaştırılmalı; hangisinin gerçek stok olduğu iş birimi tarafından belirlenmeden otomatik toplanmamalıdır.
- Eski fiyat logları eksik girdiliyse tam snapshot gibi gösterilmemelidir.
- Fiyat sözleşmesi versiyonları ve tarih aralıkları çakışma raporuna tabi tutulmalıdır.
- Kategori slug çakışmaları migration öncesi çözülmelidir.

---

# 14. Geliştirme planı ve iş paketleri

Aşağıdaki sıra bağımlılıklara göre hazırlanmıştır. Takvim tahmini ekip büyüklüğü, tasarım ve entegrasyon kapsamı bilinmeden verilmemiştir.

| Faz | İş paketi | Teslim çıktısı | Tamamlanma koşulu |
|---|---|---|---|
| 0 | Güvenlik ve repo temizliği | `.env` temizliği, secret rotation, settings ayrımı | Gizli değer yok, kurulum tekrarlanabilir |
| 1 | Firma/kullanıcı/RBAC | Tek firma, tek rol, permission matrisi, tenant scope | P0 kimlik testleri geçer |
| 2 | Katalog | Ürün, varyant, kategori, medya, onay | Katalog testleri geçer |
| 3 | Tedarikçi teklif | Çoklu tedarikçi teklifleri, versiyon, onay | Teklif sahipliği testleri geçer |
| 4 | Fiyatlama | Kur, sözleşme, resolver, quote snapshot, lock | Fiyatlama testleri geçer |
| 5 | B2B ticaret | RFQ, sepet, sipariş, onay | Sipariş E2E geçer |
| 6 | Stok ve operasyon | Rezervasyon, üretim, kalite, sevkiyat | Concurrency ve operasyon testleri geçer |
| 7 | Finans | Tahsilat, hak ediş, ledger, mutabakat | Finans testleri ve uzman onayı tamam |
| 8 | Bildirim/raporlama | Outbox, bildirim, dashboard | Tekrarlı olaylar güvenli işlenir |
| 9 | Pilot ve canlıya hazırlık | İzleme, backup, runbook, UAT | Pilot kabul ve rollback planı hazır |
| 10 | B2C/entegrasyon | Perakende, SAP/ERP, ödeme/kargo | Ayrı kapsam ve kabul kriterleri |

## 14.1 İlk sprint için somut görevler

1. `.env` dosyasını repodan çıkar; secret rotation yap.
2. `requirements.txt` dosyasını UTF-8'e çevir ve kilitli bağımlılık yönetimi kur.
3. Django settings'i base/development/production olarak ayır.
4. DRF ve OpenAPI bağımlılıklarını ekle.
5. Kullanıcı firma alanını zorunlu hale getirecek veri migration planını yaz.
6. Superuser bypass'ını normal iş yetkisinden kaldır.
7. `assign_user_role()` servisini admin kayıt akışına bağla.
8. Permission seed ve rol matrisi testlerini yaz.
9. `onaya_gonder()` içine tedarikçi sahipliği ve rol doğrulaması ekle.
10. API tenant-scope altyapısını kur; örnek firma ve kullanıcı fixture'larıyla IDOR testleri yaz.

## 14.2 İş kartı şablonu

Her geliştirme kartı aşağıdaki formatta açılmalıdır:

- **Amaç:** Kullanıcının/operasyonun hangi ihtiyacı çözülecek?
- **Aktör:** Hangi rol kullanır?
- **Ön koşullar:** İşlemin yapılabilmesi için gereken durumlar.
- **Ana akış:** Adım adım işlem.
- **Alternatif akışlar:** Hata, iptal, red, süre aşımı.
- **Veri etkisi:** Hangi tablolar oluşturulur/güncellenir?
- **Yetki:** Hangi permission ve tenant scope uygulanır?
- **API:** Endpoint, request, response, hata kodları.
- **Audit:** Hangi olay kaydedilir?
- **Kabul kriterleri:** Otomatik test edilebilir maddeler.
- **Operasyon:** Log, metrik, alarm ve geri dönüş davranışı.

---

# 15. Ürün müdürü için karar kayıtları

Aşağıdaki ticari konular kod içinde tahmin edilerek sabitlenmemelidir. Geliştirme bunları parametreli yapmalı; canlıya geçiş öncesinde ilgili iş sahibi onaylamalıdır.

| Karar ID | Konu | Geliştirme için varsayılan davranış | Onay sahibi |
|---|---|---|---|
| B-01 | Platformun hukuki satıcı/komisyoncu rolü | Sipariş ve finans modelinde taraf rolleri konfigüre edilebilir; kod tek hukuki varsayıma bağlanmaz | Yönetim + hukuk |
| B-02 | Alıcıya gösterilen fiyat kalemleri | Yalnızca satış toplamı ve açıkça seçilen müşteri kalemleri; tedarikçi maliyeti gizli | Ürün + finans |
| B-03 | Fiyat kilidi süresi | Ayar bazlı süre; süresi dolan quote ile sipariş yok | Ürün + finans |
| B-04 | Metal kuru kaynağı | Kaynak ve gecikme politikası konfigüre edilir; stale kurla sessiz fiyat üretimi yok | Finans/operasyon |
| B-05 | Döviz dönüşüm tipi | Kur tipi konfigüre edilir ve snapshot'a yazılır | Finans |
| B-06 | Vergi/KDV uygulaması | Vergi kuralı ayrı modül/konfigürasyon; oran kodda sabit değil | Mali müşavir |
| B-07 | İade/iptal kesintileri | Kural ve zaman penceresi konfigüre edilir | Yönetim + finans |
| B-08 | Tedarikçi hak ediş zamanı | Teslimat/kalite/ödeme koşuluna göre parametreli | Finans + operasyon |
| B-09 | Kalite kontrol kriterleri | Ürün kategorisi/metal/taş grubuna göre checklist | Kalite operasyon |
| B-10 | Kargo/lojistik modeli | Platform kontrollü sevkiyat; taşıyıcı entegrasyonu sonradan | Operasyon |
| B-11 | B2C kapsamı | B2B akışı doğrulandıktan sonra | Ürün yönetimi |
| B-12 | SAP/ERP entegrasyon yönü | Önce hangi sistemin hangi veride master olduğu belirlenir; çift yönlü yazma varsayılmaz | ERP sahibi + finans |

Bu kararların açık bırakılması geliştiriciyi durdurmamalıdır. Kod, oran/süre/rol gibi değişkenleri konfigürasyon tablosundan okumalı; onaylanmamış parametre ile canlı ticari işlem yapılmasını engellemelidir.

---

# 16. Mevcut kod için korunacaklar, değiştirilecekler, kaldırılacaklar

| Mevcut parça | Karar | Gerekçe |
|---|---|---|
| `Firma` temel modeli | İyileştirerek koru | Firma domain'i doğru başlangıç |
| `Kullanici` | Değiştir | Superuser bypass kaldırılmalı; firma DB'de zorunlu |
| `rol_servisi` | Yeniden düzenleyerek koru | Tek rol yazma noktası fikri doğru; admin/API entegrasyonu ve permission seed eksik |
| `FirmaAdresi` | İyileştir | Varsayılan adres tekilliği ve adres amacı kuralları |
| `FirmaBankaHesabi` | İyileştir | IBAN normalize/validasyon/masking |
| `KiymetliMetal`, `AyarMilyem` | Koruyup güçlendir | Temel referans yapısı uygun |
| `MetalKuru`, `DovizKuru` | Yeniden tasarla | Kaynak, gecikme, geçerlilik ve kur tipi eksik |
| `Kategori` | İyileştir | Alt ağaç derinliği ve slug çakışması |
| `Urun` | Önemli ölçüde değiştir | Tedarikçi bağı katalogdan ayrılmalı; medya ve ürün yaşam döngüsü eklenmeli |
| `Varyant` | Koruyup genişlet | SKU ve eksen fikri doğru; stok/fiyat sahipliği ayrılmalı |
| `UrunTasi` (urunler) | `ProductStone` olarak koru | Katalog özelliği olarak anlamlı |
| `UrunTasi` (fiyatlama) | Yeniden adlandır | `OfferStoneCost` gibi teklif maliyeti olarak ayrıştır |
| `TedarikciTeklif` | Temel fikri koru, yeniden tasarla | Çoklu tedarikçi ve versiyonlama için merkezi ilişki |
| `FiyatSozlesmesi` | İyileştir | Tarih çakışması, immutability ve onay akışı |
| `FiyatSozlesmesiKalemi` | Kuralını düzelt | Genel/spesifik kural çelişkisi |
| `hesapla()` | Saf hesap fonksiyonu olarak koru | Decimal tabanlı formül iyi; orkestrasyon servisi eksik |
| `PriceCalculationLog` | Audit/log olarak koru | Ticari quote snapshot yerine geçmemeli |
| Ürün onay servisi | Yeniden düzenle | Sahiplik/rol kontrolü, audit ve geçiş kuralları |
| Django admin | Backoffice olarak koru | Tek kullanıcı arayüzü olmamalı |
| Seed komutları | İyileştir | Idempotent kalmalı; kod/ad değişiklikleri için veri güncelleme politikası netleşmeli |

---

# 17. Definition of Done — proje genel standardı

Bir modül ancak aşağıdaki maddelerin tamamı sağlandığında tamamlanmış kabul edilir:

- İş akışı ve aktörler bu dokümandaki kurallara uygundur.
- Her endpoint authentication, permission ve tenant scope uygular.
- İstemciden gelen sahiplik/firma bilgisi güvenilir kabul edilmez.
- İş kuralı domain service içinde uygulanır.
- Yapısal veri kısıtları DB seviyesinde korunur.
- Kritik işlem transaction ve eşzamanlılık açısından güvenlidir.
- Audit event üretilir.
- API şeması ve örnekleri günceldir.
- Başarı, hata, sınır durum ve yetki testleri vardır.
- PostgreSQL üzerinde integration testleri geçer.
- Hassas alanlar response ve loglarda sızmaz.
- Admin ve API aynı domain servislerini kullanır.
- Migration geri dönüş/backup planı vardır.
- Operasyon logu, alarmı ve runbook'u yazılmıştır.

---

# 18. Nihai değerlendirme

Mevcut kodun en değerli kısmı, ürün/varyant/kategori ve metal/ayar gibi kuyumculuk domain'inin temel kavramlarını ayırmaya başlamış olmasıdır. Bu kısım çöpe atılmamalıdır. Fakat mevcut sistemin en büyük mimari açığı, **katalog ürünü, tedarikçi teklifi, fiyat, stok ve siparişin tek bir tutarlı ticari akış olarak modellenmemiş olmasıdır.**

En kritik tasarım değişikliği şudur:

**Ürün katalogda platforma ait olmalı; tedarikçi, ürüne/variyanta teklif veren ayrı ticari kaynak olmalıdır.** Böylece aynı katalog ürünü birden fazla tedarikçiden karşılanabilir; alıcı tedarikçiyi görmeden platformun seçtiği teklif üzerinden fiyat alabilir. Sipariş, seçilen teklif ve fiyat snapshot'ına bağlanır. Stok rezervasyonu ve platform operasyonu bu sipariş üzerinden yürür.

İkinci kritik değişiklik: **firma izolasyonu ve rol yetkisi ilk sınıf mimari gereksinim olmalıdır.** Yalnızca `firma` ForeignKey'i veya rol string'i koymak güvenlik sağlamaz. Her sorgu, servis ve endpoint tenant scope ve permission ile korunmalıdır.

Üçüncü kritik değişiklik: **fiyat hesaplama fonksiyonu ile ticari fiyat teklifi aynı şey değildir.** Hesap fonksiyonu matematik yapar; quote servisi doğru girdileri seçer, snapshot üretir, geçerlilik süresi verir ve sipariş anında kilitler.

Bu üç konu çözülmeden sipariş, ödeme ve B2C geliştirmesine geçilmesi teknik borcu büyütür ve veri güvenliği/ticari tutarlılık riski yaratır.

**Uygulama emri:** Önce P0 maddeleri tamamlanacak; ardından katalog/tedarikçi teklif ayrımı ve fiyatlama snapshot zinciri kurulacak; sonra B2B sipariş, stok, kalite, lojistik ve finans akışı geliştirilecektir. Mevcut yapıyı korumak hedef değil; doğru iş kuralını güvenilir ve test edilebilir biçimde çalıştırmak hedeftir.

---

## Ek A — İncelenen başlıca kaynak dosyalar

- `config/config/settings.py`
- `config/config/urls.py`
- `config/firmalar/models/firma.py`
- `config/firmalar/models/kullanici.py`
- `config/firmalar/models/firma_adresi.py`
- `config/firmalar/models/firma_banka_hesabi.py`
- `config/firmalar/services/rol_servisi.py`
- `config/firmalar/admin/kullanici_admin.py`
- `config/firmalar/management/commands/audit_user_assignments.py`
- `config/tanimlar/models/kiymetli_metal.py`
- `config/tanimlar/models/ayar_milyem.py`
- `config/tanimlar/models/metal_kuru.py`
- `config/tanimlar/models/doviz_kuru.py`
- `config/urunler/models/kategori.py`
- `config/urunler/models/urun.py`
- `config/urunler/models/varyant.py`
- `config/urunler/models/urun_kanal.py`
- `config/urunler/models/urun_tasi.py`
- `config/urunler/services/onay_servisi.py`
- `config/fiyatlama/models/tedarikci_teklif.py`
- `config/fiyatlama/models/fiyat_sozlesmesi.py`
- `config/fiyatlama/models/fiyat_sozlesmesi_kalemi.py`
- `config/fiyatlama/models/sozlesme_cozumleme.py`
- `config/fiyatlama/models/price_calculation_log.py`
- `config/fiyatlama/services/fiyat_hesaplama.py`
- Mevcut admin modülleri, seed komutları, migration dosyaları ve test dosyaları.

## Ek B — Önemli sınırlamalar

- Bu rapor yüklenen ZIP'teki kaynak kodun statik incelemesine dayanır.
- Üretim veritabanı, canlı API, frontend, SAP/ERP ortamı veya ödeme/kargo servisleri bu incelemede test edilmemiştir.
- Çalıştırılabilir Django ortamı bu analiz oturumunda bulunmadığından Django system check, migration drift ve test suite çalıştırılmamıştır.
- ZIP içindeki `.env` içeriği rapora alınmamıştır. Gizli değerleri döndürün ve dosyayı arşivden çıkarın.
- Bu doküman teknik geliştirme şartnamesidir; hukuki sözleşme, vergi görüşü veya muhasebe politikası yerine geçmez.


Bu proje; kuyumculuk sektörünün en büyük operasyonel problemlerinden biri olan, dünya genelindeki binlerce çeşit ürüne, doğru üreticiye ve/veya toptancıya ulaşma zorluğunu ve en önemlisi "güven" sorununu ortadan kaldırmayı amaçlayan dijital bir çözümdür.

Sistem; operasyon, lojistik ve finans yönetimi tamamen platform sahibinde (konsolidasyon merkezi) olan hibrit bir B2B ve B2C kapalı devre e-ticaret platformudur. Alıcı ile tedarikçiyi doğrudan buluşturmak yerine, tüm süreçlerin güvenliğini ve standardizasyonunu platform merkezileştirerek üstlenir.


İş Modeli ve Değer Önerisi

• Tedarikçi Havuzu (Çoklu Tedarikçi): Dünyanın her yerindeki toptancı ve imalatçılarla sözleşme yapar. Ürün girişleri, sözleşme kuralları ve fiyatlaması tedarikçiler veya platform yöneticisi tarafından yapılır. Aynı ürünü birden çok tedarikçi sunabilir, alıcı tedarikçiyi görmez, platform servis bedeli alır ve bunu kimseye göstermez.

• Kapalı Devre Güven Zinciri (Kör Havuz): Alıcılar (Kuyumcular veya Nihai Tüketiciler), ürünün arkasındaki asıl imalatçıyı veya toptancıyı görmez. Finansal akış, kalite kontrol ve teslimat tamamen platform güvencesiyle yönetilir; böylece sektördeki en kritik eşik olan "güven" yapısal olarak sağlanır.

• Katma Değerli Operasyon (Stüdyo ve Kalite Kontrol): Havuza giren tüm ürünlerin yüksek kaliteli görsel ve video çekimleri platform yöneticisi tarafından standartlaştırılmış bir stüdyo ortamında yapılır.

• Merkezi Fiyatlandırma, Finans ve Operasyon Yönetimi: Ürünlerin altın kuru, milyem, işçilik, taş maliyetleri ve finansal tahsilat süreçleri platform yöneticisi tarafından kontrol edilir. Siparişler doğrudan yöneticiye düşer. Yönetici ürünleri tedarikçilerden toplar, kalite kontrolünü yapar ve alıcıya tek bir paket halinde kargolar.

• Ürünler sisteme girilirken "Milyem + Günlük Has Altın Fiyatı + İşçilik (TL/Gram veya Dolar/Gram)" formülüyle dinamik fiyatlandırılır. API entegrasyonuyla altın kuru değiştikçe sitedeki fiyatlar otomatik günceller

Platformun hayatını sürdürebilmesi ve büyümesi için kurgulanan gelir akışları (Revenue Streams) şunlardır:

1. B2B RFQ Gelir Modeli (Komisyon ve Arbitraj)

• Gizli Servis Bedeli: Alıcı toptancıyı, toptancı da alıcıyı görmediği için platform, toptancının verdiği ham fiyata (Has Altın + İşçilik) %2 ile %5 arasında değişen bir "Platform Hizmet Payı" ekler. Bu pay faturaya yedirilir ve dışarıdan görünmez.
• Altın Kur Arbitrajı: Anlık kur dalgalanmalarında, sipariş anında kilitlenen kur ile toptancıya ödeme yapılan an arasındaki finansal hedging ve optimizasyondan elde edilen mikro kur kârları.

2. B2C Hemen Öde Gelir Modeli (Yüksek Marjlı Perakende)

• B2C Kâr Marjı: Anlık dinamik fiyatlandırma motoru tetiklendiğinde, toptancının sabit işçilik maliyetinin üzerine %15 ila %30 arasında perakende operasyon marjı eklenir.
• İptal/İade Fonu (Risk Primleme): B2C'deki yasal iade haklarından doğabilecek kur zararlarını sübvanse etmek amacıyla her B2C satış fiyatının içine küçük bir risk primleme payı eklenir. Bu pay iade olmadığı durumlarda doğrudan platforma net kâr kalır.

3. Katma Değerli Hizmet Gelirleri (SaaS & Operasyon)

• Stüdyo ve Standardizasyon Ücreti: Üreticilerin havuzdaki ürünlerini öne çıkarmak için platformun endüstriyel stüdyosunda çekilen 360° video ve yüksek kaliteli fotoğraflar için alınan içerik üretim bedeli.

• API Lisanslama / Altyapı Bedeli: Dışarıya verilen B2C canlı fiyat API'leri için harici e-ticaret sitelerinden veya pazaryeri satıcılarından alınan aylık/yıllık veri lisanslama ücreti.

• Premium Üyelik (B2B): Bazı üreticilerin ürünlerini "Öncelikli Tedarikçi" olarak eşleştirmek veya alıcı kuyumculara "Hızlı Kargo / Öncelikli Kontrol" sağlamak için tasarlanan aylık abonelik modeli.

---

## Sapma kaydı

**Tür:** Ek not (rapor metni v1.0 değiştirilmedi)  
**Tarih:** 2026-11-08  
**Kapsam:** Faz 3 fiyatlama / PriceQuote (proforma)

Ürün sahibi kararıyla (2026-11-08) aşağıdaki kanonik maddeler **Faz 3 için geçerli değildir**:

| Rapor maddesi | Ne diyor (v1.0, olduğu gibi) | Faz 3 sapması |
|---------------|------------------------------|---------------|
| §5.4 formül (`toplam = … + vergiler`) | Hedef toplamda vergi kalemleri yer alır; aşama mali/hukuki onaya bağlı | KDV/vergi **hesaplanmaz**, saklanmaz; alıcıya vergi dahil/hariç tutar gösterilmez. Quote toplamı vergisiz (`toplam_vergisiz`). Belge türü **proforma / fiyat teklifi** ("fatura" değil). |
| B-06 Vergi/KDV uygulaması | Varsayılan: vergi kuralı ayrı modül/konfig; onay sahibi mali müşavir | **ERTELENDİ.** Mali müşavir doğrulaması şimdilik gerekmez; vergi motoru ihtiyacı doğduğunda yeniden açılır. |

**Dayanak:** [`docs/decisions/ADR-0007-faz3-fiyatlama.md`](decisions/ADR-0007-faz3-fiyatlama.md) §2.9 (Ürün sahibi kararı).

**Notlar:**

- Bu bölüm rapor sürümünü yükseltmez; v1.0 gövde metni korunur.
- B-01 (gizli platform hizmet payı / şeffaflık) bu sapmadan **etkilenmez**; ayrı hukuk konusu olarak açık kalır.
- İleride vergi eklenmesi ayrı ADR ve ayrı katman ile yapılır; immutable Faz 3 `PriceQuote` kayıtları geriye dönük değiştirilmez.
