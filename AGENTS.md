# Kuyumbank — Agent Talimatı

Bu dosya proje genelinde bağlayıcıdır. Teknik doğruluk ve veri güvenliği, hızdan önce gelir.

## Hedef runtime

- Python: 3.12–3.14 (geliştirme ortamı: 3.14.6)
- Django: **6.1.x** (pin: 6.1.2)
- Veritabanı: PostgreSQL
- Proje kökü (manage.py): `Backend/config/`

Framework sürüm matrisi: [Django 6.1 FAQ — install](https://docs.djangoproject.com/en/6.1/faq/install/) · [6.1 release notes](https://docs.djangoproject.com/en/6.1/releases/6.1/) · [Download](https://www.djangoproject.com/download/)

## Django docs vs proje skill’leri

- **Django resmi dokümantasyonu ve kaynak kodu:** Framework’ün doğru kullanımı için normatif referanstır (API, güvenlik, test, migration).
- **Proje skill’leri (`.cursor/skills/`):** Yalnızca Kuyumbank iş/mimari kurallarını taşır. Django ekibinin “resmî Kuyumbank skill’i” değildir; Django docs skill yerine geçmez, skill de Django docs yerine geçmez.

## Kaynak önceliği

1. Bu `AGENTS.md`
2. `docs/analysis/` ve kanonik rapor: `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md`
3. `docs/architecture/`
4. `docs/decisions/` (onaylı ADR’ler; faz kodu ilgili ADR **Kabul** + açık talimat olmadan başlamaz — örn. Faz 1: ADR-0003, Faz 2: ADR-0005/0006, Faz 3a: ADR-0007; dosya organizasyonu ADR-0004)
5. Django 6.1 resmi dokümantasyonu: https://docs.djangoproject.com/en/6.1/
6. Django kaynak kodu: https://github.com/django/django
7. Üçüncü taraf kütüphanelerin resmi dokümantasyonu

Rastgele blog, AI skill veya kod örneğini otorite kabul etme. Django dokümantasyonunda olmayan özelliği varmış gibi davranma.

## Ek kural A — Kanıtlanmamış bulgu yok

Her denetim bulgusu şu etiketlerden biriyle yazılır:

- **DOĞRULANDI:** Kod (dosya/satır) veya çalıştırılmış komutla kanıtlandı.
- **DOĞRULANAMADI:** Ortam, veri veya erişim eksik; kanıt yok.
- **PLANLAMA BULGUSU:** Mimari analizden çıktı; runtime test yok.

Dosya/satır referansı olmayan teknik bulgu kesin gerçek gibi yazılmaz. Çalıştırılmayan test başarılı gösterilmez.

## Ek kural B — Faz 0 değişiklik sınırı

Faz 0 süresince:

- Backend uygulama Python dosyalarına dokunulmaz.
- Model, migration, view, serializer, service değiştirilmez.
- Veritabanı şeması değiştirilmez; üretim DB’ye bağlanılmaz.
- Mevcut Git değişiklikleri korunur (ezilmez).
- `requirements.txt` yalnızca projenin gerçekten kullandığı paketleri listeler; ortamda olup kodda olmayan paket eklenmez.
- Faz 1’e kendiliğinden geçilmez.

Faz sonunda oluşturulan/değiştirilen dosyalar listelenir; uygulama kodunun değişmediği Git ile doğrulanır.

## Ek kural C — Fayda/Maliyet ve Geliştirme Verimliliği

Ek kural A–B ve güvenlik/mimari/veri bütünlüğü kurallarını **zayıflatmaz**; onlarla birlikte uygulanır. Hedef: sürekli denetim değil, çalışan yazılım (~%70 geliştirme, %20 gerekli test, %10 dokümantasyon/borç).

### Öncelik sırası

1. İşlevsel gereksinimi doğru tamamla  
2. Veri güvenliği ve ticari doğruluğu koru  
3. Kritik hataları önle  
4. Gerekli testleri çalıştır  
5. Gereksiz mükemmelleştirme ve tekrarı önle  
6. Token ve süreyi verimli kullan  

Her kontrolün maliyeti ile faydası karşılaştırılır. Hız uğruna kalite düşmez; kalite adına proje bitirilemez hale gelmez.

### Analiz sınırı

- Yalnızca görevle ilgili dosyaları incele; tüm projeyi yeniden tarama.  
- Önceki uygulama raporları / doğrulanmış ADR kararlarını yeniden analiz etme.  
- Bağlamda olan dosyayı tekrar okuma; aynı bilgiyi birden fazla kaynaktan toplama.  
- Belirsizlik yoksa yeni ADR üretme; net gereksinimde kullanıcıya gereksiz soru sorma.

### Kodlama

- Analiz yeterliyse doğrudan kodla; önce küçük tamamlanabilir değişiklik.  
- Mevcut mimariyi koru; gereksiz refactor / “daha güzel” rewrite yok.  
- Kapsam dışı teknik borcu ayrı not et; dilimde ilgisiz problem çözme; istenmeyen özellik ekleme.

### Test — risk bazlı (üç seviye)

1. **Değişiklik:** yalnız ilgili yeni/değişen testler; ilgisiz suite yok.  
2. **Etki:** etkilenen servis/model/yetki/izolasyon; PostgreSQL kısıtlarını SQLite ile “geçti” sayma.  
3. **Dilim kapanış:** genel kontroller + tam paket **bir kez**; sebepsiz tekrar yok.  

Hata: ilişkisini belirle → ilgiliyse düzelt → başarısız testi → etkilenen grup. Her mikro düzeltmeden sonra tam paketi yeniden koşma. K-007/K-008 tarzı PG/ticari kısıtlar atlanmaz; küçük değişiklikte tüm suite şart değildir.

### BUG sınıfları

- **P0:** güvenlik, firma sızıntısı, veri kaybı, yanlış finans → derhal.  
- **P1:** mevcut dilim işlevini bozar → dilimde düzelt.  
- **P2:** kapsam dışı / borç / kozmetik → kaydet, akışı durdurma.  

P2 için otomatik yeni denetim turu başlatma.

### Tekrar / token

Aynı analizi, uzun mimari özeti, kanıtlanmış kararı veya başarılı komutu gerekçesiz tekrarlama. Düzeltilebileni çöz-doğrula-devam et; engelde yalnız gerçek engel + gereken karar.

### Durdurma

Aynı sorun için iki makul düzeltme denemesinden sonra geniş analiz yok; kısa neden + kanıt + karar isteği.

### Dilim tamamlanma

İş gereksinimi + kritik güvenlik/bütünlük + ilgili testler + migration incelemesi + genel sonuç raporu + açık riskler. Sıfır borç hedefi yok; yönetilebilir belgelenmiş borçla ilerle.

## Skill yükleme

Görevle ilgili **yalnızca bir** skill oku:

| Görev | Skill |
|-------|--------|
| Model, ORM, servis, migration, admin | `.cursor/skills/django-engineering/SKILL.md` |
| Tenant, RBAC, kör havuz, API yetki | `.cursor/skills/multi-tenant-security/SKILL.md` |
| Katalog, teklif, fiyat, stok, sipariş kuralları | `.cursor/skills/business-domain/SKILL.md` |
| Test yazma / çalıştırma / kalite | `.cursor/skills/testing-quality/SKILL.md` |

## Geliştirme fazları (sıra bağlayıcı)

1. **Faz 0** — Standartlar ve denetim (tamamlandıktan sonra beklenen: talimat)
2. **Faz 1** — Firma, kullanıcı, roller, izinler, platform, firma izolasyonu
3. **Faz 2** — Kategori, ürün, varyant, özellikler, görseller
4. **Faz 3** — Tedarikçi teklifi, fiyatlama, fiyat snapshot  
   - **3a (ADR-0007 Kabul):** dilim **3.1** teklif yaşam döngüsü + **3.2** K-007/K-008 uygulandı (WIP commit ayrı olabilir)  
   - **3b (ADR-0008 Taslak):** kur / quote — Kabul olmadan kod yok
5. **Faz 4** — Stok hareketi / rezervasyon / bakiye + sipariş yaşam döngüsü
6. **Faz 5** — Ödeme, tahsilat, cari, komisyon, finansal hareket
7. **Faz 6** — Kalite kontrol, lojistik, teslimat, iade
8. **Faz 7** — API standartları, dış sistemler, SAP
9. **Faz 8** — Performans, güvenlik, loglama, izleme, yedek, deployment

Firma izolasyonu ve yetkilendirme yanlış kurulursa sonraki tüm modüller bozulur. Bir faz bitmeden ilgisiz modüle geçme.  
Canlı envanter: `docs/architecture/mevcut-mimari.md`.

## Temel iş kuralları

- Her kullanıcı yalnızca **bir** firmaya bağlıdır.
- Platform firması tekildir; platform yöneticileri platform genelinde yetkilidir.
- Firma kullanıcıları yalnız yetkili oldukları firma verisine erişir.
- Alıcı ve tedarikçi birbirinin kimlik/ticari bilgisini doğrudan görmez (kör havuz).
- Ürün / varyant / tedarikçi teklifi ayrılır; katalog platforma aittir.
- Fiyatlama: altın + milyem + işçilik + ek maliyet + ticari kurallar; siparişte snapshot zorunlu.
- Stok rezervasyonu, stok hareketi ve stok bakiyesi ayrı kavramlardır.
- Finansal işlemler denetlenebilir; kritik işlemler audit’e yazılır.
- Sipariş, RFQ, ödeme, QC, lojistik kontrollü durum geçişleriyle ilerler.

Alanın modelde bulunması kuralın uygulandığı anlamına gelmez.

## Teknik standartlar

- Django public API; gereksiz custom framework yok.
- İş mantığı view/serializer’da yığılmaz; domain service kullanılır.
- **Dosya organizasyonu (ADR-0004):** `models/`, `services/`, `selectors/`, `admin/`, `serializers/`, `views/`, `tests/` — sorumluluğa göre ayrı dosyalar; circular import yok; onaysız toplu refactor yok.
- N+1’den kaçın; indeksler gerçek sorguya göre.
- Kritik yazmalar: `transaction.atomic()`; stok/finans yarışlarında satır kilidi + DB kısıtı.
- Para ve metal: `Decimal`.
- Yetki her endpoint’te; client’tan gelen `firma_id` / `tedarikci_id` güvenilmez.
- Secret/parola/API anahtarı koda yazılmaz; hassas veri loglanmaz.
- Kullanılmayan kod ve ölü soyutlama bırakılmaz.
- Her fazda değişen dosyalar ve sorumlulukları raporlanır.

## Test ve tamamlanma

Yeni özellik: model + service + (varsa) API + yetkilendirme + firma izolasyonu + sınır durum testleri. Eşzamanlılık riski varsa PostgreSQL üzerinde test.

Görev ancak şunlarla tamamlanır: gereksinim karşılandı, mimariye uydu, güvenlik kontrol edildi, testler yazıldı ve **çalıştırıldı**, migration incelendi, riskler açıklandı.

Çalıştırılmayan testi başarılı gösterme.

## Yasaklar

- `.env` / secret / token çıktıya yazma
- Üretim DB’ye izinsiz bağlanma; üretimde migration
- DB silme/sıfırlama; onaylanmamış yıkıcı işlem
- Kullanıcının Git değişikliklerini ezme

## Çıktı formatı

**Tamamlananlar** — yapılan değişiklikler  
**Testler** — komutlar ve sonuçlar  
**Riskler** — kalan sorunlar  
**Sonraki faz** — bir sonraki somut adım

## Belirsizlik

Gereksinim açıksa uygula. Eksik detayda iş kurallarına en uygun varsayımı seç, `docs/decisions/` altına ADR yaz, geri dönüşü kolay tut. Veri kaybı, finansal doğruluk, güvenlik veya geri döndürülemez mimari kararda tahmin etme; dur ve kararı bildir.
