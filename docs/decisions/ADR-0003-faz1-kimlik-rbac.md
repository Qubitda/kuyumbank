# ADR-0003 — Faz 1 kimlik, RBAC ve tenant kararları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onaylayan:** Proje sahibi (dört karar + ek güvenlik kriteri)  
**Bağlı tasarım:** [`docs/architecture/faz1-kimlik-gecis-tasarimi.md`](../architecture/faz1-kimlik-gecis-tasarimi.md)  
**Kaynak:** `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md` §5.1, §8, K-002…K-005

**Uygulama notu:** Bu ADR onaylı mimari karardır. Ayrı açık talimat olmadan kod, migration veya model değişikliği yapılmaz.

---

## ADR-0003-01 — Platform rolleri: raporun 8 rolü kanonik

### Karar

İş analizindeki **8 platform rolü** kanonik listedir. Mevcut 3 platform rolü bu sekize eşlenir; gelişigüzel ekstra platform rolü eklenmez.

### Kanonik platform rolleri (rapor §5.1)

| Kod | Açıklama |
|-----|----------|
| `platform_super` | Platform üst yönetim |
| `platform_admin` | Platform yönetim |
| `platform_ops` | Platform operasyon |
| `platform_finance` | Platform finans |
| `platform_catalog` | Platform katalog |
| `platform_quality` | Platform kalite |
| `platform_logistics` | Platform lojistik |
| `platform_support` | Platform destek |

### Mevcut → kanonik eşleme

| Mevcut kod | Kanonik | Geçiş |
|------------|---------|--------|
| `platform_super` | `platform_super` | Birebir |
| `platform_admin` | `platform_admin` | Birebir |
| `platform_ops` | `platform_ops` | Birebir |
| — | `platform_finance` … `platform_support` | Yeni choices + seed; kullanıcı ataması operasyonel |

### Kurallar

1. Platform rolleri ile firma rolleri (alıcı / tedarikçi) **ayrı kümelerdir**; aynı yetki kümesini paylaşmaz.
2. **Platform yöneticisi ≠ firma yöneticisi.** `platform_admin` ile `alici_yonetici` / `tedarikci_yonetici` permission setleri farklıdır.
3. Varsayılan: kullanıcıya **tek** iş rolü. Çoklu rol ihtiyacı ayrı ADR ister; rol karmaşası oluşturulmaz.
4. Rol kodları string literal olarak dağılmaz: tek sabit kaynak (ör. `firmalar.roles` / enum benzeri modül) + Group adı `rol:<kod>`.
5. Karşılığı olmayan eski bir rol ileride çıkarsa: kaldırılmadan önce veri geçiş planı zorunlu (bu ADR’de mevcut 3 platform rolünün hepsi kanonikte var; silme yok).

### Sonuçlar

- `PLATFORM_ROLLERI` seti 8 kod olacak.
- Alıcı/tedarikçi rol listeleri raporla uyumlu mevcut setle korunur (Faz 1’de değiştirilmez) — ayrı ADR olmadıkça.

---

## ADR-0003-02 — `Kullanici.firma` NOT NULL; superuser firmasız olamaz

### Karar

İş kuralı kesin: **her kullanıcı tam olarak bir firmaya bağlıdır.**  
`firma` alanı Faz 1 içinde **NOT NULL** yapılır. Superuser olmak firmasız olmak demek değildir.

### Geçiş sırası (bağlayıcı)

1. Mevcut `firma` alanı ile geçiş başlar (`null=True` geçici kalır).
2. Firması olmayan kullanıcılar tespit edilir (audit komutu / sorgu).
3. Platform yöneticileri / platform personeli **Kuyumbank Platform** firmasına bağlanır.
4. Diğer kullanıcıların firmaları doğrulanır ve backfill yapılır.
5. Veri bütünlüğü kontrol edilir (sıfır `firma_id IS NULL`).
6. Alan **NOT NULL** (+ uygulama `clean`/`save` zorunluluğu) yapılır.
7. DB constraint ve uygulama kuralı birlikte korunur.

### Superuser / tenant politikası

- `is_superuser=True` → `firma` yine zorunlu (tercihen platform firması).
- `is_superuser`, tenant izolasyonunu **otomatik aşamaz**.
- Platform genelinde işlem: açık permission / politika ile; kritik işlemler **audit**’e yazılır.
- İş servislerinde `if user.is_superuser: allow` kalıbı kaldırılır veya break-glass + audit ile sınırlanır (Faz 1 uygulama tasarımında detaylanır; bu ADR ilkeyi sabitler).

### Sonuçlar

- `createsuperuser` sonrası veya özel komutla platform firma + uygun rol ataması zorunlu.
- Test tabanları firmasız superuser ile kurulmaz.

---

## ADR-0003-03 — K-004 `onaya_gonder` sahiplik kontrolü Faz 1 acceptance’ta

### Karar

`onaya_gonder` için sahiplik ve yetkilendirme Faz 1 **zorunlu acceptance** kriteridir. Onay iş akışının tamamını yeniden tasarlamak Faz 1 kapsamı değildir.

### Acceptance (minimum)

1. Kaydın sahibi firma doğrulanır (`urun.tedarikci_id` ile kullanıcı firması).
2. Kullanıcı o firmaya bağlıdır.
3. Yetkisiz kullanıcı işlemi yapamaz (rol/permission).
4. ID değiştirerek başka firma nesnesi üzerinden işlem yapılamaz (IDOR).
5. Başarılı/başarısız kritik denemeler gerektiği ölçüde audit edilir.

### Sonuçlar

- `urunler.services.onay_servisi.onaya_gonder` sahiplik + yetki kontrolü alır.
- Şema değişikliği gerekmez; servis + test + (gerekiyorsa) audit kaydı.

---

## ADR-0003-04 — Permission’lar ilgili uygulamaların modellerinde

### Karar

Permission tanımları **dağıtık** `Meta.permissions` (veya ilgili model) üzerindedir. Tüm permission’ları `firmalar` altına yığmak yasaktır.

| Konu | Tanım yeri |
|------|------------|
| Firma yönetimi | `firmalar` / `Firma` |
| Kullanıcı yönetimi | `firmalar.Kullanici` |
| Ürün yönetimi | `urunler.Urun` (ve ilgili katalog modelleri) |
| Tedarikçi teklifleri | `fiyatlama` ilgili model (`TedarikciTeklif` vb.) |
| Fiyat / sözleşme | `fiyatlama` ilgili model |
| Sipariş | İleride sipariş app/modeli |

### Rol ↔ permission politikası

- Eşleştirme **merkezi politika** ile yönetilir (tek seed/policy modülü).
- Seed **idempotent**tir: tekrar çalışınca çoğalmaz.
- Runtime yetki kararı: Django `has_perm` / ince wrapper; rol string switch dağılmaz.
- Group `rol:<kod>` yalnızca senkron taşıyıcıdır; asıl yetki permission kodlarındadır.

---

## ADR-0003-05 — Tenant izolasyonu çok yüzeyli test zorunluluğu

### Karar

Tenant izolasyonu yalnızca “normal kullanıcı API” için değil; **Django Admin, superuser politikası, domain servisler ve ilişkili nesne erişimi** için ayrı ayrı test edilmeden Faz 1 tamamlanmış sayılmaz.

### Zorunlu senaryolar (hepsi çalıştırılmış + yeşil)

1. Firma A kullanıcısı Firma B kaydını **listeleyemez**.
2. Firma A kullanıcısı Firma B kaydını **ID ile getiremez**.
3. Firma A kullanıcısı Firma B kaydını **değiştiremez / silemez**.
4. Firma A kullanıcısı Firma B’ye ait **ilişkili nesne** üzerinden işlem yapamaz.
5. Firma yöneticisi **platform yetkilerini kullanamaz**.
6. Platform yetkilisi yalnızca kendisine tanımlanan **platform izinlerini** kullanabilir.
7. Superuser davranışı bu ADR’deki politikaya uygundur (firma zorunlu; tenant’ı sessizce aşmaz).

Kanıt: çalıştırılan test komutları ve sonuçları (Ek kural A: DOĞRULANDI). Çalıştırılmayan test başarılı gösterilmez.

---

## Özet tablo

| No | Karar |
|----|--------|
| ADR-0003-01 | Raporun 8 platform rolü kanonik; mevcut 3 eşlenir; tek rol varsayılan; string dağılmaz; platform ≠ firma yöneticisi |
| ADR-0003-02 | Tüm kullanıcılar `firma` NOT NULL; superuser firmasız olamaz; superuser tenant’ı otomatik aşamaz |
| ADR-0003-03 | K-004 sahiplik Faz 1 acceptance; tam onay workflow redesign değil |
| ADR-0003-04 | Permission’lar ilgili app/model `Meta.permissions`; rol eşlemesi merkezi idempotent seed |
| ADR-0003-05 | Admin + superuser + servis + ilişkili nesne izolasyon testleri zorunlu |

## Non-goals (bu ADR kapsamı dışı)

- Katalog platform ownership refactor (Faz 2)
- DRF `/api/v1/` (Faz 7)
- Production migrate
- Kod uygulaması (ayrı kullanıcı talimatı gerekir)
