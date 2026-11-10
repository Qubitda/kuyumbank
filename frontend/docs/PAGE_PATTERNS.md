# Page Patterns

Bu kalıplar zorunlu şablon değildir. Sayfanın kullanıcı amacı ve veri yapısına göre uyarlanmalıdır.

## 1. Genel Bakış / Dashboard

Amaç: Kullanıcının önemli durumu hızlıca anlaması ve aksiyon alması.

Olası içerikler:
- Sayfa başlığı ve tarih/bağlam
- Gerçekten anlamlı 2–4 metrik
- Fiyat/kur trendi gerekiyorsa grafik
- Bekleyen onaylar veya dikkat gerektiren işler
- Son işlemler

Kurallar:
- KPI'ların hepsini aynı kartta veya aynı tip kartlarda sıralama zorunluluğu yok.
- Gerçek veri yoksa metrik üretme.
- Grafik yalnızca karar desteği sağlıyorsa kullan.

## 2. Firma Listesi

Önerilen hiyerarşi:
- Firmalar başlığı
- Firma ekle aksiyonu (yetki varsa)
- Arama ve durum/rol filtreleri
- Tablo: firma adı, firma kodu, rol tipi, onay durumu, aktiflik, güncelleme
- Satır aksiyonları
- Pagination

Not: Gerçek alanlar ve kullanıcıya gösterilmesi uygun olmayan alanlar API/iş kuralından doğrulanmalı. Vergi numarası gibi hassas iş verileri gereksiz yere listelenmemeli.

## 3. Firma Detayı

- Breadcrumb
- Firma adı ve firma kodu
- Firma tipi/ilişkileri
- Onay ve aktiflik durumu
- İletişim bilgileri (yetkiye göre)
- Kullanıcılar
- Sözleşmeler
- İlgili aktiviteler

Firma tenant izolasyonunu UI değil backend garanti etmelidir.

## 4. Ürün Kataloğu

- Ürünler başlığı
- Ürün ekleme aksiyonu (yetki varsa)
- Arama, kategori, metal/ayar, onay ve yayın filtreleri
- Tablo veya uygun ürün liste görünümü
- Ürün adı, platform kodu, kategori, ayar/metal, fiyat tipi, onay/yayın durumu
- Ürün detayına erişim

Backend modelinde `olusturan_firma` denetim alanı olarak tanımlanmıştır; alıcıya gösterilmemesi gerektiğine dair model açıklaması vardır. Bu alanı müşteri/vitrin UI'ında göstermeyin.

## 5. Ürün Detayı / Düzenleme

- Ürün kimliği ve başlık
- Kategori, ayar, fiyat tipi
- Temin ve termin bilgisi
- Varyant/ölçü/renk
- Vitrin nitelikleri
- SEO alanları (uygun rol ve iş akışında)
- Onay/yayın durumu ve izinli aksiyonlar

Onay ve yayın durumlarını doğrudan UI state ile değiştirmeyin; backend servis/endpoint sözleşmesi ne gerektiriyorsa onu kullanın.

## 6. Fiyatlama / Hesaplama

- Hesaplama bağlamı
- Metal/ayar ve gram
- Kur ve fiyat girdileri
- İşçilik / marj / servis bedeli gibi iş kuralları
- Sonuç ve hesaplama dökümü
- Kaydetme veya teklif/sözleşmeye dönüştürme aksiyonları

Hesaplama formülünü frontend'de kopyalayıp backend ile farklı sonuç üretmeyin. Backend hesaplama otoritesi olmalı; frontend yalnızca girdileri toplar ve sonucu sunar.

## 7. Fiyat Sözleşmeleri

- Firma ve kontrat tipi
- Satış kanalı (varsa)
- Geçerlilik başlangıç/bitiş
- Durum
- Versiyon
- Önceki versiyon ilişkisi

Model açıklamasına göre şartlar değiştiğinde eski sözleşme değiştirilmek yerine yeni versiyon oluşturulması beklenir. UI bu iş kuralını desteklemeli; mevcut sözleşmeyi sessizce overwrite etmemeli.

## 8. Tanımlar

- Kıymetli metaller
- Ayar/milyem
- Döviz kurları
- Metal kurları
- Satış kanalları

Tanım ekranlarında hızlı arama, net birim/format, aktiflik ve değişiklik yetkisi önemlidir.

## 9. Kullanıcı ve Yetkiler

- Kullanıcı listesi
- Firma/tenant bağlamı
- Rol
- Aktiflik
- İzinli rol atama ve yönetim aksiyonları

Yetki isimlerini veya rol matrisini tahmin etme. Backend'deki `roles.py`, `role_permissions.py`, servisler ve API sözleşmesi incelenerek doğrula.

## 10. Ayarlar

- Hesap/profil
- Firma ayarları
- Tema tercihi
- Bildirim tercihleri (varsa)
- Güvenlik

Gerçekte desteklenmeyen ayarları tasarıma ekleme.
