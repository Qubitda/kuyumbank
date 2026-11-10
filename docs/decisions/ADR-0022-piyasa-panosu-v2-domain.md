# ADR-0022 — Piyasa panosu v2 domain (GoldXT hizası; backend)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “go onaylıyorum”)  
**Bağımlılık:** ADR-0020 **Kabul** (çekirdek korunur); ADR-0018 kur; ADR-0014 karlılık sim  
**Kapsam ID:** CAP-PANO-v2 — [BACKLOG](../BACKLOG.md) · [MASTER](../MASTER.md) §12  
**Referans davranış:** GoldXT panosu (alış/satış + Marj Ayarları) + `margin_calc` P&L — **HTML port yok**; domain/servis sözleşmesi

## Neden

ADR-0020 çekirdeği (`baz_fiyat`, `PANO`|`MANUEL`, metal/ayar FK, alış↓/satış↑ marj) doğru yönde.  
Ürün sahibi değerlendirmesi (2026-11-10): mevcut `piyasa` altyapısı GoldXT beklentisinden **uzak** — eksik katalog yapısı, darphane işçiliği, birimli kesintiler, metal/ayar üzerinden doğrudan sim.

Bu ADR **yalnız backend domain + servis sözleşmesini** netleştirir. FE/Next ayrı (backend-first).

## Korunan (ADR-0020 — değiştirilmez)

| ID | Koruma |
|----|--------|
| V2-0a | App `piyasa`; ham kur `tanimlar.MetalKuru` / `kur_servisi` (ADR-0018). |
| V2-0b | Metal/ayar **yalnız** `tanimlar` FK; pano içinde yeni metal/ayar açılmaz. |
| V2-0c | Pano marjı: alış marjı ≥0 **düşer**, satış marjı ≥0 **ekler** (TL veya %). |
| V2-0d | `baz_fiyat` / `pano_ozeti` / `cozumle_islem_birim_fiyati(PANO|MANUEL)` tek giriş kalır. |
| V2-0e | Kar sim ledger/quote/order **yazmaz**. Quote bağlama hâlâ PP-9 (ayrı talimat). |

## Kararlar (onaya sunulan)

### A — Pano kataloğu

| ID | Karar | Öneri |
|----|--------|--------|
| V2-1 | `PiyasaUrun`’a **grup** eklenir (`HAS`, `GUMUS`, `SARRAFIYE`, `AYAR_GRAM`, `DIGER` … TextChoices veya `PiyasaGrup` FK). Sıra: grup.sira → urun.sira. | **Kabul önerisi** |
| V2-2 | Opsiyonel `varyant_etiket` (ör. `YENI` / `ESKI` / boş) — sarrafiye çift satırları için; hesap formülü aynı. | **Kabul önerisi** |
| V2-3 | Çapraz satırlar (ONS USD, TL/KG, …): ya ayrı `PiyasaUrun` (metal+çarpan/gram politikası seed’de) ya da v2.1’e ertelenir. | → **[ADR-0025](ADR-0025-pano-ons-kg.md) UYGULANDI** |

### B — Marj politikası

| ID | Karar | Öneri |
|----|--------|--------|
| V2-4 | **Global marj modu** (`PiyasaMarjPolitikasi` tekil satır veya `KurPolitikasi` eklentisi): `TL` \| `YUZDE` — tüm aktif ürün satırlarına uygulanır. Ürün satırındaki `marj_modu` **kaldırılır** veya salt okunur türetilir. | **Kabul önerisi: global** (GoldXT sağ panel) |
| V2-5 | Satırda yalnız `alis_marj` / `satis_marj` (≥0) + yuvarlama alanları kalır. | **Kabul önerisi** |

### C — Darphane / sabit işçilik tablosu

| ID | Karar | Öneri |
|----|--------|--------|
| V2-6 | Yeni model `DarphaneIscilik`: `urun` → `PiyasaUrun` (veya kod), `kanal` = `YENI_HAS` \| `ESKI_HAS` \| `BORSA_HAS`, `iscilik_tl` ≥0, aktif, sira. | **Kabul önerisi** |
| V2-7 | Pano `baz_fiyat` hesabına **otomatik eklenmez** (GoldXT’te ayrı tablo). Kar sim / iç işlem Katman-2 isteğe bağlı bu tablodan okuyabilir. | **Kabul önerisi** |

### D — Kar simülasyonu (margin_calc hizası)

| ID | Karar | Öneri |
|----|--------|--------|
| V2-8 | `karlilik_simulasyonu` kesintileri **birimli** olur: banka / işletme / GV / diğer için `tip` = `YUZDE` \| `TL` + `deger`. Mevcut % default’lar (2 / 1 / 20) geriye uyumlu varsayılan. | **Kabul önerisi** |
| V2-9 | Giriş yolu A: mevcut `urun_kod` → pano baz birim. Giriş yolu B: **metal + ayar** (+ isteğe `taraf`) → `kur_servisi` × milyem; `PiyasaUrun` zorunlu değil. | **Kabul önerisi** |
| V2-10 | Platform varsayılan kesinti: `PiyasaKarPolitikasi` (tekil; banka/işletme/GV/diğer birim+değer). Admin düzenler; sim bunu default alır, çağrı override edebilir. | **Kabul önerisi** |
| V2-11 | Formül korunur (ADR-0014): `gr_maliyet = maden + iscilik_tl`; Mod A kar%; Mod B hedef toplam; net = brut − kesintiler. | **Kabul önerisi** |

### E — Servis yüzeyi (FE değil; Python API)

| ID | Karar | Öneri |
|----|--------|--------|
| V2-12 | `pano_ozeti()` çıktısına `grup`, `varyant_etiket`, `marj_modu` (global), ham/marjlı ara adımlar eklenir. | **Kabul önerisi** |
| V2-13 | `darphane_iscilik_listesi()` + `kar_yardimcisi.simule_*` birimli kesinti + metal/ayar yolu. | **Kabul önerisi** |
| V2-14 | HTTP/OpenAPI bu ADR’de **yok** (admin + servis yeterli; B7 ayrı dilim). | **Kabul önerisi** |

### F — Doküman / durum

| ID | Karar | Öneri |
|----|--------|--------|
| V2-15 | ADR-0020 “UYGULANDI” = **çekirdek v1**. CAP-PANO-v2 bu ADR Kabul + uygulama sonrası ayrı UYGULANDI. | **Kabul önerisi** |
| V2-16 | ADR-0020 metnindeki `PiyasaFiyatKurali` ifadesi tarihsel; v1 sonrası marj ürün satırında / v2’de global politika. | **Kabul önerisi** |

## Bilinçli dışarıda

- Next.js / GoldXT HTML port / TradingView  
- Quote/Order otomatik bağlama (PP-9)  
- Celery websocket canlı push  
- ONS/KG çapraz ürün seti (V2-3 erteleme seçilirse)

## Uygulama dilimleri (Kabul sonrası — kod yok)

1. Model + mig: grup/varyant + global marj politikası + `DarphaneIscilik` + `PiyasaKarPolitikasi`  
2. `hesap` / `piyasa_fiyat_servisi` / seed güncelle  
3. `karlilik_simulasyonu` birimli kesinti + test  
4. `kar_yardimcisi` çift giriş + admin form alanları  
5. Odaklı `piyasa.tests` + `fiyatlama.tests.test_karlilik_*`

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul (V2-1…16) | **Evet** (2026-11-10, Qubit) |
| Model + migration | **UYGULANDI** (`piyasa.0003`) |
| Servis + test | **UYGULANDI** (`piyasa.tests` + karlilik **21 OK**) |
| Admin | **UYGULANDI** |
| HTTP | Bu ADR’de yok |

## İlişkili

- [ADR-0020](ADR-0020-piyasa-panosu-baz-fiyat.md) · [ADR-0014](ADR-0014-karlilik-simulasyonu.md) · [ADR-0018](ADR-0018-cap-piyasa-kur-dayanikliligi.md)  
- BACKLOG `[CAP-PANO-v2]` · MASTER §12.3
