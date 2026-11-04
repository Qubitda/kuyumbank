# Kuyum B2B Pazaryeri — Mimari ve Analiz Dokümanı v3

Hazırlayan: Platform sahibi ve analiz ekibi. Okuyucu: iş analisti, geliştirici, AI agent. Bu doküman v2 üzerine netleşen kararları toplar, tekrarları çıkarır.

## 1. Amaç ve kapsam

Platform, kuyum tedarikçilerinin ürünlerini alıcı firmalara (kuyumcu, acente, API ile bağlanan firma) ileten bir B2B pazaryeridir. Bedbank mantığına benzer: aynı ürünü birden çok tedarikçi sunabilir, alıcı tedarikçiyi görmez, platform servis bedeli alır ve bunu kimseye göstermez.

Platform fiziksel olarak da araya girer: tedarikçi ürünü platforma gönderir, platform kontrol eder ve alıcıya kargolar.

## 2. Taraflar

| Taraf | Rol |
| --- | --- |
| Platform (ops, admin) | Katalog, teklif, sözleşme, kontrol, sevkiyat yönetimi. Her şeyi görür |
| Tedarikçi firma | Ürün ve teklif girer, kendi net fiyatını görür, siparişi platforma gönderir |
| Alıcı firma | Talep gönderir veya fiyat sorgular, tek toplam fiyat görür |

B2C diye ayrı bir müşteri tipi yoktur. B2C hizmet veren firma da bizim için sıradan bir alıcı firmadır. Tüketici o firmanın müşterisidir, bizim sistemimizde kaydı yoktur. Firmanın kendi kârı bizim sistemimizde tutulmaz.

## 3. Çalışma modu ve teslimat modu (firma ayarları)

Her alıcı firma tek bir çalışma modu seçer. Bir firma iki modu birden kullanamaz. Mod backend'de zorlanır: talep/teklif firması fiyat endpoint'lerini API'den de çağıramaz.

| Ayar | Değerler | Kural |
| --- | --- | --- |
| `calisma_modu` | `TALEP_TEKLIF` / `DOGRUDAN_FIYAT` | Varsayılan `TALEP_TEKLIF`. Yalnızca platform yetkilisi değiştirir, audit'li. Açık talep veya teklif varken değişmez |
| `teslimat_modu` | `FIRMAYA` / `MUSTERIYE` | B2B firma `FIRMAYA`, B2C hizmet veren API firması `MUSTERIYE`. Siparişe kopyalanır, sonradan değişse eski sipariş etkilenmez |

`MUSTERIYE` siparişte alıcı adı, telefon ve adres zorunludur. Bu bilgi kişisel veridir (KVKK): yalnızca teslimat için alınır, tedarikçi tarafına asla geçmez, saklama süresi belirlenir.

## 4. Katalog

Üç katmanlı yapı: model (platformun), varyant (platformun), tedarikçi teklifi (tedarikçinin).

```
Kategori ──< UrunModel ──< UrunVaryant ──< TedarikciTeklif ──< UrunTasi
                │                                │
                └──< UrunGorsel >────────────────┘
```

### 4.1 UrunModel

Vitrinde görünen ürün. Alanlar: `platform_kod` (benzersiz, alıcıya görünen kod), `ad`, `aciklama`, `aile`, `kategori`, `kaynak` (`PLATFORM` / `TEDARIKCI`), `olusturan_firma`, `durum` (`taslak` → `onay_bekliyor` → `yayinda` → `pasif`), `kdv_grubu`, yapı nitelikleri (`zincir_tipi`, `kopca_tipi`, kategoriye bağlı), vitrin nitelikleri (`koleksiyon`, `ozel_gun`, `stil`, `yas_grubu`, opsiyonel), `birlestirildi_model`.

Modeli platform da tedarikçi de girebilir. Tedarikçi girerse model onay bekler, ops onaylar ya da mevcut modelle birleştirir. Fotoğraf ve ürün detayını da platform girebilir.

### 4.2 Aile

Aile, hangi alanların sorulacağını ve hangi doğrulamaların çalışacağını belirler. Fiyat biçimini belirlemez.

| Aile | Vitrin adı | Kural |
| --- | --- | --- |
| `kuyum` | Altın / gümüş takı | Metal, ayar, gram zorunlu (metal bazlı teklifte). Taş opsiyonel |
| `mucevher` | Pırlanta / renkli taşlı | En az bir taş satırı zorunlu |
| `taki` | Çelik ve fantezi takı | Değerli maden yok. Sertifika ve 4C alanları gösterilmez |

Filtre seti ve form şeması aileye göre değişir ve API'den döner. Kural tek yerde (`servisler.py`) durur, admin, tedarikçi paneli ve Excel içe aktarma aynı kuralı kullanır.

### 4.3 UrunVaryant

`model`, `platform_sku`, `ayar` (nullable), `renk`, `olcu`, `malzeme`, `kaplama`, `aktif`. `(model, ayar, renk, olcu)` benzersizdir. Fiyat ve stok burada tutulmaz. `malzeme` ve `kaplama` fiyatı etkilemez, vitrin ve filtre içindir.

### 4.4 TedarikciTeklif

Fiyatlama bunun üzerinde çalışır.

| Alan | Not |
| --- | --- |
| `varyant`, `tedarikci` | FK |
| `tedarikci_kodu` | Alıcıya görünmez |
| `fiyat_modeli` | `METAL_BAZLI` / `GRAM_BIRIM` / `SABIT_PARCA` |
| `gram`, `gram_tolerans` | Nominal gram teklifte durur |
| `birim_fiyat`, `para_birimi` | `GRAM_BIRIM` ve `SABIT_PARCA` için |
| `iscilik_override` | Boşsa işçilik tedarikçi sözleşmesinden çözülür |
| `temin_tipi` | `HAZIR` / `SIPARISE_OZEL` / `BENZERSIZ` |
| `stok_adet`, `uretim_suresi_gun` |  |
| `oncelik` | Ops'un önceliklendirmesi |
| `durum`, `onaylayan`, `onay_zamani` | `taslak` → `onay_bekliyor` → `yayinda` → `pasif` |

Fiyat biçimi ürüne veya aileye değil teklife bağlıdır. Aynı ürünü bir tedarikçi gramla, diğeri sabit dövizle verebilir.

| `fiyat_modeli` | Hesap |
| --- | --- |
| `METAL_BAZLI` | gram × milyem × saf birim fiyat + işçilik (altın, gümüş) |
| `GRAM_BIRIM` | gram × birim fiyat (gramla satılan, değerli maden olmayan ürün) |
| `SABIT_PARCA` | tutar × adet |

### 4.5 UrunTasi (teklife bağlı)

`tas_grubu`: `pirlanta` / `renkli` / `sus_tasi`. Ortak: `adet`, `toplam_karat`, `toplu_mu`, `bedel`, `para_birimi`. Pırlanta: renk derecesi, berraklık, kesim, sertifika kurumu ve no. Renkli: taş türü, menşe, işlem. Süs taşında sertifika ve kalite alanları sorulmaz. Küçük taşlar (pavé, melle) tek toplu satırdır. Taş bedelini tedarikçi girer.

### 4.6 UrunGorsel

Modele veya teklife bağlı, ikisi birden olamaz. Vitrinde yalnızca model görselleri görünür. Tedarikçi görseli ops ekranında seçilebilir.

### 4.7 Doğrulama kuralları

| Koşul | Kural |
| --- | --- |
| `aile = mucevher` | Teklifte en az bir taş satırı |
| `METAL_BAZLI` | Metal, ayar, gram zorunlu |
| `GRAM_BIRIM` | Gram ve birim fiyat zorunlu, metal kuru kullanılmaz |
| `SABIT_PARCA` | Birim fiyat zorunlu, gram opsiyonel |
| `BENZERSIZ` | Stok 1, varyantta tek teklif, satılınca kapanır |
| `SIPARISE_OZEL` | Üretim süresi zorunlu |
| Model yayına çıkarken | En az bir yayında teklif ve bir vitrin görseli |

### 4.8 Teklif eşleştirme ve seçimi

İlk sürümde otomatik eşleştirme yoktur. Tedarikçi Excel yüklediğinde her satır için ops "mevcut modele bağla / yeni model oluştur" kararı verir. Ortak sütunlar modele, tedarikçiye özel sütunlar teklife gider. Benzersiz parça ve renkli taşlı ürünlerde model otomatik oluşur.

Teklif seçimini ops yapar. Sistem uygun teklifleri (stoklu, onaylı) TL toplamına göre sıralayıp öneri sunar.

## 5. Sözleşmeler ve fiyatlama

### 5.1 İki ayrı sözleşme

| Sözleşme | Taraflar | İçindeki bedel |
| --- | --- | --- |
| Tedarikçi sözleşmesi | Tedarikçi ↔ Platform | İşçilik |
| Alıcı sözleşmesi | Platform ↔ Alıcı | Servis bedeli (platformun kazancı) |

Her kayıtta tek bedel vardır. Kâr ayrıca saklanmaz, servis bedeli zaten platformun kazancıdır.

### 5.2 Sözleşme tipleri

| Tip | Anlamı | Ek alan |
| --- | --- | --- |
| `PARA` | Sabit tutar | `para_birimi`: TRY / USD / EUR |
| `YUZDE` | Bir tabanın yüzdesi | `taban` |
| `GRAM` | Has gram cinsinden tutar | yok |

- `GRAM`, ürün gramı başına değil parça başına has gram tutarıdır (örnek: 250 TL / 6.250 = 0,04 has gram).
- Tip, sonucun birimini belirler: TRY için TL, USD için USD, `GRAM` için has gram. Döviz ve gram tipinde metal bedeli de o birime çevrilir.
- `taban`: işçilikte her zaman ham metal. Servis bedelinde ham metal, ham metal + işçilik veya toplam (taş dahil).
- `min_tutar` opsiyonel alan olarak modelde durur.
- Doğrulama: `PARA`'da para birimi dolu, `YUZDE`'de taban dolu, `GRAM`'da ikisi de boş olmalı. Yüzde tabanı ham metal olan kural yalnızca `METAL_BAZLI` tekliflerde geçerlidir, aksi halde hata verilir, sessizce 0 hesaplanmaz. `GRAM_BIRIM` ve `SABIT_PARCA` tekliflerde yüzde tabanı otomatik toplamdır.

### 5.3 Kapsam alanları

Her iki sözleşme türünde aynı nullable alanlar bulunur, boş alan "hepsi" demektir: alıcı firma veya fiyat grubu, tedarikçi (tedarikçi sözleşmesinde zorunlu), `aile`, `kategori`, `model`, `varyant`, `ayar`, `renk`, `baslangic`, `bitis`. Ölçü kapsam değildir, çünkü gramı etkiler ve gram teklifte durur. `varyant` doluysa model ve kategori türetilir, çelişkili giriş reddedilir.

### 5.4 Çakışma kuralları

| Eksen | Kural |
| --- | --- |
| Alıcı | Bir alıcı, bir ürün ve bir tarih için en fazla bir sözleşme geçerlidir. Çakışan kayıt reddedilir (`clean()` ve PostgreSQL exclusion constraint). Motor sıfır veya birden fazla sonuç bulursa hata verir |
| Alıcıya özel anlaşma | Genel kurala `haric_firmalar` listesi eklenir. Özel anlaşma girilirken sistem çakışan genel kuralı bulur, onayla firmayı hariç tutar ve yeni sözleşmeyi tek işlemde kaydeder. Özel anlaşma bitince firma otomatik geri girmez, ops'a görev düşer |
| Ürün | Kategori ve varyant kuralları iç içe geçebilir, en spesifik kazanır: teklif override > varyant > model > ayar/renk kapsamlı > kategori (alt → üst) > aile > genel. Aynı seviyede iki kural varsa hata verilir |
| Zaman | Tarihe uyan kampanya, sürekli kuraldan önce gelir |

### 5.5 Hesap akışı

1. Metal bedeli: gram × milyem / 1000 × saf birim fiyat.
2. Tedarikçi sözleşmesinden işçilik çözülür. Metal + işçilik tedarikçi net fiyatıdır.
3. Alıcı sözleşmesinden servis bedeli çözülür.
4. Alıcı fiyatı = metal + işçilik + servis (+ taş bedeli, varsa).
5. Tedarikçiye ödenecek = metal + işçilik (+ taş bedeli).

Tüm hesap `Decimal` ile yapılır. Ara adımda yuvarlama yapılmaz, yalnızca sonda yuvarlanır. Sonuç, kalem listesi olarak döner: her kalem `tip`, `tutar`, `birim`, `kur`, `kur_tipi`, `kur_zamani` ve `gorunurluk` taşır. Yeni ücret kalemi (kargo gibi) listeye eklenir, mevcut yapı değişmez. Servis bedeli satır bazında hesaplanır ve satırda saklanır (parça başı × adet). Kontratta `uygulama_seviyesi` (`SATIR` / `SIPARIS`) alanı vardır, ilk sürümde yalnızca `SATIR` kabul edilir.

### 5.6 Doğrulama örneği (Excel)

Ürün: 8,41 gr, 24K (milyem 0,995), saf altın 6.250 TL/gr, USD kuru 49,70. İşçilik 250 TL, servis 1.500 TL.

| Tip | Metal bedeli | İşçilik | Servis | Satış fiyatı |
| --- | --- | --- | --- | --- |
| `PARA` (TRY) | 52.299,69 TL | 250 TL | 1.500 TL | 54.049,69 TL |
| `PARA` (USD) | 1.052,31 USD | 5,03 USD | 30,18 USD | 1.087,52 USD |
| `YUZDE` | 52.299,69 TL | ham metalin \~%0,5'i | ham metalin \~%2,9'u | 54.049,69 TL |
| `GRAM` | 8,368 has gram | 0,04 | 0,24 | 8,648 has gram |

Her satır birim test olarak yazılır. Ek örnek: 10 gr, 14K, altın 6.250: has gram 5,85, ham fiyat 36.562,50 TL.

### 5.7 Kurlar ve master veri

`PreciousMetal`, `AyarMilyem`, `MetalRate`, `FXRate`. Kur ve metal fiyatı `DateTimeField` ile gün içinde birden çok kayıt alır. Kur tipi (döviz satış gibi) tek bir ayardır, kodda gömülü olmaz. Milyem tablosu: 8K 333, 14K 585, 18K 750, 22K 916, 24K 995, 925 gümüş.

## 6. Fiyat görünürlüğü ve gizlilik

Gizlilik veri katmanında çözülür, ekranda gizlemek yetmez.

| Kim | Görür | Görmez |
| --- | --- | --- |
| Alıcı | Tek toplam fiyat (sözleşme biriminde) ve bilgi amaçlı TL karşılığı | Tedarikçi, tedarikçi kodu, kırılım, servis bedeli |
| Tedarikçi | Kendi net fiyatı, sipariş içeriği, platform adresi | Alıcı fiyatı, alıcı kimliği, müşteri adresi, servis bedeli |
| Platform | Hepsi | – |

- Alıcı ve tedarikçi için ayrı serializer'lar, açık izinli alan listesiyle yazılır. Tüm alanları otomatik veren serializer kullanılmaz.
- Kırılım yalnızca `PriceCalculationLog`'da durur, erişim yalnızca platformdadır.
- Alıcı fiyatı sözleşme biriminde görünür (TL, USD veya has gram). Ödeme ve mutabakat da bu birimdedir.
- Fatura platform markasıyla, alıcıya tek kalem olarak kesilir.

## 7. Talep ve teklif akışı (`TALEP_TEKLIF` modu)

Kuyumcu panelinde fiyat görünmez. Kuyumcu ürünleri seçip talep gönderir, platform yöneticisi stok ve fiyatı belirleyip teklif yollar, kuyumcu onaylarsa süreç devam eder.

| Adım | Kim | Durum |
| --- | --- | --- |
| 1 | Alıcı talep gönderir | `talep_gonderildi` |
| 2 | Ops stok ve tedarikçiyi seçer, fiyatı sistem hesaplar | `teklif_hazirlaniyor` |
| 3 | Ops teklifi alıcıya gönderir | `teklif_gonderildi` |
| 4 | Alıcı onaylar veya reddeder | `onaylandi` / `reddedildi` |
| 5 | Sistem onaylanan teklifi siparişe çevirir | `siparis` |

Varlıklar: `Talep`, `TalepSatiri` (varyant ve adet, fiyat alanı yok), `AliciTeklifi` (satırlar, seçilen tedarikçi teklifleri, kilitli fiyat, geçerlilik, durum). Tedarikçi teklifi (`TedarikciTeklif`) ile alıcıya giden `AliciTeklifi` farklı kavramlardır.

`DOGRUDAN_FIYAT` modunda alıcı fiyatı API veya sepet üzerinden kendisi sorgular. Fiyat sorgusu geçerlilik süresiyle döner, süre dolunca yeni sorgu gerekir. Firma gösterdiği fiyatı bu süre içinde siparişe çevirmek zorundadır.

## 8. Fiyat kilidi

- `TALEP_TEKLIF`: kilit teklif gönderilirken oluşur, süre `teklif_gecerlilik_bitis`. `DOGRUDAN_FIYAT`: kilit fiyat sorgusunda oluşur, kısa süreli, varsayılan 15 dakika, ayar olarak tutulur.
- Kilit seçilen teklifi, ana tutarı ve birimini, TL karşılığını, kuru, altın fiyatını ve hesap zamanını saklar.
- Tedarikçi tarafı da aynı anda kilitlenir: teklif, işçilik, metal fiyatı, kur. Platformun açık pozisyonu bu anda doğar.
- Süre dolarsa yeniden hesaplanır, eski fiyatla sipariş geçmez.
- Stok kilitle rezerve edilmez. Benzersiz parça teklif süresince ayrılır.

## 9. Sipariş yaşam döngüsü ve lojistik

Tedarikçi ürünü platforma gönderir, platform kontrol edip alıcıya kargolar. Tedarikçi alıcıyı, alıcı tedarikçiyi hiç görmez.

| Adım | Durum |
| --- | --- |
| Ops siparişi tedarikçiye iletir | `tedarikciye_iletildi` |
| Tedarikçi kabul eder | `tedarikci_onayladi` (ret: `tedarikci_reddetti`) |
| Tedarikçi platforma gönderir | `tedarikci_kargoda` |
| Platform teslim alır, tartar, kontrol eder | `platformda_kontrol` |
| Kontrol geçerse alıcıya gönderilir | `alicya_kargoda` |
| Alıcı teslim alır | `teslim_edildi` |

Sapmalar: `tedarikci_reddetti` (ops sıradaki teklife atar, `teklif_id` satırda tutulur), `kontrol_basarisiz`, `iade_edildi`, `alici_onayi_bekliyor`.

- `Sevkiyat`: `yon` (`TEDARIKCI_PLATFORM` / `PLATFORM_ALICI`), kargo firması, takip no (ops elle girer), tarihler. Tedarikçi yalnızca ilk yönü görür.
- `KontrolKaydi` (satır başına): gerçek gram, fark, kalite notu, fotoğraf, `karar`, kararı veren, zaman, gerekçe.
- Tedarikçi ödemesi `platformda_kontrol` başarıyla geçilmeden doğmaz.

### 9.1 Gram toleransı

| Durum | Kural |
| --- | --- |
| Gerçek gram tolerans içinde | Nominal gram geçerli, fiyat değişmez |
| Gerçek gram düşük (tolerans dışı) | Ops doğrudan gerçek grama göre düzeltir |
| Gerçek gram yüksek (tolerans dışı) | Ops doğrudan düzeltemez, alıcıya sormak zorunludur |
| Ops'un diğer seçeneği | Tedarikçiye iade (`iade_edildi`, satır iptal, ödeme doğmaz) |

- Düzeltme kilitli kur ve altın fiyatıyla yapılır, yalnızca gram değişir. `PriceCalculationLog`'a "kontrol düzeltmesi" tipinde ikinci kayıt yazılır, ilk hesap silinmez.
- "Alıcıya sor": alıcı onaylarsa düzeltme akışı, reddederse iade akışı işler. Cevap süresi dolarsa sipariş iade edilir.
- Alıcı düzeltmede yine yalnızca yeni toplamı görür, tedarikçi yalnızca kendi payının değiştiğini görür.

## 10. Mutabakat ve kur riski

Alıcı USD öderken tedarikçiye has gram ödenebilir. Fiyat kilitlenince ödeme gününe kadar kur ve altın oynar, bu farkı platform taşır. Mutabakat her tarafın kendi biriminde ayrı tutulur, platformun açık pozisyonu raporda görünür. Kilit ve ödeme sürelerinin kısa tutulması riski küçültür.

## 11. Denetim ve yetki

- Audit: Firma, sözleşme, teklif ve kontrol kararları `django-simple-history` ile baştan kayıt altındadır. Mod değişikliği, kim, ne zaman, hangi moddan hangisine olduğuyla yazılır.
- Teklifi kimin hazırladığı, gönderdiği ve alıcının ne zaman onayladığı kaydedilir. Maker-checker ve ince izin matrisi sonraki aşamadadır, yeri hazır bırakılır.
- Platform rolleri: Ops, Admin, Super.

## 12. İlk sürüm kapsamı

| Çalışır | Modelde durur ama "henüz desteklenmiyor" hatası verir |
| --- | --- |
| B2B + `TALEP_TEKLIF` + `FIRMAYA` | `DOGRUDAN_FIYAT`, `MUSTERIYE`, `uygulama_seviyesi = SIPARIS` |
| Manuel eşleştirme, ops teklif seçimi | Otomatik eşleştirme, fallback otomasyonu |
| Manuel takip no, tek kanal (kuyumcu paneli) | Kargo entegrasyonu, vitrin fiyat önbelleği, sepet |

## 13. Geliştirme sırası (elle, AI agent olmadan)

1. İskelet: Django + PostgreSQL, uygulamalar `firmalar`, `katalog`, `fiyatlama`, `siparis`, `operasyon`, `mutabakat`, `audit`.
2. Master veri: metal, ayar, kur modelleri ve fixture.
3. Minimal Firma (`ad`, `is_buyer`, `is_supplier`, `aktif`, `calisma_modu`, `teslimat_modu`), admin'den üç firma. Audit hemen eklenir.
4. Katalog: model, varyant, teklif, taş, görsel ve doğrulama kuralları.
5. Sözleşme modelleri ve çakışma kontrolü.
6. `FiyatHesaplamaServisi`: saf Python, `Decimal`, önce `PARA` (TRY) ve `YUZDE`, sonra `PARA` (döviz) ve `GRAM`. Her tip için birim test. Excel örnekleri hazır test verisidir.
7. Sözleşme çözümleme, kampanya ve `PriceCalculationLog`.
8. Talep, `AliciTeklifi` ve fiyat kilidi.
9. Sipariş yaşam döngüsü, sevkiyat, kontrol kaydı.
10. Sonra: mutabakat, ikinci kanal, API, yetki devri, maker-checker.

## 14. v2'den v3'e değişenler

- Katalog tek katmandan üç katmana (model, varyant, tedarikçi teklifi) geçti, fiyat biçimi teklife taşındı.
- Üç ürün ailesi (`kuyum`, `mucevher`, `taki`) ve üç taş grubu eklendi.
- Sözleşme tipleri üçe indi (`PARA`, `YUZDE`, `GRAM`), işçilik ve servis iki ayrı sözleşmeye bölündü.
- Çakışma yasağı alıcı ekseninde, "en spesifik kazanır" ürün ekseninde geçerli.
- Alıcı tek toplam fiyatı sözleşme biriminde görür, servis bedeli gizlidir.
- Firma bazında `calisma_modu` ve `teslimat_modu` eklendi, B2C ayrı alıcı tipi olmaktan çıktı.
- Talep/teklif akışı, platform üzerinden lojistik ve gram toleransı kuralları eklendi.
- Fiyat kilidi, `DOGRUDAN_FIYAT` için sepetten fiyat sorgusuna, `TALEP_TEKLIF` için teklif gönderimine bağlandı.
