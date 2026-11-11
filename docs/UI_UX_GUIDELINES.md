# UI/UX Guidelines

## 1. Ürün alanı ve kullanıcı zihinsel modeli

Kod tabanında görülen alanlara göre arayüzün temel iş alanları:
- Firmalar ve tenant ilişkileri
- Kullanıcılar ve roller
- Ürün kataloğu, kategori ve varyantlar
- Kıymetli metaller ve ayar/milyem tanımları
- Fiyatlama ve fiyat sözleşmeleri
- Tedarikçi teklifleri ve ürün eşleştirme/onay süreçleri

Bu alanlar kullanıcıya teknik Django model isimleriyle değil, anlaşılır iş diliyle sunulmalıdır. Gerçek kullanıcı rolleri ve yetkileri backend sözleşmesinden doğrulanmalıdır.

## 2. Navigasyon prensipleri

Önerilen bilgi mimarisi (backend yetenekleri ve yetkiler doğrulanmadan nihai menü kabul edilmemeli):

- Genel Bakış
- Katalog
  - Ürünler
  - Kategoriler
  - Varyantlar
- Fiyatlama
  - Fiyat hesaplamaları
  - Fiyat sözleşmeleri
  - Tedarikçi teklifleri
- Tanımlar
  - Kıymetli metaller
  - Ayarlar / milyem
  - Döviz ve metal kurları
  - Satış kanalları
- Firmalar
- Kullanıcılar ve yetkiler
- Sistem / Ayarlar

Menü öğeleri kullanıcının rolüne göre gösterilebilir; ancak UI'da gizlemek güvenlik kontrolü değildir. Yetki her zaman backend'de doğrulanmalıdır.

## 3. Sayfa hiyerarşisi

Uygun olduğunda:
1. Breadcrumb / konum
2. Sayfa başlığı
3. Kısa açıklama veya bağlam
4. Ana aksiyon
5. Arama ve filtreler
6. Ana içerik
7. İkincil bilgiler

Her sayfada tüm alanlar zorunlu değildir. Sayfanın işine göre sadeleştir.

## 4. Veri yoğunluğu

Kuyumculuk ve fiyatlama ekranlarında kullanıcılar çok sayıda sayısal alanla çalışabilir:
- Gram
- Ayar / milyem
- Metal
- Döviz
- İşçilik
- Marj / servis bedeli
- Fiyat
- Tarih ve geçerlilik aralığı

Kurallar:
- Sayısal değerleri tutarlı hizala.
- Birim bilgisini belirsiz bırakma.
- Ondalık hassasiyetini backend iş kuralına göre uygula; UI kendi başına yuvarlama kuralı uydurmasın.
- Ham ve hesaplanmış değerleri görsel olarak ayırt et.
- Hesaplama sonucunun hangi girdilerden geldiğini gerektiğinde açıklanabilir kıl.
- Kritik fiyat değişikliklerinde önce/sonra karşılaştırması sun.
- Kullanıcının yanlışlıkla onay/ret yapmasını önleyecek teyit ve geri bildirim kullan.

## 5. Kart politikası

Kart yalnızca:
- Ayrı bir varlık/özet widget'ı varsa
- İçeriğin bağımsız yüzeye ihtiyacı varsa
- Etkileşim alanı belirgin olmalıysa
- Görsel gruplama gerçek anlam taşıyorsa

kullanılır.

Aksi halde başlık + açıklama + içerik + gerektiğinde divider yeterlidir.

## 6. Tablo UX

- Arama ve filtreler tabloya yakın konumlandırılır.
- Kolon başlıkları kısa ve anlaşılırdır.
- Sayısal değerler sağa hizalanır.
- Uzun metinlerde kontrollü truncate + erişilebilir tam değer sunulur.
- Satır aksiyonları tutarlı yerde bulunur.
- Toplu seçim yalnızca toplu işlem gerçekten varsa eklenir.
- Pagination, toplam kayıt ve sayfa boyutu net olmalı.
- Loading, empty, error ve permission state tasarlanmalı.
- Mobilde yatay kaydırma, kolon önceliklendirme veya kart benzeri satır sunumu bilinçli seçilmeli; masaüstü tablosu sadece küçültülmemeli.

## 7. Form UX

- Alanlar iş bağlamına göre gruplanır.
- Label her zaman görünür ve açık olmalı.
- Placeholder label yerine kullanılmamalı.
- Hata mesajı alanın yanında ve düzeltilebilir bir dilde gösterilmeli.
- Kaydetme sırasında çift gönderim engellenmeli.
- Kaydedilmemiş değişiklikler gerektiğinde uyarılmalı.
- Zorunlu alanlar tutarlı belirtilmeli.
- Uzun formlar mantıklı bölümlere ayrılmalı; her bölümü karta koyma.

## 8. Onay ve durum yönetimi

Kodda ürün ve firma onay durumları, yayın durumları ve sözleşme durumları bulunduğu görülüyor. UI etiketleri backend `choices` değerleriyle eşleştirilmeli; yeni durum icat edilmemeli.

- Taslak
- Onay bekliyor
- Onaylı
- Reddedildi
- Aktif / Pasif
- Süresi doldu

Bunlar yalnızca örnek görünen iş durumlarıdır. Her modelin gerçek durum seçenekleri API şemasından doğrulanmalıdır.

Onay/ret aksiyonlarında:
- Kullanıcının yetkisi backend'de doğrulanmalı.
- Gerekli açıklama alanı gösterilmeli.
- Sonuç toast ve güncellenmiş durumla bildirilmeli.
- Hata halinde kullanıcı girdisi kaybolmamalı.

## 9. Loading / empty / error

Her veri ekranı için:
- İlk yükleme skeleton'ı veya uygun loading state
- Filtre sonucu yok empty state
- Henüz veri yok empty state
- Yetki yok state
- API hatası state
- Tekrar dene aksiyonu

tasarlanmalı. Skeleton, gerçek içerik yerleşimini taklit etmeli; dekoratif animasyon olmamalı.

## 10. Responsive

- Desktop: veri yoğunluğu ve çoklu kolonlar.
- Tablet: filtrelerin ve aksiyonların yeniden düzenlenmesi.
- Mobile: birincil görev, kritik alanlar ve temel aksiyonlar.

Mobilde önemli işlemleri erişilemez hale getirme. Tabloyu küçültmek yerine kolon önceliği belirle.
