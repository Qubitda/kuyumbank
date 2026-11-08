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
4. `docs/decisions/` (onaylı ADR’ler; Faz 1 için ADR-0003 bağlayıcı — ayrı talimat olmadan kodlama yok; dosya organizasyonu ADR-0004)
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
5. **Faz 4** — Stok hareketi / rezervasyon / bakiye + sipariş yaşam döngüsü
6. **Faz 5** — Ödeme, tahsilat, cari, komisyon, finansal hareket
7. **Faz 6** — Kalite kontrol, lojistik, teslimat, iade
8. **Faz 7** — API standartları, dış sistemler, SAP
9. **Faz 8** — Performans, güvenlik, loglama, izleme, yedek, deployment

Firma izolasyonu ve yetkilendirme yanlış kurulursa sonraki tüm modüller bozulur. Bir faz bitmeden ilgisiz modüle geçme.

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
