# Design System — Kuyumbank

## 1. Ürün karakteri

**Yön:** Minimal Enterprise SaaS  
**Görsel referans:** Vercel'in monokromatik disiplini; Linear'ın bilgi hiyerarşisi ve yoğun veri sunumu.  
**Ürün bağlamı:** Kuyumculuk, firma/tenant yönetimi, ürün kataloğu, kıymetli metal ve fiyatlama süreçleri.

Arayüz şu özellikleri taşımalı:
- Sakin, ölçülü, güvenilir
- Veri odaklı ve taranabilir
- Dekorasyondan çok iş akışına odaklı
- Tutarlı ve öngörülebilir
- Geniş ekranda verimli, küçük ekranda bilinçli şekilde sadeleştirilmiş

## 2. Tasarım ilkeleri

1. Önce iş akışı, sonra görsel sunum.
2. Hiyerarşi öncelikle tipografi, boşluk ve hizalama ile kurulur.
3. Kart varsayılan kapsayıcı değildir.
4. Border yalnızca sınır veya gruplama anlatıyorsa kullanılır.
5. Shadow nadir ve işlevsel olmalıdır.
6. Renk dekorasyon değil, anlam taşır.
7. Her sayfa aynı ürün ailesine ait görünmelidir.
8. Gerçek olmayan veri veya grafik üretme.
9. İçerik yoğunluğunu işin doğasına göre ayarla.
10. Görsel sadelik, bilgi saklamak anlamına gelmez.

## 3. Renk sistemi

Mevcut OKLCH gri paleti korunur. Projedeki gerçek CSS token'ları incelenmeden ikinci bir renk sistemi oluşturulmaz.

Önerilen semantik token eşlemesi:

| Token | Light | Dark | Kullanım |
|---|---|---|---|
| background | `oklch(0.985 0 0)` | `oklch(0.145 0 0)` | Sayfa zemini |
| foreground | `oklch(0.145 0 0)` | `oklch(0.985 0 0)` | Ana metin |
| card | `oklch(1 0 0)` | `oklch(0.205 0 0)` | Gerçek yüzeyler |
| primary | `oklch(0.205 0 0)` | `oklch(0.922 0 0)` | Ana aksiyon |
| primary-foreground | `oklch(0.985 0 0)` | Mevcut token ile uyumlu | Primary üzeri metin |
| secondary | `oklch(0.97 0 0)` | Mevcut dark token | İkincil yüzey |
| muted | `oklch(0.97 0 0)` | Mevcut dark token | Soluk yüzey |
| muted-foreground | `oklch(0.556 0 0)` | Mevcut dark token | İkincil metin |
| border | `oklch(0.922 0 0)` | Mevcut dark token | Sınırlar |
| ring | `oklch(0.708 0 0)` | Mevcut dark token | Focus |
| destructive | Mevcut kırmızı token | Mevcut dark kırmızı token | Hata/silme |

Kurallar:
- Renkleri bileşenlerde hex/oklch literal olarak tekrar etme; semantic token kullan.
- Başarı, uyarı ve bilgi durumları için yeni renk eklemek gerekiyorsa önce mevcut token sistemini incele ve erişilebilir kontrastı doğrula.
- Grafiklerde 5 gri tonu kullanılıyorsa seriler yalnızca ton farkıyla ayırt edilebiliyor mu kontrol et; gerekirse etiket, çizgi tipi veya marker da kullan.
- Renk tek başına durum anlatmamalı.

## 4. Tipografi

Font:
- Geist Sans: arayüz metinleri
- Geist Mono: kod, teknik kimlik, gerektiğinde hassas sayısal değerler

| Kullanım | Boyut | Ağırlık | Not |
|---|---:|---:|---|
| Sayfa başlığı | 24px | 600 | `tracking-tight` |
| Bölüm başlığı | 16px | 600 | Gereksiz büyük değil |
| Bileşen başlığı | 14px | 600 | Kompakt |
| Gövde | 14px | 400 | Ana içerik |
| İkincil metin | 13px | 400 | Yeterli kontrast |
| Label | 12px | 500 | Form/alan etiketi |
| Metadata | 11–12px | 500 | Sınırlı kullanım |
| Tablo başlığı | 12px | 500 | Sessiz ama okunur |
| Tablo hücresi | 13px | 400–500 | Veri yoğunluğuna göre |

Kurallar:
- Bütün metinleri bold yapma.
- 11px altını temel bilgi için kullanma.
- Sayısal kolonlarda `tabular-nums`.
- Para, gram, milyem ve yüzde değerlerinde tutarlı formatlama.
- Uzun metinlerde satır uzunluğunu kontrol et.
- Türkçe karakterler ve tarih/para formatları doğru olmalı.

## 5. Spacing ölçeği

4px tabanlı ölçek:

| Token | Değer | Örnek |
|---|---:|---|
| 1 | 4px | İkon-metni aralığı |
| 2 | 8px | Kompakt grup |
| 3 | 12px | Form alanları |
| 4 | 16px | Standart iç boşluk |
| 5 | 20px | Bileşen grubu |
| 6 | 24px | Bölüm içi |
| 8 | 32px | Bölümler arası |
| 10 | 40px | Büyük bölüm arası |
| 12 | 48px | Sayfa bölümleri |

İlişkili öğeler birbirine yakın, farklı gruplar daha ayrık olmalıdır. Sayfayı ferah göstermek için gelişigüzel büyük boşluk bırakma.

## 6. Radius, border, shadow

Önerilen başlangıç değerleri:
- Küçük kontrol: 4px
- Input/button: 6px
- Genel yüzey: 8px
- Dialog: 10px

Kurallar:
- Her yerde `rounded-xl` kullanma.
- İnce border: `border` semantic token.
- Shadow varsayılan olarak yok veya çok hafif.
- Kart içinde kart oluşturma.
- Bölüm ayırmak için önce spacing ve divider düşün.

## 7. Layout ölçüleri

Bunlar başlangıç referansıdır; ekran içeriğine göre test edilerek ayarlanır.

| Alan | Başlangıç |
|---|---:|
| Sidebar genişliği | 240px |
| Dar sidebar | 64px |
| Header | 56px |
| Desktop içerik yatay boşluk | 32px |
| İçerik üst boşluğu | 28px |
| Form genişliği | 640px civarı |
| Input | 36px |
| Button | 36px |
| Tablo satırı | 44–48px |

Masaüstünde tablo ve operasyon ekranları gereksiz daraltılmamalı. Uzun formlarda kontrollü max-width kullanılmalı.

## 8. Motion

- Mikro etkileşimler kısa ve işlevsel olmalı.
- Varsayılan geçiş hedefi 120–180ms.
- Sürekli hareket eden dekoratif öğe kullanma.
- `prefers-reduced-motion` desteği sağla.
- Animasyon, durum değişikliğini açıklamalı; dikkat çekmek için kullanılmamalı.

## 9. Erişilebilirlik

- Klavye ile tüm etkileşimler kullanılabilir olmalı.
- Focus görünür olmalı.
- Form label'ları gerçek input ile ilişkili olmalı.
- Renk kontrastı kontrol edilmeli.
- Dialog açıldığında focus yönetimi doğru olmalı.
- Tablo başlıkları semantik olmalı.
- Durumlar yalnızca renkle anlatılmamalı.

## 10. Anti-pattern listesi

- Her bölümü Card yapmak
- Aşırı `rounded-xl` / `rounded-2xl`
- Her başlığa ikon eklemek
- Gereksiz gradient ve shadow
- Her değeri badge yapmak
- Sahte grafik ve sahte KPI
- Her sayfayı aynı dashboard şablonuna çevirmek
- Rastgele margin/padding
- Her yerde aynı yoğunluk
- Birbiriyle ilgisiz öğeleri aynı kartta toplamak
- Sadece güzel screenshot için kullanılabilirliği bozmak
