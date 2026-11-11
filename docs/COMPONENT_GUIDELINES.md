# Component Guidelines

## Genel

- Önce mevcut shadcn/ui bileşenlerini incele.
- Bileşenleri varsayılan görünümüyle körlemesine kullanma; token sistemine uyarla.
- Her bileşenin tek ve anlaşılır sorumluluğu olsun.
- Gereksiz wrapper ve soyutlama üretme.
- `className` birleştirme yaklaşımını projede standartlaştır.
- Component API'leri tutarlı ve tip güvenli olmalı.

## Application Shell

### Sidebar
- Desktop genişliği başlangıçta 240px.
- Dar mod gerekiyorsa 64px.
- Aktif route açıkça anlaşılmalı.
- Menü grupları anlamlı olmalı.
- İkonlar yalnızca tanınabilirlik sağlıyorsa kullanılmalı.
- Kullanıcı yetkisine göre menü sunumu backend yetkileriyle uyumlu olmalı.

### Header
- Başlangıç yüksekliği 56px.
- Breadcrumb, arama veya bağlamsal aksiyonlar ihtiyaca göre.
- Gereksiz ikinci toolbar oluşturma.
- Kullanıcı menüsü ve tema kontrolü tutarlı yerde olmalı.

### Main content
- Sayfa genişliği içeriğe göre belirlenmeli.
- Veri tabloları gereksiz max-width ile daraltılmamalı.
- Formlar kontrollü genişlikte olmalı.

## Button

Önerilen varyantlar:
- default
- secondary
- outline
- ghost
- destructive
- link

Önerilen boyutlar:
- sm
- default
- lg
- icon

Kurallar:
- Bir ekranda birincil aksiyon görsel olarak ayırt edilsin.
- Birden fazla primary butonla rekabet yaratma.
- Icon-only butonlarda accessible label / tooltip sağla.
- Loading ve disabled durumları tanımlı olsun.

## Input / Select

- Başlangıç yüksekliği 36px.
- Focus ring görünür.
- Error state semantik.
- Label ve açıklama bağlantılı.
- Select arama gerektiriyorsa uygun combobox kullan.
- Klavye navigasyonu korunmalı.

## Table / Data Grid

- TanStack Table kullanımı mevcut sürüm ve API ile doğrulansın.
- Toolbar sadece gerekli kontrolleri içersin.
- Başlık satırı sakin ve okunur.
- Sayısal kolonlar sağa hizalı.
- Metin kolonları sola hizalı.
- Satır yüksekliği başlangıçta 44–48px.
- Hover durumu çok hafif.
- Satır border'ları ince.
- Gereksiz dikey grid çizgileri kullanma.
- Sorting, filtering ve pagination gerçek data state ile çalışmalı.
- Kolon görünürlüğü yalnızca ihtiyaç varsa eklenmeli.
- Empty/loading/error state ayrı tasarlanmalı.
- Tablo semantik HTML ve erişilebilir başlıklar kullanmalı.

## Form

- React Hook Form + Zod.
- Schema ve UI sorumluluklarını ayır.
- Server validation hatalarını uygun alana eşle.
- Submit sırasında loading/disabled.
- Başarılı kayıtta net geri bildirim.
- Form reset davranışı açık olmalı.

## Dialog / Sheet

- Kısa, açık başlık.
- Gerekliyse açıklama.
- Ana ve iptal aksiyonu.
- Yıkıcı işlemde açık teyit.
- Uzun ve karmaşık formları dar dialog'a sıkıştırma; uygun sayfa veya sheet kullan.
- Focus trap ve escape davranışı korunmalı.

## Badge / Status

- Badge yalnızca kısa durum/etiket için.
- Her veri hücresini badge'e çevirme.
- Durum metni backend değerleriyle eşleşmeli.
- Renk yanında metin/ikon desteği olmalı.

## Charts

- Recharts yalnızca anlamlı trend/karşılaştırma varsa.
- Sahte veya sabit demo veriyi canlı veri gibi sunma.
- Tooltip, axis ve legend okunur olmalı.
- Gri tonları yeterli değilse çizgi tipi/marker/etiket ekle.
- Grafik yanında önemli sayısal özet bulunabilir.

## Toast / Alert

- Sonner ile kısa, eylem odaklı mesajlar.
- Hata mesajları teknik stack trace göstermemeli.
- Kullanıcıya sonraki adımı anlat.
- Kritik hata yalnızca toast ile geçiştirilmemeli.

## Icons

- Lucide React.
- Genel boyut 16px.
- Navigation 16px.
- Büyük aksiyon 18px.
- Tutarlı stroke.
- Dekorasyon için ikon kullanma.
