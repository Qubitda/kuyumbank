# ADR-0020 — Piyasa panosu (baz fiyat) + kar yardımcısı + işlem fiyat seçimi

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — açık onay + uygulama talimatı)  
**Bağımlılık:** ADR-0008 (kur/quote), ADR-0018 (CAP-PIYASA LKG/banner), ADR-0014 (karlılık sim; yeniden kullan)  
**Kapsam ID:** CAP-PANO — [BACKLOG](../BACKLOG.md) · [MASTER](../MASTER.md) §12  
**Referans UX:** GoldXT panosu / WhatsApp dernek listesi (işlenmiş alış–satış; ham kur panoya yazılmaz)

## Amaç

1. Canlı ham metal kurundan (**`MetalKuru`**) platform **baz fiyat panosu** üretmek (alış ≠ satış, işaretli işçilik/marj, yuvarlama).
2. Panoyu **Django Admin**’den yönetmek.
3. Aynı alanda **kar hesaplama yardımcısı** (ADR-0014 simülasyonunu pano baz fiyatıyla beslemek).
4. İç işlemlerde kullanıcının **pano değeri** (isteğe bağlı Katman-2 ek) **veya manuel birim fiyat** seçebilmesi.

## İki katman

| Katman | Sahip | Anlam |
|--------|-------|--------|
| 1 — Baz fiyat | Platform / admin | Ham × milyem × gram + işaretli işçilik/marj + yuvarlama → panodaki “bizim fiyatımız” |
| 2 — Kullanıcı ekleri | Kullanan kişi (opsiyonel) | Bazın üstüne marj / servis / işçilik; bazı **değiştirmez** |

Tek giriş (hesaplayıcılar): `piyasa.services.piyasa_fiyat_servisi.baz_fiyat(urun_kod)` → `alis` / `satis`.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| PP-1 | Yeni app `piyasa` (ADR-0004 paket düzeni). Ham kur `tanimlar`; ticari quote gerçeği `fiyatlama` — pano **ayrı** yayın yüzeyi. |
| PP-2 | Modeller: `PiyasaUrun` (kalem + yuvarlama) + `PiyasaFiyatKurali` (ürün×taraf; işaretli işçilik/marj; PB TRY/USD/EUR/GBP). |
| PP-3 | Saf matematik `piyasa.services.hesap` — Django’suz Decimal; ara adımda yuvarlama yok. |
| PP-4 | Ham kur her hesapta `kur_servisi.resolve_metal_kuru_detay` (ADR-0018); stale → LKG+banner; sessiz LKG yok; `0` fiyat yok. |
| PP-5 | Taraf: panoda `ALIS`/`SATIS`. Metal çözüm: `ALIS`→`KurTaraf.TEDARIKCI`, `SATIS`→`KurTaraf.ALICI`. |
| PP-6 | Admin: ürün + kural CRUD (`manage_piyasa`); listede canlı baz alış/satış; **kar yardımcısı** admin URL. |
| PP-7 | İç işlem fiyat seçimi: `PANO` \| `MANUEL` — kullanıcıya kalmış; servis `cozumle_islem_birim_fiyati`. |
| PP-8 | Kar yardımcısı: ADR-0014 `karlilik_simulasyonu` çağrısı; ledger/quote yazmaz. |
| PP-9 | PriceQuote / OrderLine bağlama → **[ADR-0024](ADR-0024-pano-quote-baglama.md)** **UYGULANDI**. |

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10, Qubit) |
| Model + migration | Bu dilim |
| Servis (baz / seçim / kar) | Bu dilim |
| Admin yönetimi + kar yardımcısı | Bu dilim |
| Quote/Order bağlama | **UYGULANDI** (ADR-0024) |

## İlişkili

- Test: `piyasa.tests`
- GoldXT: davranış özeti; Django’ya HTML port yok
- **Domain genişletme:** [ADR-0022](ADR-0022-piyasa-panosu-v2-domain.md) (**Taslak** — grup/darphane/birimli kesinti/global marj; ürün sahibi onayı)
