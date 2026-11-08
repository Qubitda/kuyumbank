# KUYUMBANK — Ana Proje Dokümanı (Master)

**Dosya:** `docs/KUYUMBANK_MASTER.md`  
**Rol:** Kuyumbank’ın **tek kanonik** ürün, mimari, karar, tarihçe, yol haritası ve iş havuzu kaynağı.  
**Güncelleme:** 2026-11-08 — Dilim 3.7 (PriceLock L-01…L-10 kod) + docs sadeleştirme  
**Dal:** `adim-1-ilerleme`  
**Doküman kökü:** yalnız bu dosya (`docs/` altında analysis / architecture / decisions klasörü **yok**).

> Cursor Agent / geliştirici: önce `AGENTS.md`, sonra **bu dosya**. Yeni faz raporu / ikinci yol haritası / dağınık backlog / ayrı ADR dosyası **üretilmez**; değişiklikler buraya işlenir.

---

## İçindekiler

1. [Proje tanımı ve vizyon](#1-proje-tanımı-ve-vizyon)
2. [Mevcut sistemin gerçek durumu](#2-mevcut-sistemin-gerçek-durumu)
3. [Mimari ve teknik standartlar](#3-mimari-ve-teknik-standartlar)
4. [Ürün domainleri](#4-ürün-domainleri-ve-işleyiş)
5. [Kuyumculuk sektörü gereksinimleri](#5-kuyumculuk-sektörü-gereksinimleri)
6. [Karar kayıtları (ADR birleşik)](#6-geçmişte-alınan-kararlar-adr-birleşik-kayıt)
7. [Faz uygulama tarihçesi](#7-geçmiş-fazlar-ve-uygulama-geçmişi)
8. [Hedef mimari ve Prosperer gap](#8-hedef-mimari-ve-prosperer-gap-analizi)
9. [Geliştirme yol haritası](#9-ana-geliştirme-yol-haritası)
10. [İş havuzu](#10-iş-havuzu-kanonik)
11. [Ürün sahibi karar bekleyenler](#11-ürün-sahibi-karar-bekleyen-konular)
12. [Güncel durum ve sıradaki adım](#12-güncel-proje-durumu-ve-sıradaki-adım)

**Durum etiketleri (özellikler):** `UYGULANDI` · `TEST EDİLDİ` · `KISMİ` · `PLANLANDI` · `KARAR BEKLİYOR` · `DOĞRULANAMADI`

---

## 1. Proje tanımı ve vizyon

### 1.1 Nedir?

**Kuyumbank**, kuyumculuk sektörüne özel bir **Jewelry B2B Commerce & Trading Platform**’udur. Katalog, tedarikçi pazaryeri, dinamik fiyatlama, teklif, fiyat kilidi, stok, sipariş, finans, üretim, kalite kontrol, lojistik ve satış sonrasını **tek kapalı devre** platformda birleştirmeyi hedefler.

### 1.2 Problem

Açık pazaryerlerinde alıcı–tedarikçi kimlik sızıntısı, dağınık fiyat/kur, stok çift satışı ve denetimsiz sipariş riski yüksektir. Kuyumbank platform aracılığıyla **kör havuz** ticareti, **değişmez fiyat snapshot**’ı ve kontrollü operasyon sağlar.

### 1.3 Hedef kullanıcılar ve roller

| Rol | Görür | Görmez |
|-----|-------|--------|
| **Alıcı firma** | Platform kataloğu, kendine sunulan fiyat/koşul, kendi sipariş/belge | Tedarikçi kimliği, iç maliyet, iç SKU, platform marj kırılımı (hukuk onayı yoksa) |
| **Tedarikçi firma** | Kendi teklifleri, atanmış işler, kendi stok yüzeyi | Alıcı kimliği, diğer tedarikçi teklifleri |
| **Platform** | Yetki matrisindeki operasyon + audit | — |

Her kullanıcı **tek firmaya** bağlıdır; platform firması tekildir (ADR-0003).

### 1.4 Ticari model

Platform katalog sahibidir. Tedarikçiler varyanta teklif verir. Alıcı fiyatı platform quote’undan gelir (ham tedarikçi maliyeti değil). Siparişte fiyat kilitlenir/snapshot alınır; sonraki kur/sözleşme geçmişi değiştirmez.

### 1.5 Prosperer seviyesi

Hedef: **HYCOM Prosperer sınıfı** B2B Commerce yetenek seti (katalog, fiyat listesi, sepet/sipariş, stok, finans, portal, entegrasyon). Prosperer’ın tek tek özellikleri bu repoda **runtime ile DOĞRULANAMADI**; kıyas ürün sahibi hedef çerçevesidir.

**Ayrışma (kuyumculuk):** metal/ayar/milyem/gram, kur zaman damgası, quote TTL + PriceLock, kör çoklu teklif, taş maliyeti (K-011), ileride QC gram toleransı, konsinye/emanet, özel üretim/RFQ.

---

## 2. Mevcut sistemin gerçek durumu

**Kanıt önceliği:** kod/migration/test > kabul ADR > son faz raporu.  
**Kod kökü:** `backend/config/` · **Python** 3.12–3.14 (dev 3.14.6) · **Django** 6.1.2 · **PostgreSQL**.

### 2.1 Teknoloji yığını

| Bileşen | Durum | Etiket |
|---------|-------|--------|
| Django 6.1.2 modular monolith | `requirements.txt` pin | UYGULANDI |
| PostgreSQL + psycopg | varsayılan DB | UYGULANDI |
| django-environ, import-export, Pillow | requirements | UYGULANDI |
| DRF / Celery / Redis / Next.js | requirements’ta yok (bilinçli) | PLANLANDI |
| HTTP yüzeyi | yalnız `admin/` | KISMİ |

### 2.2 Uygulama / paketler (ADR-0004)

`firmalar`, `tanimlar`, `urunler`, `fiyatlama` — her birinde `models/`, `services/`, `selectors/`, `admin/`, `tests/`.

### 2.3 Veri modelleri (özet — kodda var)

| Alan | Modeller | Etiket |
|------|----------|--------|
| Kimlik | `Firma`, `Kullanici`, adres, banka, `AuditOlay` | UYGULANDI |
| Tanımlar | Metal, ayar/milyem, `KurSaglayici`, `KurPolitikasi`, Metal/Döviz kuru, `SatisKanali` (quote TTL) | UYGULANDI |
| Katalog | `Kategori`, `Urun` (`olusturan_firma`), `Varyant`, katalog `UrunTasi` | UYGULANDI |
| Teklif | `TedarikciTeklif` (SM + versiyon), `TeklifTasMaliyeti` (K-011) | UYGULANDI · TEST EDİLDİ |
| Sözleşme | `FiyatSozlesmesi`, kalem, K-007/K-008 | UYGULANDI · TEST EDİLDİ |
| Fiyat | saf hesap + `PriceQuote`/`Line` + immutability trigger | UYGULANDI · TEST EDİLDİ |
| Kilit | `PriceLock` + L-04 TTL guard + L-07 perm | UYGULANDI · TEST EDİLDİ (34 PriceLock + 288 suite OK) |
| Log | `PriceCalculationLog` (ticari truth değil) | UYGULANDI |
| Order/Cart/Stock ledger | — | PLANLANDI |
| RFQ/Payment/QC/Ship | — | PLANLANDI |

**Borç:** `Varyant.stok` / `TedarikciTeklif.stok_adet` ikiliği — ledger yok; Faz 4’te çözülecek.

### 2.4 Servisler / selector’lar

| Servis | Rol | Etiket |
|--------|-----|--------|
| `yetki_servisi` / `rol_servisi` / `audit_servisi` | RBAC, durable fail audit | UYGULANDI |
| `teklif_servisi` / `sozlesme_servisi` | durum geçişleri | UYGULANDI |
| `kur_servisi` / `currency_conversion` | kur + PB | UYGULANDI |
| `fiyat_hesaplama` / `fiyat_motoru` | üç model Decimal | UYGULANDI |
| `pricing_service.quote` / `lock_quote` | snapshot + kilit (L-07 perm + on-behalf gerekçe) | UYGULANDI |
| `buyer_quote` selector | B-02 alıcı yüzeyi | UYGULANDI |
| tenant selectors | firma scope | UYGULANDI |

### 2.5 Güvenlik

- Tenant: selector + admin queryset; `view_all_tenants` yalnız platform+perm (ADR-0003 addendum).  
- Superuser iş kuralı kısa yolu yok.  
- Kör havuz: alıcı satır/maliyet/tedarikçi görmez; IDOR → DoesNotExist.  
- Quote/Lock immutability: uygulama + PostgreSQL trigger.  
- PriceLock create: `fiyatlama.lock_quote` (alıcı) veya `fiyatlama.lock_quote_on_behalf` (platform); `view_all_tenants` tek başına create yetkisi **vermez**.

### 2.6 Test / migration

| Madde | Durum |
|-------|--------|
| Suite (`*.tests` paketleri) | **288 OK** (3.7 L-07 sonrası) — TEST EDİLDİ |
| PriceLock testleri | **34 OK** — TEST EDİLDİ |
| `fiyatlama.0007` PriceQuote trigger | UYGULANDI |
| `fiyatlama.0008–0009` K-011 | UYGULANDI (commit `7802eb4`) |
| `fiyatlama.0010` PriceLock model + immutability | UYGULANDI |
| `fiyatlama.0011` L-04 TTL INSERT guard | UYGULANDI |
| `fiyatlama.0012` L-07 permissions | UYGULANDI |
| DRF API testleri | Yok — PLANLANDI |

### 2.7 Özellik matrisi (çekirdek)

| Özellik | Etiket |
|---------|--------|
| Firma/RBAC/audit | UYGULANDI · TEST EDİLDİ |
| Katalog platform ownership | UYGULANDI · TEST EDİLDİ |
| Teklif SM + versiyon | UYGULANDI · TEST EDİLDİ |
| K-007/K-008 sözleşme | UYGULANDI · TEST EDİLDİ |
| Kur politikası B-04/B-05 | UYGULANDI · TEST EDİLDİ |
| Üç fiyat modeli + CurrencyConversion | UYGULANDI · TEST EDİLDİ |
| PriceQuote immutability | UYGULANDI · TEST EDİLDİ |
| Kör havuz B-02 + K-011 | UYGULANDI · TEST EDİLDİ |
| PriceLock L-01…L-10 (kod) | UYGULANDI · TEST EDİLDİ |
| ADR-0010 resmi ürün Kabul | **KARAR BEKLİYOR** (Taslak; kod kabul sayılmaz) |
| B-01 platform servis payı | KARAR BEKLİYOR (kodlanmadı) |
| B-06 KDV | KARAR BEKLİYOR (ertelendi; proforma) |
| Order / stok ledger / ödeme / DRF | PLANLANDI |
| Prosperer özellik parity | DOĞRULANAMADI (hedef kıyas) |

---

## 3. Mimari ve teknik standartlar

### 3.1 Bağlayıcı (Kabul ADR özeti)

| Konu | Kural | Kaynak |
|------|-------|--------|
| Monolith | Erken mikroservis yok; ADR-0004 paket düzeni | ADR-0004 **Kabul** |
| Runtime | Django 6.1.x pin, PG, requirements yalnız kullanılan paket | ADR-0002 **Kabul** |
| Kimlik | Tek firma + tek rol; full_clean tüm kullanıcılar | ADR-0003 **Kabul** |
| Yetki | `has_perm` / matris; superuser bypass yok | ADR-0003 |
| Tenant | Selector zorunlu; client `firma_id` güvenilmez | ADR-0003-05 |
| Katalog | Platform ownership; `olusturan_firma` | ADR-0005 **Kabul** |
| Teklif | Durum yalnız servis; eşleşme kapısı | ADR-0007 **Kabul** |
| Sözleşme | NULL-safe unique / exclusion | ADR-0007 |
| Fiyat | Üç model; quote immutable; TTL kanal; kör B-02 | ADR-0008 **Kabul** |
| Admin sertleştirme | H1–H5 | ADR-0009 **Kabul** |
| PriceLock L-01…L-10 kod; L-11 Order FK yok | Servis+DB+test | ADR-0010 **Taslak** (resmi Kabul yok) |
| Para | `Decimal`; float yasak | standart |
| Yazım | `domain_atomic`; fail audit durable dışı | audit_servisi |
| Concurrency | `select_for_update` + DB kısıt | standart |
| Migration | Üretim migrate onaysız yok; satır silerek NOT NULL yok | AGENTS |
| API | Henüz yok; gelecek DRF + object-level perm | PLANLANDI |
| Test | Risk bazlı; PG constraint SQLite ile “geçti” sayılmaz | AGENTS Ek C |

### 3.2 Agent / dokümantasyon kuralı

Proje bağlamı için **tek kanonik kaynak bu dosyadır**. `docs/` altında yalnız `KUYUMBANK_MASTER.md` tutulur. Yeni faz raporu, ikinci yol haritası, dağınık backlog, `docs/analysis|architecture|decisions` klasörü veya ayrı `ADR-*.md` **açılmaz**. Geliştirme bitince §2, §7/§10/§12 güncellenir. Büyük kararlar §6’ya ADR ID ile eklenir.

---

## 4. Ürün domainleri ve işleyiş

| Domain | Sorumluluk | Veri (şimdi/hedef) | Durum | Eksik | Bağımlılık |
|--------|------------|-------------------|-------|-------|------------|
| Identity & RBAC | Firma, kullanıcı, rol, audit | `firmalar` | UYGULANDI | Org/şube | — |
| Product Catalog | Ürün, varyant, onay, medya | `urunler` | KISMİ | Search API, zengin medya UI | Identity |
| Supplier Mgmt | Teklif SM, eşleşme | `TedarikciTeklif` | UYGULANDI | Portal UI | Catalog |
| Pricing Engine | Sözleşme, kur, hesap, quote | `fiyatlama`+`tanimlar` | UYGULANDI | B-01, vergi | Supplier |
| PriceLock | Kilit TTL; sipariş bağ | `PriceLock` | UYGULANDI (FK yok) | Order bağ | Pricing |
| RFQ & Quotation | RFQ müzakere | — | PLANLANDI | Tümü | Pricing |
| Cart & Checkout | Sepet, checkout | — | PLANLANDI | Tümü | Lock, Inventory |
| Order Mgmt | SM, snapshot | — | PLANLANDI | Tümü | Cart |
| Inventory & WH | Ledger, rezervasyon | dual alan borç | PLANLANDI | Ledger | Supplier |
| Payments & Finance | Ödeme, cari | — | PLANLANDI | U-* | Order |
| Quality | QC, gram | — | PLANLANDI | Tümü | Order |
| Shipping | Sevkiyat, carrier | — | PLANLANDI | Tümü | QC |
| Returns | İade, uyuşmazlık | — | PLANLANDI | U-004 | Ship, Finance |
| Customer & Org | Şube, limit | — | PLANLANDI | Faz 10 | Identity |
| Notification | Outbox | — | PLANLANDI | | Events |
| Documents | Sertifika, POD | — | PLANLANDI | S3 | |
| Workflow | Onay zinciri | kısmi (ürün/teklif) | KISMİ | Genel motor | Order, Org |
| Audit | AuditOlay | var | KISMİ | API yüzeyi | Tümü |
| Reporting | Rapor | — | PLANLANDI | | Order+ |
| Integration Hub | Adapter | — | PLANLANDI | | API |
| Search | Katalog arama | — | PLANLANDI | | Catalog |

**İş kuralları (çekirdek):** kör havuz; quote fail-closed (TTL/kur/sözleşme); teklif seçimi `oncelik`↓ → iç maliyet↑ → `id`↑; stok üçlüsü (balance/reservation/movement) ayrı kavramlar — henüz kodda yok.

---

## 5. Kuyumculuk sektörü gereksinimleri

| Gereksinim | Durum |
|------------|-------|
| Altın/gümüş/metal + ayar/milyem | UYGULANDI |
| Gram / adet / sabit parça modelleri | UYGULANDI |
| İşçilik + kanal marj | UYGULANDI |
| Taş maliyeti (teklif vs katalog ayrımı K-011) | UYGULANDI |
| Sertifika kurum/no/dosya | PLANLANDI |
| Kur/metal zaman damgası + stale fail-closed | UYGULANDI |
| PriceQuote + PriceLock | UYGULANDI (sipariş bağ PLANLANDI) |
| Fiyat girdi izi (`hesap_girdisi`) | KISMİ (JSON var; UI yok) |
| Kör çoklu teklif pazaryeri | UYGULANDI |
| Seri/lot/batch, emanet/konsinye, depo transfer | PLANLANDI · U-008 |
| Üretim / özel sipariş / RFQ | PLANLANDI |
| Gram tolerans + QC | PLANLANDI · U-002 |
| Teslimat / uyuşmazlık | PLANLANDI |

---

## 6. Geçmişte alınan kararlar (ADR birleşik kayıt)

> Tüm ADR metinleri bu bölümde. Ayrı `docs/decisions/` **yok**. Agent ADR’yi kendi başına **Kabul** etmez.

| ID | Konu | Karar (özet) | Durum | Faz | Domain | Uygulama | Kanıt |
|----|------|--------------|-------|-----|--------|----------|-------|
| ADR-0001 | Agent standartları | Skill yolu, faz sırası, kanıt etiketleri | **Kabul** | 0 | — | UYGULANDI (AGENTS) | AGENTS.md |
| ADR-0002 | Runtime | Django 6.1 pin, PG, requirements disiplini | **Kabul** | 0 | Infra | UYGULANDI | requirements.txt |
| ADR-0003 | Kimlik/RBAC | 8 platform rolü, firma NOT NULL, dağıtık perm, izolasyon | **Kabul** | 1 | Identity | UYGULANDI | firmalar app |
| ADR-0003-add | view_all scope | Quality/logistics/support’tan view_all çıkarıldı | **Kabul** | 1 | Identity | UYGULANDI | yetki matrisi |
| ADR-0004 | Modüler paket | models/services/selectors/admin/tests | **Kabul** | 1+ | Tümü | UYGULANDI | paket ağacı |
| ADR-0005 | Katalog ownership | Platform; olusturan_firma; K1–K6 | **Kabul** | 2 | Catalog | UYGULANDI | urunler |
| ADR-0005-bekleyen | K1–K6 bekleyen | KAPANDI → 0005’e taşındı | **Kapandı** | 2 | Catalog | — | tarihsel |
| ADR-0006 | Faz 2.1 | B1–O6 (eşleştirme, onay kilidi, audit O3) | **Kabul** | 2.1 | Catalog/Teklif | UYGULANDI | testler |
| ADR-0007 | Faz 3a | Teklif SM, versiyon swap, K-007/K-008 | **Kabul** | 3.1–3.2 | Supplier/Pricing | UYGULANDI | 0005–0006 mig |
| ADR-0008 | Faz 3b | Üç model, kur, quote, B-02…B-06, PriceLock tanımı | **Kabul** | 3.3–3.7 | Pricing | 3.3–3.7 kod | 0007–0012 |
| ADR-0009 | Admin H1–H5 | Admin yüzey sertleştirme | **Kabul** | 3.1+ | Admin | UYGULANDI | admin tests |
| ADR-0010 | PriceLock L-01…L-11 | Tek lock/quote; TTL=quote; L-07 perm; sipariş FK yok | **Taslak** | 3.7 | PriceLock | L-01…L-10 kod+test; L-11 yok | 0010–0012 |
| B-01 | Servis payı | Kodlanmaz (hukuk) | **Açık** | 3+ | Pricing | Kod yok | ADR-0008 |
| B-02 | Alıcı görünürlük | Yalnız toplam (+ gram başı) | **Kabul** | 3.6 | Pricing | UYGULANDI | buyer_quote |
| B-03 | Quote TTL | Kanal bazlı; ≤ kur max gecikme | **Kabul** | 3.3–3.5 | Pricing | UYGULANDI | SatisKanali |
| B-04 | Kur sağlayıcı | Tek aktif; fallback yok | **Kabul** | 3.3 | Pricing | UYGULANDI | KurSaglayici |
| B-05 | Kur tipi | Alıcı/tedarikçi ayrı | **Kabul** | 3.3 | Pricing | UYGULANDI | KurPolitikasi |
| B-06 | Vergi | Faz 3 proforma; KDV yok | **Ertelendi** | 3 | Pricing | Bilinçli yok | ADR-0008 §2.9 |

### 6.1 ADR-0010 — madde durumu (ADR hâlâ **Taslak**)

Ürün sahibi resmi **Kabul** vermeden Faz 4 kodu başlamaz. Aşağısı kod gerçeğidir; ADR Kabul’ü değildir.

| Madde | Kod | Özet |
|-------|-----|------|
| L-01 | UYGULANDI | Quote başına tek lock (`OneToOne`); expired → yeni quote; tarihsel koruma |
| L-02 | UYGULANDI | Yeniden fiyat hesabı yok |
| L-03 | UYGULANDI | Yalnız geçerli quote kilitlenir |
| L-04 | UYGULANDI | `gecerlilik_sonu` = quote; `clean()` + INSERT trigger (`0011`); TTL uzatılamaz |
| L-05 | UYGULANDI | AKTIF → SURESI_DOLDU |
| L-06 | UYGULANDI | Idempotent create |
| L-07 | UYGULANDI | `lock_quote` = `ALICI_SATINALMACI`; `lock_quote_on_behalf` = Super+Admin + gerekçe ≥10 (trim); Finance/Ops/Catalog/Support/Quality/Logistics/tedarikçi create yok; `view_all_tenants` create vermez |
| L-08 | UYGULANDI | App + DB immutability (expire istisnası) |
| L-09 | UYGULANDI | `select_for_update` |
| L-10 | UYGULANDI | Success/fail audit; on-behalf `gerekce` + gerçek aktör |
| L-11 | PLANLANDI | Sipariş FK yok — Faz 4 + ADR Kabul sonrası |

**Açık ürün notu (matris):** `PLATFORM_FINANCE` on-behalf opt-in şimdilik **yok**. `ALICI_YONETICI` / `ALICI_ONAYLAYICI` `lock_quote` almaz.

### 6.2 Çelişki / kapanmış drift

| Konu | Not |
|------|-----|
| ADR-0010 | Kod L-01…L-10 hazır; ADR **Taslak** → resmi Kabul bekler |
| Eski handoff / faz raporları / `docs/decisions|architecture|analysis` | Kaldırıldı; kanonik yalnız bu master |
| Prosperer parity | Hedef kıyas; runtime DOĞRULANAMADI |

---


### 6.3 ADR tam metin arşivi (Git HEAD birleştirme öncesi)

Aşağıdaki metinler tarihsel ADR arşividir (eski ayrı dosya adları yalnızca etiket). **Canlı durum:** üstteki §6 tablo + §6.1. Yeni kararlar yalnız §6 tablosuna ADR ID ile eklenir.

#### Kaynak: `docs/decisions/ADR-0001-agent-standartlari.md`

# ADR-0001 — Agent standartları ve faz sırası

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlam:** Faz 0

## Karar

1. Proje bağlayıcı agent talimatı kök `AGENTS.md` dosyasıdır.
2. Cursor platformu kullanıldığı için skill yolu `.cursor/skills/<ad>/SKILL.md` olur (`.agent/skills` değil).
3. İnce her zaman-uygula kuralı: `.cursor/rules/kuyumbank-core.mdc`.
4. Geliştirme faz sırası kullanıcının verdiği 0–8 sırasıdır; rapor §14 ile uyumlu öz: önce kimlik/tenant, sonra katalog/teklif/fiyat, sonra stok/sipariş, finans, operasyon, API, prod.
5. İş kuralı kaynağı: `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md` (K-* ve §9).
6. Django resmi docs/kaynak kodu framework referansıdır; proje skill’i değildir. Skill’ler Kuyumbank kurallarını taşır.
7. Denetimde Ek kural A (kanıt etiketleri) ve Faz 0’da Ek kural B (değişiklik sınırı) bağlayıcıdır.

## Sonuçlar

- Agent görev başında tüm dokümanı yeniden okumaz; ilgili skill + ADR yeterlidir.
- Faz atlanmaz; özellikle Faz 1 tamamlanmadan sipariş/finans yazılmaz.
- Kanıtsız bulgu ve çalıştırılmamış “yeşil test” iddiası geçersizdir.

---

#### Kaynak: `docs/decisions/ADR-0002-runtime-ve-bagimliliklar.md`

# ADR-0002 — Runtime ve bağımlılıklar

**Durum:** Kabul edildi (Faz 0 denetim turu ile güncellendi)  
**Tarih:** 2026-11-08

## Karar

1. **Django 6.1.x** pin: `Django==6.1.2`. Matris: Python 3.12–3.14 ([FAQ](https://docs.djangoproject.com/en/6.1/faq/install/)).
2. PostgreSQL zorunlu; test varsayılanı proje DB’sidir.
3. `requirements.txt` **yalnızca doğrudan bağımlılık** içerir (import / INSTALLED_APPS kanıtlı).
4. Ortamda yüklü DRF, Celery, redis **projeye eklenmez** — kod kullanmıyor (DOĞRULANDI: `INSTALLED_APPS`, `urls.py`).
5. `django-environ` zorunlu: `settings.py` L10 `import environ` (HEAD requirements’ta eksikti).
6. DB sürücü: geliştirme ortamında `psycopg==3.3.6` var; HEAD’deki `psycopg2==2.9.13` ile uyumsuzluk vardı → pin `psycopg[binary]==3.3.6` (`ENGINE=django.db.backends.postgresql`).
7. `django-import-export` pin ortamla hizalı: `4.4.3` (HEAD 4.4.4 idi; ortam 4.4.3).

## Bilinçli dışarıda bırakılanlar

- Transitive pin yağmuru (asgiref/sqlparse/tablib…) — pip çözer; gereksiz drift yaratmayız.
- colorama — proje import etmiyor.

## Kanıt

| Paket | Neden | Sınıf |
|-------|-------|--------|
| Django | framework | DOĞRULANDI |
| django-environ | settings import | DOĞRULANDI |
| django-import-export | INSTALLED_APPS | DOĞRULANDI |
| psycopg | DATABASES ENGINE + pip freeze | DOĞRULANDI |
| djangorestframework | freeze’te var, projede yok | DOĞRULANDI — requirements’a **konmaz** |

---

#### Kaynak: `docs/decisions/ADR-0003-addendum-view-all-scope.md`

# ADR-0003 Addendum — `view_all_tenants` daraltması

**Durum:** Kabul edildi (uygulama sonrası bilinçli sapma kaydı)  
**Tarih:** 2026-11-08  
**Üst ADR:** [ADR-0003](ADR-0003-faz1-kimlik-rbac.md)

## Karar

`firmalar.view_all_tenants` permission’ı **yalnızca** şu rollere seed edilir:

- `platform_super`
- `platform_admin`
- `platform_ops`
- `platform_finance`
- `platform_catalog`

**Verilmez:** `platform_quality`, `platform_logistics`, `platform_support`

## Gerekçe

`faz1-teknik-inceleme.md` §2.3’te bu üç rol için tenant-genel liste **S (sınırlı)** idi. İlk seed hepsine `view_all` vermişti; doğrulama turunda ADR-0003-05 senaryosu 7 (superuser sessiz aşım) ile çakışmayı önlemek ve “S = tam view_all değil” ilkesini korumak için daraltıldı.

Kod: `firmalar/role_permissions.py` (PLATFORM_QUALITY/LOGISTICS/SUPPORT → boş perm tuple).

## Sonuç

Bu roller platform firmasına bağlı olsa bile çapraz tenant listeleme yapamaz; QC/lojistik/destek için ileride dar scope permission’ları ayrı ADR ile eklenebilir.

---

#### Kaynak: `docs/decisions/ADR-0003-faz1-kimlik-rbac.md`

# ADR-0003 — Faz 1 kimlik, RBAC ve tenant kararları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onaylayan:** Proje sahibi (dört karar + ek güvenlik kriteri)  
**Bağlı tasarım:** tarihsel metin bu master arşivinde (ayrı architecture dosyası yok).  
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

---

#### Kaynak: `docs/decisions/ADR-0004-modular-python-organizasyon.md`

# ADR-0004 — Modüler Python Dosya Organizasyonu

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onaylayan:** Proje sahibi  
**Bağlam:** Faz 0 tamam; Faz 1 uygulama standardı. Ayrı talimat olmadan mevcut WIP topluca yeniden düzenlenmez.

## Karar

Kuyumbank projesinde modeller, view'lar, serializer'lar, admin sınıfları, servisler, selector'lar ve testler sorumluluklarına göre ayrı Python dosyalarında tutulacaktır.

### 1. Model organizasyonu

- Her ana model ayrı bir Python dosyasında tanımlanır.
- Modeller `models/` paketi altında tutulur.
- `models/__init__.py` dışa aktarımları yönetir.
- Birbiriyle doğrudan ilişkili küçük yardımcı sınıflar, gerekçesi belgelenerek aynı dosyada bulunabilir.

### 2. View organizasyonu

- View sınıfları ve fonksiyonları sorumluluklarına göre ayrı dosyalara ayrılır.
- HTTP işlemleri dışında iş mantığı view içine yerleştirilmez.
- URL yapılandırması merkezi `urls.py` üzerinden ilgili view dosyalarına bağlanır.

### 3. Diğer katmanlar

- `services/`: İş kuralları ve yazma işlemleri.
- `selectors/`: Okuma ve veri sorgulama işlemleri.
- `serializers/`: API veri doğrulama ve dönüşüm.
- `admin/`: Django Admin yapılandırmaları.
- `tests/`: Testler, konu ve sorumluluğa göre ayrı dosyalar.

### 4. Bağlayıcı kurallar

- Yeni kod mevcut dosyalara yalnızca dosyanın sorumluluğuyla uyumluysa eklenebilir.
- Büyük ve birden fazla sorumluluk taşıyan dosyalar uygun paketlere ayrılır.
- Gereksiz küçük dosyalar oluşturulmaz.
- Circular import oluşturulmaz.
- Django model keşfi, migration sistemi, admin keşfi ve test keşfi korunur.
- Dosya taşıma ve yeniden düzenleme işlemlerinde import yolları ve geriye dönük uyumluluk kontrol edilir.
- Agent, yalnızca biçimsel gerekçeyle mevcut kodu topluca yeniden düzenlemez.

### 5. AI agent yükümlülüğü

Yeni modül ve kod geliştirmelerinde bu organizasyon standardı zorunludur. Her fazda değiştirilen dosyalar ve sorumlulukları raporlanır.

## Hedef paket iskeleti (örnek: `urunler`)

```text
urunler/
├── models/
│   ├── __init__.py
│   ├── kategori.py
│   ├── urun.py
│   ├── urun_varyant.py
│   ├── urun_medya.py
│   └── tedarikci_urun.py
│
├── views/
│   ├── __init__.py
│   ├── kategori_views.py
│   ├── urun_views.py
│   └── varyant_views.py
│
├── services/
│   ├── __init__.py
│   ├── urun_service.py
│   └── varyant_service.py
│
├── selectors/
│   ├── __init__.py
│   └── urun_selectors.py
│
├── admin/
│   ├── __init__.py
│   ├── urun_admin.py
│   └── kategori_admin.py
│
├── serializers/
│   ├── __init__.py
│   └── urun_serializer.py
│
├── tests/
│   ├── __init__.py
│   ├── test_urun.py
│   ├── test_varyant.py
│   └── test_tenant_isolation.py
│
├── urls.py
└── apps.py
```

Aynı desen `firmalar`, `tanimlar`, `fiyatlama` ve sonraki app’ler için geçerlidir. App’te henüz API yoksa `views/`, `serializers/`, `urls.py` oluşturulmaz (gereksiz dosya yasağı).

## Mevcut kod / WIP

- Birçok app zaten `models/`, `admin/`, `services/` paketlerine yakın.
- **Onaysız toplu refactor yok.** Faz 1’de yalnızca dokunulan yüzey ADR-0004’e uyar; geniş taşıma ayrı talimat ister.
- Taşıma yapılırsa: import yolları, `AppConfig`, admin register, migration tarihçesi ve test keşfi doğrulanır.

## Sonuçlar

- İş mantığı `services/`; okuma sorguları `selectors/`; HTTP ince kalır.
- Tenant scope okumaları tercihen selector’da; yazma kuralları service’te (ADR-0003 ile uyum).
- Faz raporu: değişen dosya + sorumluluk listesi zorunlu.

## İlişkili

- [`AGENTS.md`](../../AGENTS.md)
- [`.cursor/skills/django-engineering/SKILL.md`](../../.cursor/skills/django-engineering/SKILL.md)
- [`ADR-0003`](ADR-0003-faz1-kimlik-rbac.md) (kimlik/RBAC; bu ADR yapısal iskelet)

---

#### Kaynak: `docs/decisions/ADR-0005-bekleyen-kararlar.md`

# ADR-0005 — Bekleyen kararlar

**Durum:** KAPANDI (2026-11-08) — K1–K6 ürün sahibi tarafından kabul edildi; bağlayıcı metin: [`ADR-0005-katalog-platform-ownership.md`](ADR-0005-katalog-platform-ownership.md).

Açık kalanlar (ADR §9–§10): tekilleştirme skor eşiği, onaylı katalogda tedarikçi varyant görünürlüğü, `EslestirmeOlay` vs yalnız AuditOlay; hukuki tolerans ve B2C metni için **DIŞ DOĞRULAMA**; K-014 object storage.

---

#### Kaynak: `docs/decisions/ADR-0005-katalog-platform-ownership.md`

# ADR-0005 — Katalog platform ownership

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onay:** Ürün sahibi — 2026-11-08 (K1–K6 bağlayıcı)  
**Bağlı:** K-006, K-010, K-011, K-014 (kapsam dışı), K-015, K-016; `faz2-etki-analizi.md`; Faz 1.1 audit kalıbı  
**Önkoşul:** Faz 1.1 GO

---

## 1. Bağlam

Mevcut modelde `Urun.tedarikci` katalog ürününü tek tedarikçiye bağlar. Kör havuz ve çoklu tedarikçi teklifi (rapor §5.2 / K-006) bunu reddeder. Faz 1 K-004 sahipliği `urun.tedarikci_id` üzerinden doğrulanıyordu; bu ADR ile sahiplik yeniden tanımlanır.

---

## 2. Karar ve gerekçe (K1–K6)

| No | Karar | Gerekçe |
|----|-------|---------|
| **K1** | Kimlik sınıfları: **A**=seri/sertifikalı (sertifika no veya parça no), **B**=markalı/model kodlu (marka+model, varsa GTIN), **C**=jenerik kalıp. İlk sürümde A ve B otomatik kesin eşleşme; C elle onaylı. | Farklı tekilleştirme güveni; yanlış birleştirmeyi sınırlar. |
| **K2** | C sınıfında “aynı ürün” = platform standart modeli (spec). Kimlik: kategori/tip, metal, ayar, kalıp ailesi, ölçü sınıfı, içi dolu/boş, taş var/yok, yüzey/renk. Kimlik **değil:** tedarikçi, üretici markası, tedarikçi SKU. **Ayar sert kimlik** (14K ≠ 18K). | Kör havuz + kalıp ailesi birleşimi; ayar karışması engeli. |
| **K3** | Gramaj kimlik değil; **varyant boyutu** (gram bandı parametreli). Teklifler toplam fiyatla değil **gram-başı işçilik + milyem** ile normalize edilip karşılaştırılır. | Aynı kalıbın farklı gramları ayrı varyant; adil teklif kıyası. |
| **K4** | Görsel eşdeğerlik: B2B’de fotoğraf **temsili**, ürün “belirtilen özelliklerde”; B2C’de sipariş anında **tek teklife kilitleme** + QC’de kalıp uyumu. Kalite toleransları (gram, ölçü, kalıp) **konfigürasyon parametresi**. Hukuki tolerans doğrulaması → **DIŞ DOĞRULAMA GEREKİR**. | Operasyonel esneklik; hukuki metin ajan tarafından uydurulmaz. |
| **K5** | Eşleştirme: tedarikçi teklif/nitelik **önerir**; karar yalnız `platform_catalog` (+ `approve_urun` / eşleştirme permission). **Şüphede ayır.** Her eşleştirme/ayırma/birleştirme **audit’li ve geri alınabilir**. | Platform kontrolü; yanlış birleştirme geri alınabilir. |
| **K6** | Katalog ürünü **platforma** aittir. `Urun.tedarikci` **kaldırılır**; yerine denetim amaçlı `olusturan_firma` (alıcıya hiçbir yüzeyde gösterilmez). Tedarikçi, onaydan önce yalnız kendi önerdiği **taslağı** düzenler (K-004 yeni tanım); onaydan sonra ürün işlemi yok, yalnız `TedarikciTeklif` / SupplierOffer. | K-006; kör havuz; çoklu teklif. |

### Kabul edilmeyen alternatifler (kısa)

| Alternatif | Neden reddedildi |
|------------|------------------|
| Katalogda `Urun.tedarikci` kalsın (yeniden adlandırılmış “ana kaynak”) | Kör havuz sızıntı riski; çoklu teklif modeli bulanık kalır (K6). |
| Tedarikçi doğrudan onaylı `Urun` yazar | Platform sahipliği ve eşleştirme denetimi zayıf (K5/K6). |
| C sınıfında otomatik birleştirme (ilk sürüm) | Yanlış birleştirme maliyeti yüksek; elle onay zorunlu (K1). |
| Gramajı ürün kimliğine dahil etmek | Aynı kalıp farklı gram = ayrı varyant olmalı (K3). |
| B2C’de “temsili fotoğrafla rastgele teklif” | Sipariş anında tek teklif kilidi + QC şart (K4). |

---

## 3. Veri modeli taslağı (alan düzeyi, kodsuz)

### 3.1 `Urun`

| Alan | Not |
|------|-----|
| `tedarikci` | **Kaldırılır** (migration + veri taşıma). |
| `tedarikci_urun_kodu` | Teklife / öneriye taşınır; üründen kaldırılır veya boş bırakılıp kullanılmaz. |
| `olusturan_firma` | FK `Firma`, PROTECT; denetim; alıcı API/admin listelerinde yok. |
| `kimlik_sinifi` | `A` / `B` / `C` |
| `kimlik_anahtari` | Normalize string; sınıf A/B’de unique (aktif kayıtlar); C’de platform spec anahtarı. |
| Mevcut | `platform_kodu`, onay/yayın, kategori, ayar, SEO, vitrin alanları kalır. |

**Çakışma:** `onay_servisi` K-004 `urun.tedarikci_id` → `olusturan_firma_id` + durum=taslak/reddedildi.  
**Etki analizi:** `faz2-etki-analizi.md` B1 satırları `urun.py`, `onay_servisi`, admin, testler.

### 3.2 `Varyant`

| Alan | Not |
|------|-----|
| `gram` | Mevcut; kimlik değil. |
| `gram_bandi_min` / `gram_bandi_max` | Parametreli bant (opsiyonel ilk dilimde settings sabiti + alan). Teklif gramı bant dışıysa **ayrı varyanta** düşer (K3). |
| `tedarikci_sku` | Teklife taşınır; varyantta kaldırılır veya kullanılmaz. |
| `stok` | Otomatik `TedarikciTeklif.stok_adet` ile **toplanmaz** (§13.2). |

### 3.3 `TedarikciTeklif` (SupplierOffer)

| Alan | Not |
|------|-----|
| Mevcut | `varyant`, `tedarikci`, fiyat/stok/termin/durum kalır. |
| `eslestirme_durumu` | `onerildi` / `onaylandi` / `reddedildi` / `ayrildi` |
| `eslestirme_guveni` | `kesin` / `manuel` / `cikarim` |
| `eslestiren_kullanici` | FK user (platform) |
| `eslestirme_kaniti` | JSON (sertifika no, model kodu, spec hash, not) |
| `esdegerlik_seviyesi` | `birebir` / `esdeger` |

K-006: teklif `tedarikci_id == kullanici.firma_id`; başka firmanın varyantına yazma IDOR engeli serviste.

### 3.4 Eşleştirme geçmişi / audit

- Her `eslestir` / `onayla` / `reddet` / `birlestir` / `ayir` → `AuditOlay` (Faz 1.1 kalıbı).
- İsteğe bağlı `EslestirmeOlay` tablosu (entity snapshot + reverse pointer); ilk sürümde `AuditOlay.detail` yeterli olabilir — servis sözleşmesi geri alınabilirliği garanti eder.

---

## 4. Servis sözleşmeleri (imza + kurallar, kodsuz)

Ortak kurallar: `transaction.atomic` ürün/teklif yazımıyla; **fail audit atomic dışı** (Faz 1.1); permission her çağrıda; idempotency: aynı girdi + aynı hedef durumda no-op + tek success audit.

```
teklif_eslestir_oner(teklif, kullanici, hedef_urun|None, kanit) -> teklif
  - require: manage_own_teklif + teklif.tedarikci_id == kullanici.firma_id
  - A/B: otomatik aday + guven=kesin öneri; C: guven=manuel, durum=onerildi
  - ayar/kimlik çelişkisi → ValidationError + fail audit
  - şüphe → ayır / önerme

eslestirmeyi_onayla(teklif, kullanici) -> teklif
  - require: platform firma + approve_urun (veya eşleştirme perm)
  - durum onerildi → onaylandi; audit success

eslestirmeyi_reddet(teklif, kullanici, neden) -> teklif
  - platform + neden zorunlu; audit

urunleri_birlestir(kaynak_urun, hedef_urun, kullanici) -> hedef
  - yalnız platform_catalog; aynı kimlik_sinifi + uyumlu anahtar
  - 14K/18K birleşmez; audit + geri alınabilir işaret

urunu_ayir(urun_veya_teklif, kullanici, neden) -> yeni_urun|teklif
  - platform; şüphe veya yanlış birleştirme geri alma; audit
```

---

## 5. K-004 yeni karşılığı ve tenant scope

### K-004 (Faz 2)

1. **Taslak / reddedildi:** `onaya_gonder` yalnız `urun.olusturan_firma_id == kullanici.firma_id` + `submit_urun`.
2. **Onaylı ürün:** tedarikçi ürün alanını değiştirmez / onaya göndermez; yalnız kendi `TedarikciTeklif` kayıtları.
3. Platform `approve_urun` / `publish_urun` katalogda; eşleştirme onayı platform_catalog.

### `katalog_tenant` (tek nokta)

| Önce (Faz 1.1) | Sonra (Faz 2) |
|----------------|---------------|
| `scope_urun_queryset` → `tedarikci_id=firma` | Platform `view_all_tenants`: tüm katalog. Tedarikçi: **onay öncesi** `olusturan_firma_id=firma` taslaklar; onaylı katalog **okuma** politikası ayrı (teklif ekleme için varyant listesi platform yayınına bağlı — detay uygulama PR’ında). |
| İlişkili `urun__tedarikci_id` | `urun__olusturan_firma_id` (taslak scope) |
| Teklif scope | Yeni/existing `scope_teklif_queryset`: `tedarikci_id=firma` (zorunlu) |

Alıcı yüzeylerinde `olusturan_firma` / tedarikçi kimliği **yok** (`user_may_see_tedarikci_identity` false).

---

## 6. Veri taşıma planı

1. **Kapı sorguları (migrate öncesi):**  
   - `Urun` sayısı, `tedarikci` null/dolu, varyant/teklif sayıları  
   - `Varyant.stok` vs eşleşen `TedarikciTeklif.stok_adet` farkları (otomatik toplanmaz)  
   - `kimlik_anahtari` çakışma adayları  
2. Her `Urun` için: `olusturan_firma = eski tedarikci`; taslak `TedarikciTeklif` (veya eşdeğer) oluşturulur — stok kopyalanmaz otomatik.  
3. `tedarikci` / `tedarikci_urun_kodu` kaldırılır (çok adımlı migration: ekle → doldur → NOT NULL → kaldır).  
4. **Geri dönüş:** migration reverse + yedek; production migrate ayrı onay.  
5. Yerel envanter (2026-11-08): Urun=0 → taşıma riski düşük (**DOĞRULANDI** etki analizinde). Staging/üretim: **DOĞRULANAMADI**.

---

## 7. Faz 2 kapsamı ve iş kartı sırası

| Sıra | Kart | Kapsam |
|------|------|--------|
| 1 | **K-015** | SEO sabit marka → settings/parametre; `save()` içinde “Örnek Kuyumculuk” kalkar; güvenli teknik fallback |
| 2 | **K-016** | Kategori alt ağaç derinliği + `kategori_tasi` servisi; `yeni_üst_derinlik + alt_ağaç_yüksekliği <= 3` |
| 3 | **K-006 / ownership** | Bu ADR model + K-004 + selector + teklif eşleştirme iskeleti |
| — | **K-014 medya** | Object storage kararı yok → **kapsam DIŞI** |

Non-goals: stok üçlüsü (Faz 4), PriceQuote (Faz 3), DRF (Faz 7), onaysız WIP refactor.

---

## 8. Kabul testleri (§12.2 / §12.3 eşlemesi)

| Test | Rapor |
|------|-------|
| Tenant/IDOR: tedarikçi başka firmanın taslağını güncelleyemez | §12.2.2, güvenlik |
| Tedarikçi yalnız kendi taslağını onaya gönderir (yeni K-004) | §12.2.2 |
| Yanlış birleştirmeyi geri alma (`urunu_ayir`) | K5 |
| Aynı sınıf-A sertifika no ile çift kayıt engeli | K1 |
| Ayar farklı ürünler eşleşemez (14K≠18K) | K2 |
| Gram bandı dışı teklif ayrı varyanta düşer | K3 |
| Teklif yalnız kendi tedarikçisi | §12.3.1–2 |
| Alıcı yüzeyinde tedarikçi/`olusturan_firma` yok | §12.3.14 |
| Kategori derinlik + taşıma | §12.2.9 |
| SEO’da sabit örnek marka yok | K-015 |

---

## 9. ÜRÜN SAHİBİ KARARI GEREKİR (açık kalanlar)

| Madde | Not |
|-------|-----|
| Tekilleştirme **güven eşiği** (çıkarım skoru → otomatik mi?) | İlk sürüm: A/B kesin, C elle; skor eşiği sonraya |
| Onaylı katalogda tedarikçinin **varyant görünürlük** kapsamı (tüm aktif mi, yalnız teklif verdiği mi?) | Uygulama PR’ında netleştirilir; şüphede daralt |
| `EslestirmeOlay` ayrı tablo mu, yalnız `AuditOlay` mı? | İlk sürüm AuditOlay yeterli varsayılanı |

---

## 10. DIŞ DOĞRULAMA GEREKİR

| Madde | Not |
|-------|-----|
| Hukuki **tolerans** metni (gram/ölçü/kalıp sapması) | Avukat / regülasyon |
| B2C **eşdeğerlik / temsili görsel** tüketici metni | Hukuk + ürün |
| Object storage / CDN seçimi (K-014) | Altyapı; medya bu ADR kapsamı dışı |

---

## 11. Onay checklist

- [x] K1–K6 bağlayıcı kabul  
- [x] `Urun.tedarikci` kaldır + `olusturan_firma`  
- [x] K-004 yeni sahiplik yazıldı  
- [x] Medya (K-014) kapsam dışı  
- [x] Durum: **Kabul edildi**

---

#### Kaynak: `docs/decisions/ADR-0006-faz2-1-kararlar.md`

# ADR-0006 — Faz 2.1 düzeltme kararları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlı:** ADR-0005 (Kabul); `faz2-1-dogrulama-raporu.md`  
**Onay:** Ürün sahibi — 2026-11-08

---

## 1. Bağlam

Faz 2.1 ADIM 1 doğrulaması B1–B4 / O1–O6 açıklarını listeledi. Bu ADR, ADIM 2 uygulama sınırlarını bağlar.

---

## 2. Kararlar

| Kod | Karar |
|-----|--------|
| **B1** | Tedarikçi teklif admin: `durum`, `onaylayan`, `onay_zamani`, `eslestirme_*`, `hedef_urun`, `esdegerlik_seviyesi` salt okunur. `tedarikci` sunucuda `request.user.firma` atanır. Varyant FK tek selector ile kapsamlı. Durum geçişleri yalnız servis. |
| **B2** | `assign_user_role(actor=..., user=..., firma=..., rol=...)`; `require_perm` + tenant; audit actor=değiştiren; hedef kullanıcı detail’de. Firma değişikliği yalnız platform (`manage_all_users` / view-all). KullaniciAdmin Firma/rol seçenekleri tenant kapsamlı. |
| **B3** | `teklif_eslestir_oner`: hedef görünür/uygun değilse genel hata (kimlik ipucu yok). Güven hesabı tedarikçi kanıtından oracle üretmez (`tedarikci_kodu` ↔ ürün kimliği). ONAYLANDI/AYRILDI iken öneri reddedilir (lock sonrası). `eslestirme_kaniti` izinli anahtar + string + uzunluk. Fail audit atomic dışı. |
| **B4a** | Gram bandı hesabı (`VARYANT_GRAM_BANDI_ORAN` / override alanları); bant dışı öneri nedenli red + audit; `eslestirmeyi_onayla` hedef ayar/bant yeniden doğrular. |
| **B4b** | `urunleri_birlestir` **ertelendi** (bu fazda eklenmez). Kapsam/varyant taşıma sonraki ADR. |
| **O1** | `onay_bekliyor`: tedarikçi Urun/Varyant/inline salt okunur. `geri_cek` → taslak (sahiplik+perm+audit). Onaylıda kritik alan değişimi engellenir; `taslaga_al` + yeniden onay. |
| **O2** | Unique `urun_kimlik_ab_anahtar_uniq` → A/B + dolu anahtar + `onay_durumu != 'reddedildi'`. Migration `0007`. `onaya_gonder` aktif çakışmayı serviste genel hata + fail audit ile önler; `IntegrityError` yarışı genel hataya maplenir. |
| **O3** | Fail audit kalıcılığı — aşağıda. |
| **O4** | Toplu Reddet: `_selected_action` çoklu ID listesi doğru parse edilir. |
| **O5** | `onayla` / `yayina_al`: aktör ≠ son başarılı `urun.onaya_gonder` aktörü (yoksa `olusturan_kullanici`); ihlalde fail audit. |
| **O6** | `approve_teklif` / `manage_sozlesme` servis bağlama **Faz 3’e ertelendi**. |

### O1 kritik alanlar (onaylı kilit)

`kimlik_sinifi`, `kimlik_anahtari`, `ayar_id`, `kategori_id`, `fiyat_tipi`, `ad` — değişim engeli; düzenleme için `taslaga_al`.

### O2 migration

| Madde | İçerik |
|-------|--------|
| Dosya | `urunler/migrations/0007_o2_kimlik_uniq_reddedildi_haric.py` |
| Hedef | Partial unique: `kimlik_sinifi ∈ {A,B}` ∧ `kimlik_anahtari != ''` ∧ `onay_durumu != 'reddedildi'` |
| İleri | Kısıt gevşer; mevcut veriyi bozmaz / satır silmez |
| Reverse | Eski kısıta dönüş öncesi çakışma kontrolü; varsa `RuntimeError` (genel mesaj, satır silinmez) |

### O3 — `record_audit_durable` (üretim davranışı)

**Üretim (autocommit veya dış `transaction.atomic`):**

1. `domain_atomic()` **içinde** çağrı → `RuntimeError` (fail audit domain rollback ile silinmesin diye yasak).
2. Herhangi bir `transaction.atomic` bloğu içindeyse → audit satırı **ayrı DB bağlantısı (sidecar)** ile yazılır ve o bağlantıda `commit` edilir. Dış atomic sonra rollback olsa bile fail audit **kalır**.
3. Atomic dışında (autocommit) → normal `record_audit` yazımı; hemen kalıcıdır.

**Test sapması (yalnız TestCase):** Sidecar, henüz commit edilmemiş `actor_id` görürse FK `IntegrityError` alabilir. Bu durumda aynı test bağlantısına fallback yapılır (assert görünür; test sonunda rollback olur). Production’da kullanıcı zaten commit’lidir → sidecar yolu kullanılır. Kalıcılık `TransactionTestCase` ile kanıtlanır.

### Gram bandı (B4a)

- `gram_bandi_min/max` doluysa onlar; değilse `varyant.gram * (1 ± VARYANT_GRAM_BANDI_ORAN)`.
- Teklif `gram` band dışındaysa öneri/onay reddedilir (nedenli mesaj + audit).

### Bilinçli sınır — teklif `durum` (Faz 3)

Admin’de `TedarikciTeklif.durum` (ve onay/eşleştirme alanları) **salt okunur**; formdan durum geçişi yok. Durum makinesi / `approve_teklif` servisleri **Faz 3’e ertelendi**. Bu bilinçli sınırdır; admin üzerinden teklif yayınlama yapılmaz.

---

## 3. Non-goals

- Faz 3 fiyat motoru / `approve_teklif` / teklif durum servisi
- `urunleri_birlestir` implementasyonu
- Üretim migrate (ayrı onay)

---

## 4. Onay checklist

- [x] B1–B5 / O1–O5 uygulama kabul  
- [x] B4b birleştir ertelendi kabul  
- [x] O2 migration planı + dosya  
- [x] O3 sidecar durable kabul  
- [x] O6 Faz 3 erteleme kabul  
- [x] Durum: **Kabul edildi**

---

#### Kaynak: `docs/decisions/ADR-0007-faz3-fiyatlama.md`

# ADR-0007 — Faz 3a: Tedarikçi teklifi yaşam döngüsü ve sözleşme kuralları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08 (revizyon: Faz 3a/3b bölünmesi)  
**Bağlı:** ADR-0005, ADR-0006 (Kabul); kanonik rapor K-006…K-008; §9.3 (teklif); §12.3 (teklif/sözleşme maddeleri)  
**Etki analizi:** tarihsel özet bu master arşivinde.  
**Onay:** Ürün sahibi, 2026-11-08

**Kapsam notu:** Faz 3b kararları [`ADR-0008-faz3b-kur-fiyatlama-quote.md`](ADR-0008-faz3b-kur-fiyatlama-quote.md) içindedir; **3.3+ kodu ADR-0008 Kabul olmadan başlamaz.**  
**Uygulama:** Dilim **3.1** uygulandı — [`faz3-1-uygulama-raporu.md`](../architecture/faz3-1-uygulama-raporu.md). Dilim **3.2** (K-007/K-008) uygulandı — [`faz3-2-uygulama-raporu.md`](../architecture/faz3-2-uygulama-raporu.md).

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/) (`UniqueConstraint.nulls_distinct`).

---

## 1. Bağlam

Faz 2 katalog ownership’i ayırdı. *(Analiz/Kabul anı:)* teklif durum servisi yoktu; K-007/K-008 (NULL-safe unique/exclusion) eksik. ADR-0006: teklif `durum` admin salt okunur; `approve_teklif` / `manage_sozlesme` Faz 3’e ertelenmişti. Bu ADR yalnız **dilim 3.0–3.2** (teklif yaşam döngüsü + sözleşme kuralları) içindir.

---

## 2. Kararlar (bağlayıcı)

### 2.1 Tedarikçi teklifi yaşam döngüsü

| Madde | Karar |
|-------|--------|
| Sahiplik | Teklif `tedarikci_id == kullanici.firma_id`; firma `tedarikci_mi=True`. Client `tedarikci_id` güvenilmez. |
| Katalog bağ | Platform `Varyant` (ADR-0005). Eski “ürün.tedarikci == teklif.tedarikci” **geçersiz**. |
| Eşleştirme kapısı | **Zorunlu:** `eslestirme_durumu == onaylandi` ve `hedef_urun` tutarlı. `eslestirme_durumu` boş (`''`) veya dolu ama `onaylandi` değil → **“eşleştirme bekliyor”** → fiyat motorunda / quote’ta **kullanılmaz** (genel hata). C sınıfı / elle istisna **yok**. (Quote üretimi ADR-0008.) |
| Faz 2 taslak teklifler | Migration ile gelen tekliflerde `eslestirme_durumu=''`: eşleşme kapısından geçmez. Operasyon: `teklif_eslestir_oner` → platform `eslestirmeyi_onayla`. Backfill otomatik `onaylandi` **yapılmaz**. |
| Durum makinesi | `TASLAK → ONAY_BEKLIYOR → YAYINDA ↔ PASIF`; yalnız servis + perm + audit. |
| `approve_teklif` | Platform + permission; dört göz (ADR-0006 O5). |
| Versiyon geçişi | Yayınlı teklifte fiyat/gram/model değişimi → **yeni satır/versiyon** `ONAY_BEKLIYOR` (veya taslak); onaylanana kadar **eski YAYINDA kalır**. Yenisi onaylanınca **tek `domain_atomic`**: önce eski → PASIF, sonra yeni → YAYINDA (`select_for_update`). Fiyatsız boşluk yok. İleriye dönük: quote/sipariş eski `teklif_id`/`versiyon` taşır — ADR-0008. |
| Geçerlilik | `gecerlilik_baslangic` / `gecerlilik_bitis` YAYINDA için zorunlu; süresi dolmuş → fiyat motorunda kullanılmaz (quote yok — ADR-0008). |
| Aktif çakışma | Aynı `tedarikci + varyant + tedarikci_kodu` (boş kodda `tedarikci+varyant`) için **bir** YAYINDA; partial unique + servis. Çoklu YAYINDA (farklı kod) seçim sırası → ADR-0008 §5. |
| FK | `varyant` CASCADE → **PROTECT**; aktif teklif varken varyant silinemez. |
| Admin | Durum readonly; action → servis. |

#### Netleştirme (anlam değişmez)

1. **Versiyon swap sırası:** Önce eski teklif → PASIF, sonra yeni teklif → YAYINDA; tek `domain_atomic` içinde; ilgili satırlar `select_for_update` ile kilitlenir. Gerekçe: “aktif çakışma” partial unique’i ertelenmemiş kısıttır; sıra ters olursa ara ifade kısıtı ihlal eder.
2. **Eşleştirme kapısı (3a):** Yalnız saf bir uygunluk koşulu (selector / predicate); quote çağrısı yok. Quote tarafındaki gerçek reddi testi ADR-0008’e aittir; §7’deki ilgili test 3a’da **predicate** testidir.
3. **Versiyon alanları:** `versiyon` ve önceki teklife bağ ADR’de adlandırılmamıştır; uygulama sırasında geri dönüşü kolay en küçük çözüm seçilir ve uygulama raporunda **VARSAYIM** olarak listelenir (alan adı uydurma yok).

### 2.2 K-007 sözleşme kalemi

| Madde | Karar |
|-------|--------|
| Çelişki | Aynı metal için genel (`ayar=NULL`) + ayara özel **birlikte olabilir**. |
| Unique (NULL-safe) | PostgreSQL’de `NULL` değerler unique’te varsayılan olarak birbirinden farklıdır. Tercih (Django 6.1): `UniqueConstraint(fields=[...], nulls_distinct=False)` — [docs](https://docs.djangoproject.com/en/6.1/ref/models/constraints/#nulls-distinct) (yalnız PostgreSQL). Alternatif: **iki (veya üç) partial unique**: (1) `ayar__isnull=False` → `(sozlesme, metal, ayar)`; (2) `ayar__isnull=True, metal__isnull=False` → `(sozlesme, metal)`; (3) gerekirse `metal__isnull=True, ayar__isnull=True` → `(sozlesme)` tek genel. Uygulama diliminde biri seçilir; test her iki NULL yolunu kapatır. |
| `clean()` | “Genel varken spesifik yasak” kalkar. |
| `cozumle` | Spesifik > genel; kanal > kanalsız; yüksek versiyon; eşit skor → hata, fiyat yok. |

### 2.3 K-008 sözleşme tarih çakışması

| Madde | Karar |
|-------|--------|
| Kural | Aynı `firma + kontrat_tipi + kanal_anahtarı` kapsamında AKTIF `daterange` çakışmaz. |
| NULL kanal | Ham `satis_kanali_id` exclusion’da **yetersiz** (`NULL` çakışma sayılmaz). İfade: `COALESCE(satis_kanali_id, 0)` (veya sentinel) + `daterange(baslangic, bitis, '[]')` + `&&`. Kanalsız iki AKTIF böylece engellenir. |
| Extension | `ExclusionConstraint` / `gist` için **`btree_gist`** gerekir. Yerel: `btree_gist` 1.8 **DOĞRULANDI** (CREATE EXTENSION OK). **DOĞRULANAMADI:** üretim hosting yetkisi (hosting henüz yok). Kurulamazsa: yayın servisinde `select_for_update` + aralık sorgusu (eşdeğer kural, test aynı). |
| Kanal vs kanalsız | Kanallı AKTIF o kanalda baskın; kanalsız diğer kanallara fallback. Matris testle sabitlenir. |
| İmmutability | AKTIF sonrası kalem/tarih değişmez → yeni versiyon. |
| Permission | `manage_sozlesme`. |

### 2.9 Vergi

§2.9 → ADR-0008 §2.9 (kanonik rapor Sapma kaydı bu atıfı kullanır).

---

## 3. Migration ve veri taşıma

| Adım | İçerik |
|------|--------|
| 1 | Teklif alanları; CASCADE→PROTECT; eşleşme boş bırakılır (kapı; quote engeli ADR-0008) |
| 2 | K-007: `nulls_distinct=False` **veya** partial unique seti |
| 3 | K-008: `btree_gist` + exclusion (`COALESCE` kanal) **veya** servis kilidi; extension **DOĞRULANAMADI** ise servis yolu |
| Reverse | Çakışmada dur; satır silme yok |

Dilim 3.0: staging yok (uzak DB yok, yalnız yerel PostgreSQL); yerel `btree_gist` 1.8 doğrulandı (CREATE EXTENSION OK); üretim yetkisi **DOĞRULANAMADI** — hosting henüz yok. Adım 4 (PriceQuote / trigger) → ADR-0008.

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| Eşleşme boş | Fiyat motorunda kullanılmaz; otomatik onaylama yok |
| §2.9 Vergi / TTL / kur | ADR-0008 |

---

## 5. ÜRÜN SAHİBİ KARARI GEREKİR — ÖNERİ (onay gerekir)

Çoklu YAYINDA teklif seçim sırası → ADR-0008 §5 (3b; quote seçimi).

B-02…B-06 ve servis payı → ADR-0008 §5.

---

## 6. DIŞ DOĞRULAMA GEREKİR

| ID | Konu |
|----|------|
| — | `btree_gist` üretim yetkisi (K-008) |

B-01 (hukuk / gizli hizmet payı) ve diğer dış doğrulamalar → ADR-0008 §6.

---

## 7. Kabul testleri (§12.3 teklif/sözleşme)

| Ek | Test |
|----|------|
| — | `eslestirme_durumu=''` → predicate reddi (kapı; quote uygulaması ADR-0008) |
| — | Versiyon: onay transaction’ında önce eski PASIF, sonra yeni YAYINDA (`select_for_update`) |
| — | K-007 NULL ayar tekilliği; K-008 iki kanalsız AKTIF reddi |
| — | Teklif sahiplik / durum makinesi / CASCADE→PROTECT |

---

## 8. Dilimler

1. **3.0** Kabul; staging yok (uzak DB yok); yerel `btree_gist` 1.8 doğrulandı; üretim yetkisi DOĞRULANAMADI  
2. **3.1** Teklif yaşam döngüsü + versiyon swap + CASCADE→PROTECT + eşleşme predicate — **uygulandı**  
3. **3.2** K-007/K-008 — **uygulandı**  

Dilim **3.3–3.7** → ADR-0008.

---

## 9. Non-goals

Kur politikası, üç model quote hesabı, `PriceQuote` / trigger, alıcı görünürlük, KDV/vergi, e-fatura (ADR-0008 / Faz 4+). Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`.

### Operasyon notu (ADR-0006 O3)

Üretimde fail audit **sidecar** ayrı DB bağlantısı açar; yoğun reddedilen istekte bağlantı sayısını izleyin. TestCase FK fallback üretim yolunu birebir kanıtlamaz; TransactionTestCase kalıcılık kanıtı zorunlu kalır.

---

## 10. Onay checklist

- [x] Eşleşme kapısı (boş = kullanılmaz) + versiyon swap atomik *(dilim 3.1)*  
- [x] K-007/K-008 NULL-safe + btree_gist notu *(dilim 3.2)*  
- [x] CASCADE→PROTECT + teklif durum servisi kapsamı *(dilim 3.1)*  
- [x] Durum: **Kabul edildi** (yalnız ürün sahibi)

---

#### Kaynak: `docs/decisions/ADR-0008-faz3b-kur-fiyatlama-quote.md`

# ADR-0008 — Faz 3b: Kur politikası, fiyat hesabı, PriceQuote snapshot, görünürlük

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Kabul:** 2026-11-08 (ürün sahibi — B-02…B-05 + çoklu YAYINDA; kayıt: [`docs/adr-0008-urun-kararlari.md`](../adr-0008-urun-kararlari.md))  
**Bağlı:** ADR-0007 (Faz 3a, Kabul), ADR-0005, ADR-0006 (Kabul); kanonik rapor K-009, K-011…K-013, K-019; §5.2, §5.4, §9.3, §9.4, §12.3; B-01…B-06  
**Etki analizi:** tarihsel özet bu master arşivinde.  
**Önkoşul:** Dilim 3.3+ kodu bu ADR **Kabul** gerektirir. Teklif yaşam döngüsü / K-007 / K-008 → ADR-0007.  
**Onay:** Ürün sahibi kabul etti (agent kendi taslağını onaylamaz)

**Net not:** B-01 gizli platform hizmet payı hukuk görüşü gelmeden servis payı kalemi **kodlanmaz**; B-02 alıcı görünürlük kararı bunu açmaz. B-06 vergi ertelenmesi (proforma) B-01’i kapatmaz.

Django constraint API (normatif): [Constraints — Django 6.1](https://docs.djangoproject.com/en/6.1/ref/models/constraints/).

---

## 1. Bağlam

ADR-0007 teklif durum makinesi ve sözleşme NULL-safe kısıtlarını tanımlar. Bu ADR: üç fiyat modeli → quote, `PricingService.quote`, kur politikası, `PriceQuote` değişmezliği, alıcı görünürlük, B-06 proforma.

---

## 2. Kararlar (bağlayıcı taslak)

### 2.1.1 Üç teklif fiyat modeli → quote

Mevcut `hesapla()` (`fiyat_hesaplama.py`): yalnız `metal_bedeli = gram × milyem × saf_birim_fiyat` + işçilik + marj + `tas_bedeli`. **GRAM_BIRIM / SABIT_PARCA bilmez.**

Orkestrasyon `PricingService` model seçer; saf çekirdek genişletilir veya model-spesifik saf fonksiyonlar eklenir (Django’suz kalır).

| Model | Quote girdileri | Kalemler (satır) | Yuvarlama |
|-------|-----------------|------------------|-----------|
| **METAL_BAZLI** | `teklif.gram` (veya varyant gram bandı içi), `ayar.milyem`, metal kuru `saf_birim_fiyat`, sözleşme işçilik/marj, teklif `iscilik_override` (varsa işçilik yerine), `teklif_tas_bedeli`, `varyant.ek_bedel` (TRY→quote PB) | `metal`, `iscilik`, `kanal_marj` (alıcı sözleşmesinden), `tas`, `ek_bedel`, `platform_servis` (konfig/sözleşme); **vergi satırı yok** | Ara adım yok; final satır + **vergisiz** `toplam` / `toplam_vergisiz` PB `quantize` (TRY: 0.01, HALF_UP) |
| **GRAM_BIRIM** | `teklif.gram`, `teklif.birim_fiyat`, `teklif.para_birimi` → dönüşüm; taş/ek_bedel/servis/alıcı marj aynı hat | `gram_birim` (= gram × birim, dönüşmüş), `tas`, `ek_bedel`, `platform_servis`, `kanal_marj` — **metal satırı yok**; **vergi satırı yok** | Aynı |
| **SABIT_PARCA** | `teklif.birim_fiyat` (+ PB); gram metal hesabına girmez; taş/ek/servis/marj | `sabit_parca`, `tas`, `ek_bedel`, `platform_servis`, `kanal_marj`; **vergi satırı yok** | Aynı |

Ortak: teklif YAYINDA + geçerli + eşleşme onaylı (ADR-0007 kapısı); kur stale değil; alıcı sözleşmesi çözülür (§2.4.1). Model alan zorunlulukları mevcut DB check + servis. **Faz 3’te KDV/vergi kalemi üretilmez** (§2.9).

### 2.4 PricingService.quote() ve snapshot

**Giriş:** `alici_firma`, `satis_kanali`, `varyant`, isteğe bağlı `teklif_id`; yoksa platform teklif seçimi (§5 ÖNERİ — çoklu YAYINDA).

**Adımlar:** yayınlı ürün/varyant → teklif YAYINDA+geçerli+**eşleşme onaylı** → teklif seçimi → kurlar (stale yok) → **sözleşmeler (§2.4.1)** → PB dönüşüm → model-spesifik hesap (§2.1.1) → **PriceQuote + Line** (immutable).

#### 2.4.1 Hangi sözleşme kimin için?

`FiyatSozlesmesi.KontratTipi`: `ALICI` | `TEDARIKCI` (mevcut model).

| Tip | Firma | Quote’da rol |
|-----|-------|----------------|
| **ALICI** | Alıcı firma | **Satış tarafı:** kanal marjı / platform hizmet (servis payı) kalemleri. `cozumle(firma=alici, kontrat_tipi=ALICI, …)` — **quote için zorunlu çözüm**. Eksik/belirsiz → quote yok. |
| **TEDARIKCI** | Tedarikçi firma | **Maliyet tarafı (opsiyonel Faz 3):** işçilik override yoksa tedarikçi anlaşması; maliyet kırılımı alıcıya gitmez. İlk dilimde: teklif alanları + metal kuru yeterli olabilir; TEDARIKCI sözleşme çözümü “gerekirse” — yoksa teklif `iscilik_override` / model fiyatı. Belirsiz çift çözüm → hata. |

`cozumle` tek firma alır; quote **iki ayrı çağrı** yapabilir (önce ALICI zorunlu; TEDARIKCI koşullu). Snapshot’a her çözülen `sozlesme_id`/`versiyon` yazılır.

**PriceQuote:** alıcı, kanal, varyant, seçilen teklif+versiyon, ALICI (ve varsa TEDARIKCI) sözleşme ref, PB, **`toplam_vergisiz`** (vergi öncesi net; alıcıya vergi dahil/hariç tutar gösterilmez), `gecerlilik_sonu`, kur gözlemleri (alıcı/tedarikçi kur tipi ayrı — B-05), `hesap_girdisi` JSON, aktör, zaman. Belge dili: **proforma / fiyat teklifi** — “fatura” kullanılmaz. Vergi line tipi Faz 3’te üretilmez (§2.9).

**Değişmezlik (zorunlu):** (1) uygulama: `save`/`update` engeli; (2) **DB trigger** (veya eşdeğer RLS/rule) UPDATE/DELETE’i reddeder. Yalnız “mümkünse” değil — finansal zorunluluk.

**Quote TTL:** konfig (B-03); değer yoksa quote üretilmez.

**PriceLock:** Faz 4 arayüzü; bu ADR tanımlar, sipariş tablosu yok.

### 2.5–2.7 K-011 / K-012 / K-019 (Dilim 3.3 kur politikası)

| Madde | Karar |
|-------|--------|
| Sağlayıcı (B-04) | `KurSaglayici`; aynı anda **tek aktif**; otomatik fallback **yok**. Kesintide resolve hata verir. |
| Gözlem | Mevcut `MetalKuru` / `DovizKuru` genişletilir: `saglayici`, `kur_tipi`, piyasa `zaman` ≠ `alinma_zamani`, manuel `neden` + onaylayan. |
| Stale | `(alinma − zaman)` veya `(now − zaman)` > sağlayıcı `max_gecikme_saniye` → geçersiz; sessiz “son bilinen kur” **yok**. |
| Kur tipi (B-05) | `KurPolitikasi`: `alici_kur_tipi` ve `tedarikci_kur_tipi` ayrı; resolve taraf parametresiyle seçer. |
| Manuel giriş | Neden zorunlu; giren ≠ onaylayan (dört göz); `AuditOlay`; yalnız aktif sağlayıcıya bağlanır. |
| Quote TTL (B-03) | `SatisKanali.quote_ttl_saniye` kanal bazlı konfig; değer yoksa ileride quote üretilmez (3.5). TTL ≤ kullanılan gözlemin max gecikmesi (3.5 assert). |
| Dilim sınırı | **3.3** yalnız kur politikası. **3.4** üç model + CurrencyConversion. **3.5** PriceQuote. K-011 taş rename → 3.6. |

### 2.8 Alıcı görünürlük

**B-02 Kabul (A):** Alıcı varsayılan olarak yalnız `toplam_vergisiz` (+ isteğe bağlı gram başı). Kırılım hukuk onayı olmadan açılmaz. Servis payı ayrı görünür satır olmaz.

**B-01 hukuk görüşü gelmeden servis payı kalemi kodlanmaz** (görünürlük kararı servis payı üretimini açmaz). Alıcı yüzey uygulaması → dilim 3.6.

### 2.9 Vergi

**Ürün sahibi kararı (2026-11-08):** Faz 3 belge türü **proforma / fiyat teklifidir**. KDV ve vergi hesaplaması Faz 3 kapsamı **dışındadır**.

| Madde | Karar |
|-------|--------|
| Hesap / saklama | KDV/vergi **hesaplanmaz**, saklanmaz; alıcıya vergi dahil/hariç tutar **gösterilmez**. |
| Toplam | `PriceQuote` toplamı = vergi öncesi (net). Alan/dokümantasyon adı bunu açıkça belirtir (ör. `toplam_vergisiz`). |
| Belge dili | Quote ve çıktıda **“fatura” kullanılmaz**; **“proforma / fiyat teklifi”**. |
| Oran | Vergi oranı kodda, seed’de veya konfigte **sabitlenmez**. |
| İleride | Ayrı ADR; yeni line tipi veya ayrı katman. Mevcut immutable `PriceQuote` kayıtları **geriye dönük değiştirilmez**. |
| B-06 | Mali müşavir doğrulaması **şimdilik gerekmez**; vergi motoru ihtiyacı doğduğunda yeniden açılır. |

B-01 / gizli platform hizmet payı (şeffaflık) bu ertelemeden **etkilenmez** — ayrı hukuk konusu (§6).

---

## 3. Migration ve veri taşıma

| Adım | İçerik |
|------|--------|
| 4 | Taş rename; PriceQuote + Line; quote UPDATE trigger |
| Reverse | Çakışmada dur; satır silme yok |

Adım 1–3 → ADR-0007.

---

## 4. Geri dönüşü kolay varsayımlar

| Konu | Varsayım |
|------|----------|
| TTL / kur tipi / servis payı sayısal değeri | Konfig; yoksa quote yok |
| Vergi | Faz 3’te yok; proforma (B-06 ertelendi — ürün sahibi kararı) |
| Eşleşme boş | Quote yok (ADR-0007 kapısı; otomatik onaylama yok) |

---

## 5. ÜRÜN SAHİBİ KARARLARI (Kabul 2026-11-08)

| ID | Konu | Karar |
|----|------|--------|
| B-02 | Alıcıya görünen kalem | **A —** Varsayılan **yalnız toplam** (+ isteğe bağlı gram başı). Kırılım hukuk onaysız açılmaz. Servis payı ayrı satır görünmez. |
| B-03 | Quote TTL | **A —** **Kanal bazlı**. TTL ≤ ilgili kur gözleminin max gecikmesi. Sayı finans konfigi. Değer yoksa quote yok. |
| B-04 | Kur sağlayıcı | **A —** Aynı anda **tek aktif provider**; otomatik fallback yok. Manuel: neden + dört göz + audit. Max gecikme konfig. |
| B-05 | Kur tipi | **A —** Alıcı ve tedarikçi için **ayrı tipler**; ikisi de (quote diliminde) snapshot’a. |
| — | Çoklu YAYINDA teklif | Alıcı seçmez. Sıra: `oncelik` ↓ → en düşük iç maliyet → `teklif.id` ↑. (Uygulama: quote dilimi 3.5+) |
| — | Servis payı kaynağı | **Kodlanmaz** (B-01 açık). Taslak not: ALICI kalem + global konfig; hukuk sonrası. |
| — | C sınıfı eşleşme istisnası | **Yok.** |
| B-06 | Vergi/KDV | **ERTELENDİ** (2026-11-08): Faz 3 proforma; KDV/vergi yok; mali müşavir şimdilik gerekmez. |

---

## 6. DIŞ DOĞRULAMA GEREKİR

| ID | Konu |
|----|------|
| B-01 | Platform hukuki rol |
| B-01 | **Gizli (faturaya yedirilen, görünmeyen) platform hizmet payı** — B2B/B2C şeffaflık ve fatura uyumu. **B-06 ertelemesi bunu kapatmaz** (proforma toplamı yine hizmet payını içerebilir; hukuk görüşü açık kalır). |
| — | Kur sağlayıcı lisans |
| — | TRY dışı yuvarlama muhasebesi |

`btree_gist` → ADR-0007 §6.

---

## 7. Kabul testleri (§12.3)

| Ek | Test |
|----|------|
| — | Üç fiyat modeli için quote kalem/toplam (birim test + servis) |
| — | Quote UPDATE trigger reddi |
| — | Kur stale → quote yok; snapshot’a kur yazılır (§12.3 ilgili maddeler) |
| — | Alıcı yüzeyinde maliyet/tedarikçi kimliği yok |

---

## 8. Dilimler

4. **3.3** Kur politikası  
5. **3.4** Üç model hesap + CurrencyConversion  
6. **3.5** quote + trigger immutability — uygulandı  
7. **3.6** kör havuz + K-011 — uygulandı  
8. **3.7** PriceLock arayüzü → Faz 4  

Dilim **3.0–3.2** → ADR-0007.

---

## 9. Non-goals

**KDV/vergi hesaplama ve resmi e-fatura/e-arşiv üretimi (Faz 3 dışı)**; belge türü proforma / fiyat teklifi. Stok/sipariş (Faz 4), DRF (Faz 7), SAP, `urunleri_birlestir`. Teklif durum makinesi / K-007 / K-008 (ADR-0007).

---

## 10. Onay checklist

- [x] B-02…B-05 + çoklu YAYINDA: ürün sahibi kabul (2026-11-08)  
- [x] B-06 vergi/KDV: **ertelendi** (proforma)  
- [x] B-01 / gizli hizmet payı: **kapsam dışı** (hukuk bekleniyor; kod yok)  
- [x] ALICI vs TEDARIKCI sözleşme rolü (§2.4.1)  
- [x] Durum: **Kabul edildi** (ürün sahibi)  
- [x] Üç fiyat modeli + `toplam_vergisiz` + quote trigger — dilim 3.4–3.5 uygulama  
- [ ] §6 kalan dış doğrulama (kur lisans, TRY dışı yuvarlama) — uygulama sırasında açık

---

#### Kaynak: `docs/decisions/ADR-0009-admin-yuzey-sertlestirme.md`

# ADR-0009 — Admin yüzey sertleştirme (post-3.1)

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlı:** ADR-0003, ADR-0005, ADR-0006, ADR-0007 (Kabul); denetim: [`faz3-1-sonrasi-guvenlik-denetimi.md`](../architecture/faz3-1-sonrasi-guvenlik-denetimi.md)  
**Onay:** Ürün sahibi — 2026-11-08

**Kapsam notu:** Bu ADR, dilim 3.2 (K-007/K-008) ve ADR-0008’den **önce** kapanması gereken admin/servis deliklerini bağlar. Kabul olmadan kod yok.

---

## 1. Bağlam

Dilim 3.1 teklif yaşam döngüsünü serviste kurdu. Bağımsız denetim: servis sağlam; admin ve maliyet görünürlüğü kuralları atlıyor veya yanlış kapatıyor (bulgu H1–H5). Faz 2.1 O1 yalnız kısmi yüzeyde.

---

## 2. Kararlar (öneri — Kabul sonrası bağlayıcı)

| Kod | Karar |
|-----|--------|
| **H1** | `is_staff` / `is_superuser` / `user_permissions` / `groups`: yalnız platform + `manage_all_users` (veya eşdeğer) düzenler. Tenant admin formunda bu alanlar yok veya readonly. Test: `tedarikci_sahip` / `alici_yonetici` bayrak yazamaz. |
| **H2** | `TedarikciTeklif` **YAYINDA** (ve tercihen `ONAY_BEKLIYOR`): fiyat/gram/model/geçerlilik/`oncelik`/`stok_adet` admin’de readonly veya `has_change_permission` false (platform istisnası yoksa). Değişiklik yalnız `yeni_versiyon_olustur` + onay. `oncelik` tedarikçi tarafından set edilmez (ADR-0008 seçim sırası platform alanı). |
| **H3** | Maliyet görünürlüğü ayrılır: **alıcı** → maliyet yok; **tedarikçi** → yalnız **kendi** teklifinin `birim_fiyat` / `iscilik_override` (ve gerekirse gram); **platform** → tümü. `user_may_see_fiyat_maliyet` bölünür veya `user_may_see_own_teklif_maliyet` eklenir. Alıcıya sızıntı yok. |
| **H4** | ADR-0006 **O1** kilidi tüm ürün yüzeylerine: `VaryantAdmin`, `UrunTasiAdmin`, `UrunKanalAdmin` (+ ilgili inline’lar). `onay_bekliyor` iken tedarikçi `list_editable` dahil yazamaz. Test: bağımsız admin + changelist. |
| **H5** | `yeni_versiyon_olustur`: (a) `eslestirme_durumu` / `hedef_urun` / kanıt **boşaltılır** (otomatik onay yok) **veya** (b) gram bandı + hedef tutarlılık `eslestirmeyi_onayla` ile aynı kontrollerden geçer; aksi halde ONAY_BEKLIYOR + eşleşme bekliyor. Tercih: **(a)** daha küçük ve geri dönüşü kolay — VARSAYIM aksi ürün sahibi (b) demedikçe. |
| **D1** | `requirements.txt` UTF-8 (BOM’suz); `Pillow` pin (ImageField kullanılıyor). Encoding düzeltmesi D1 ile birlikte. |

### Bilinçli ertelenen (bu ADR dışı)

- K-007/K-008, `cozumle` sıra → dilim 3.2  
- Quote / kur / geçerlilik cron → ADR-0008  
- AuditOlay admin + immutability, `approve_firma` servisi, slug stratejisi → sonraki sertleştirme  
- `islcilik_dahil_mi` rename → pahalı; dokunulmaz  

---

## 3. Migration

H1–H5 için şema gerekmez (beklenen). D1 yalnız requirements. H5 (a) veri migration istemez.

---

## 4. Testler (zorunlu, çalıştırılacak)

- H1: tenant rolü superuser/staff yazamaz; platform yazabilir.  
- H2: YAYINDA alan admin save reddi veya readonly; versiyon yolu çalışır.  
- H3: tedarikçi kendi teklifinde birim_fiyat görür/yazar; alıcı görmez; başka tedarikçi yok.  
- H4: `onay_bekliyor` iken VaryantAdmin / list_editable red.  
- H5: yeni versiyonda eşleşme boş (veya bant ihlali red); predicate false.  
- Mevcut suite regresyon (164+).

---

## 5. Non-goals

DRF, stok, finans, ADR-0008 quote motoru, K-007/K-008 şema.

---

## 6. Onay checklist

- [x] H1–H5 + D1 metni ürün sahibi tarafından kabul  
- [x] Durum: **Kabul edildi** (yalnız ürün sahibi)  
- [x] Uygulama + test + [`faz3-1-admin-sertlestirme-raporu`](../architecture/faz3-1-admin-sertlestirme-raporu.md)  

---

## 7. Uygulama sırası (Kabul sonrası)

Tek PR/dilim: H1 → H4 → H3 → H2 → H5 → D1; sonra tam test suite; rapor.

---

#### Kaynak: `docs/decisions/ADR-0010-faz3-7-pricelock.md` (commit öncesi; özet §6.1)

Tam madde listesi §6.1 L-01…L-11. Durum: **Taslak** (ürün sahibi kabulü beklenir).

## 7. Geçmiş fazlar ve uygulama geçmişi

> Aşağısı **tarihsel kayıttır**. Eski bulgular otomatik olarak güncel durum değildir; güncel için §2 ve §12.

### Faz 0 — Standartlar / denetim
- Amaç: Secret, requirements, tenant denetim, agent kuralları.  
- Çıktı: ADR-0001/0002, denetim raporları (içerik bu master’a özetlendi).  
- Devir: Faz 1 kimlik.

### Faz 1 — Kimlik / RBAC
- `Firma` NOT NULL, roller, perm matrisi, `AuditOlay`, platform bootstrap.  
- ADR-0003 (+ addendum). Testler yeşil (tarihsel raporlar).  
- Devir: katalog ownership.

### Faz 2 / 2.1 — Katalog
- `olusturan_firma`; onay SM; eşleştirme B1–B3; admin kilidi. ADR-0005/0006.  
- Devir: teklif fiyatlama.

### Faz 3.1 — Teklif yaşam döngüsü (ADR-0007)
- Durum makinesi, versiyon swap, PROTECT, predicate. Migration 0005.  
- Sonra ADR-0009 admin H1–H5.

### Faz 3.2 — K-007 / K-008
- Sözleşme unique/exclusion, `cozumle`. Migration 0006.

### Faz 3.3 — Kur politikası
- Tek aktif provider, KurPolitikasi, stale fail-closed, quote_ttl alanı. Migration tanimlar 0002/0003.

### Faz 3.4 — Üç model + CurrencyConversion
- `hesapla_metal_bazli` / `gram_birim` / `sabit_parca`; TRY 0.01 HALF_UP; PB dönüşüm. Commit zinciri `b516893` içinde.

### Faz 3.5 — PriceQuote
- `pricing_service.quote`; Line; app+DB immutability (`0007`). Test 14+ OK (tarihsel).

### Faz 3.6 — Kör havuz + K-011
- `TeklifTasMaliyeti`; `buyer_quote`; admin maske. Commit **`7802eb4`**. Suite 254 OK (tarihsel handoff).

### Faz 3.7 — PriceLock
- Model + `lock_quote` + expire + concurrency; migrations `0010` (model/guard), `0011` (L-04 TTL INSERT), `0012` (L-07 perms).  
- L-07/L-10: dedicated permission; on-behalf gerekçe; audit.  
- Test: PriceLock **34 OK**; suite **288 OK**.  
- ADR-0010 **Taslak** (resmi Kabul yok).  
- Devir: Faz 4 **kodlanmaz** — önce ADR-0010 Kabul + Faz4 ADR Kabul + U-012.

### Açık temalar
B-01/B-06; dual stock; DRF yok; Order yok; TRY dışı yuvarlama; ADR-0010 resmi Kabul; U-001…U-012.

---

## 8. Hedef mimari ve Prosperer gap analizi

Prosperer sütunu: hedef kıyas (**DOĞRULANAMADI** runtime).

| # | Yetenek | Mevcut | Hedef | Eksik BE | Eksik FE | Güvenlik | Öncelik | Bağımlılık | Kabul |
|---|---------|--------|-------|----------|----------|----------|---------|------------|-------|
| 1 | B2B katalog | KISMİ | Zengin katalog+arama | Search, import | Buyer browse | Tenant; olusturan gizli | P1 | Faz2 | Alıcı yalnız yayınlı |
| 2 | Firma/şube org | KISMİ | Şube/hiyerarşi | Org model | Org UI | Org scope | P2 | F1 | İzolasyon |
| 3 | Fiyat listesi/koşul | KISMİ→güçlü | Sözleşme+liste UI | Liste API | Finans UI | Maske | P0 koru | ADR-0008 | Quote fail-closed |
| 4 | Teklif/RFQ | KISMİ | RFQ+müzakere | RFQ SM | Buyer/sup UI | Kör | P1 | Teklif | Audit SM |
| 5 | Sepet/checkout | Yok | Cart+checkout | Cart svc | Buyer sepet | IDOR | P0 | Lock, rezerv | Lock olmadan sipariş yok |
| 6 | Sipariş | Yok | Order SM+snapshot | Order | Ops/buyer | Kör+audit | P0 | Cart | Fiyat değişmez |
| 7 | Çok depo/stok | Yok (dual alan) | Ledger+WH | stok app | Ops | Tedarikçi scope | P0 | F4 ADR | Count edit yok |
| 8 | Rezervasyon/ATP | Yok | TTL+ATP | Reservation | Ops | Oversell yok | P0 | Ledger | PG concurrent |
| 9 | Ödeme/cari | Yok | Payment+cari | finans | Buyer/finans | Audit | P0 | Order, U-* | State tutarlı |
| 10 | Sevkiyat | Yok | Shipment+carrier | lojistik | Takip | Adres tenant | P1 | QC | QC fail blok |
| 11 | İade/SH | Yok | RMA | after-sales | Buyer | U-004 | P1 | Ship | SM+ledger |
| 12 | Portallar | Yok (admin) | Buyer/sup portal | API | Next/PWA | Aynı RBAC | P1 | API | Admin’siz akış |
| 13 | Onay workflow | KISMİ | Limit+zincir | workflow | Kuyruk | Escalation yok | P2 | Order, org | Limit blok |
| 14 | Raporlama | Yok | Raporlar | read model | Dashboard | Rol kesit | P2 | Order data | Sızıntı yok |
| 15 | Entegrasyon | Yok | ERP/ödeme/kargo | hub | Mapping | Secret | P1 | API | Fail-closed |
| 16 | API/headless | Yok | /api/v1 + PWA | DRF | Client | Object perm | P0 PRE | ADR-0002 | Tenant test |
| 17 | i18n/FX | KISMİ | Locale+PB | i18n | Dil | — | P3 | U-009 | PB karışmaz |
| 18 | Bildirim/belge | Yok | Outbox+S3 | apps | Inbox | Belge tenant | P1 | Events | Audit |
| 19 | Güvenlik/audit | KISMİ→güçlü | API+ops sert | Her domain | — | P0 sürekli | — | Isolation yeşil |

**En kritik gap sırası:** Inventory+reservation → Cart/Order+Lock → PRE-API → Finance → QC/Ship → Portallar.

---

## 9. Ana geliştirme yol haritası

**Kural:** Faz kodu = ilgili ADR **Kabul** + açık talimat. Bu bölüm planlamadır.

### Gate (Faz 4 öncesi)
G0 3.7 commit · G1 ADR-0010 kabul · G2 Faz4 ADR kabul · G3 U-002/U-008 kapsam net · G4 PRE-API veya admin-only kararı (U-012).

### PRE — API iskeleti
Amaç: DRF pin, `/api/v1/health`, perm/tenant test iskeleti, OpenAPI, Idempotency.  
Kapsam dışı: Tam Prosperer API.  
İşler: PRE-001…005.  
Durum: PLANLANDI.

### Faz 4 — Ticari işlem çekirdeği
Amaç: Ledger → rezervasyon → cart → checkout/lock → order+snapshot.  
Kapsam dışı: Ödeme, QC, kargo, RFQ, B-01/B-06.  
Önkoşul: G0–G2.  
Alt: F4-001…070.  
Kabul: Oversell yok; expired lock checkout fail; sipariş fiyatı kurdan etkilenmez.  
Durum: PLANLANDI (kod yok).

### Faz 5 — Finans
Amaç: Ledger, cari, payment intent, adapter.  
Gate: U-003…U-007.  
Durum: PLANLANDI / kısmen Blocked.

### Faz 6 — QC & lojistik
QC gram, shipment, POD, return. QC fail → ship blok.

### Faz 7 — API & entegrasyon
Buyer/Supplier/Admin API olgunluk, rate limit, webhook, ERP iskelet. PRE’yi büyütür.

### Faz 8 — Prod readiness
CI, log, Sentry, backup, secret, perf, güvenlik paketi, runbook.

### Faz 9 — Portal bütünleşme
Faz içi ince UI erken gelir; 9 deneyim kalitesi + dashboard.

### Faz 10 — Kurumsal & RFQ
Şube, limit, onay, RFQ, özel üretim.

### Faz 11 — Analitik
Rapor, fiyat/stok analitik, bildirim otomasyonu, opsiyonel AI (insan onayı).

### Faz 12 — i18n & ekosistem
Dil, PB yuvarlama U-009, ülke kuralları, partner API.

**Bağımlılık özeti:** `3.7 → ADR-0010+F4 ADR → PRE → ledger → reservation → cart → checkout/lock → order → (U-*) finance → QC/ship → API olgunluk → ops → portal → RFQ/org → analytics → i18n`.


---

## 10. İş havuzu (kanonik)

Toplam benzersiz iş/karar kartı: **111**

### [F10-001] Org/şube modeli ADR

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Product
- **Bağımlılıklar:** ADR-0003 (tek firma/rol gerilimi netleştir)
- **Kabul kriterleri:** Ürün sahibi kabul

### [F10-010] Şube / org birimi modeli

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F10-001
- **Kabul kriterleri:** İzolasyon testleri

### [F10-011] Satın alma yetki matrisi genişlemesi

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Security
- **Bağımlılıklar:** F10-010
- **Kabul kriterleri:** has_perm; rol string switch yok

### [F10-012] Harcama limiti motoru

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F10-011, Order
- **Kabul kriterleri:** Limit aşımı blok

### [F10-013] Onay iş akışı (çok adımlı)

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F10-012
- **Audit:** her onay
- **Kabul kriterleri:** Atlanan adım yok

### [F10-014] Onay kuyruğu UI

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F10-013
- **Kabul kriterleri:** Yetkisiz onay butonu yok

### [F10-020] RFQ / RFQLine / RFQMessage modelleri

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Catalog, Pricing
- **Kabul kriterleri:** SM servisten

### [F10-021] Katalog dışı ürün talebi

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-020
- **Kabul kriterleri:** Platform aracılı eşleştirme

### [F10-022] Özel üretim / tasarım talep akışı

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F10-020, F6 QC bağ opsiyonel
- **Kabul kriterleri:** Revizyon geçmişi

### [F10-023] RFQ buyer/supplier UI (maskeli)

- **Faz:** Faz 10
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F10-020, F7 APIs
- **Kabul kriterleri:** Kimlik sızıntısı yok

### [F11-001] Raporlama veri modeli / read-model kararı

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Product
- **Bağımlılıklar:** Order+Finance veri
- **Kabul kriterleri:** ADR veya teknik not

### [F11-010] Ticari raporlar (sipariş/ciro tenant kesitli)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F11-001
- **Kabul kriterleri:** Çapraz tenant yok

### [F11-011] Fiyat analitiği (quote/lock geçmişi)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** PriceQuote, PriceLock
- **Gizlilik:** alıcıya maliyet yok
- **Kabul kriterleri:** Platform finans rolü

### [F11-012] Stok tahmin / ATP görünümü (kural tabanlı v1)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F4-012
- **Kapsam dışı:** ML zorunluluğu
- **Kabul kriterleri:** Deterministik formül dokümante

### [F11-013] Bildirim otomasyonu kuralları

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Notification outbox
- **Kabul kriterleri:** Sipariş/QC olayında bildirim

### [F11-014] Anomali tespiti (basit eşik)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F11-010
- **Kabul kriterleri:** Audit + ops uyarı

### [F11-015] AI ürün eşleştirme asistanı (opsiyonel)

- **Faz:** Faz 11
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** Eşleştirme servisi, veri politikası
- **Kapsam dışı:** Otomatik onay
- **Kabul kriterleri:** İnsan onayı zorunlu; kör havuz bozulmaz

### [F12-001] Dil/i18n strateji ADR

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** —
- **Kabul kriterleri:** Ürün sahibi

### [F12-010] Katalog/UI çeviri altyapısı

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Backend/Frontend
- **Bağımlılıklar:** F12-001
- **Kabul kriterleri:** En az 2 locale smoke

### [F12-011] TRY dışı yuvarlama muhasebe doğrulaması uygulama

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** U-009 (ADR-0008 §6)
- **Kabul kriterleri:** PB bazlı quantize testleri

### [F12-012] Ülke bazlı ticari kural motoru (iskelet)

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** F12-001, vergi U-*
- **Kabul kriterleri:** Ülke yoksa fail-closed veya TR varsayılan (karar)

### [F12-013] Bölgesel entegrasyon adaptör slotları

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Integration
- **Bağımlılıklar:** F7-E02
- **Kabul kriterleri:** Registry genişletilebilir

### [F12-014] Partner/developer API programı

- **Faz:** Faz 12
- **Durum:** Backlog · **Öncelik:** P3 · **Tip:** Product
- **Bağımlılıklar:** F7-E01, OpenAPI
- **Kabul kriterleri:** Partner key + scope; kör havuz

### [F4-001] Faz 4 ADR taslağı (stok üçlüsü + sipariş SM + PriceLock bağ)

- **Faz:** Faz 4
- **Durum:** Backlog
- **Öncelik:** P0
- **Tip / Domain:** Product
- **Bağımlılıklar:** U-001 (ADR-0010), mevcut 3.7 kod
- **Amaç:** Onaylanabilir veri modeli ve durum geçişleri
- **Kapsam:** Warehouse, Balance, Movement, Reservation, Cart, Order, Lock→Order; dual-stock taşıma politikası
- **Kapsam dışı:** Ödeme, QC, kargo kodu
- **Domain/model:** Yeni app’ler önerisi (`stok`, `siparis` veya eşdeğer)
- **Servis/API:** Servis sınırları ADR’de
- **Arayüz:** Yok (belge)
- **Audit:** Kritik geçişler listelenir
- **Migration:** Dual field stratejisi
- **Test:** ADR kabul checklist
- **Kabul kriterleri:** Ürün sahibi “Kabul”; agent kendi onaylamaz
- **Dokümantasyon:** Karar kaydı `KUYUMBANK_MASTER.md` §6’ya ADR ID ile eklenir

### [F4-002] Dual stock alan envanteri ve deprecation planı

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-001
- **Amaç:** `Varyant.stok` / `TedarikciTeklif.stok_adet` ikiliğini ledger’a taşıma planı
- **Kapsam:** Okuma noktaları listesi; yazma yasaklama sırası
- **Kapsam dışı:** Ledger uygulaması (F4-011)
- **Kabul kriterleri:** Plan ADR ekinde; silent dual-write yok

### [F4-010] Warehouse modeli + tenant scope

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-001
- **Amaç:** Depo kaydı (platform/tedarikçi sahipliği net)
- **Kapsam:** Model, admin salt, selector
- **Kapsam dışı:** Transfer UI
- **Domain/model:** `Warehouse`
- **Tenant/RBAC/gizlilik:** Tedarikçi yalnız kendi depoları
- **Audit:** create/update
- **Test:** izolasyon
- **Kabul kriterleri:** Yetkisiz depo görünmez

### [F4-011] StockMovement immutable ledger

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-010
- **Amaç:** Stok değişiminin tek kaynağı hareket satırı
- **Kapsam:** Movement tipi; PROTECT; app+DB immutability politikası
- **Kapsam dışı:** Reservation
- **Test:** update/delete reddi; birim karışmama
- **Kabul kriterleri:** Doğrudan balance edit yok
- **Decimal:** gram/adet/karat birim alanları (U-002)
- **Concurrency:** atomic yazım

### [F4-012] StockBalance projeksiyonu

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-011
- **Amaç:** Kullanılabilir / rezerve / bloke ayrımı
- **Kapsam:** Balance satırı; movement sonrası güncelleme servisi
- **Test:** tutarlılık invariant
- **Kabul kriterleri:** available = on_hand − reserved − blocked (formül ADR’de)

### [F4-013] Stok düzeltme servisi (adjustment)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend/Security
- **Bağımlılıklar:** F4-012
- **Amaç:** Düzeltmeler movement ile; audit zorunlu
- **Kabul kriterleri:** Neden + aktör olmadan adjustment yok

### [F4-020] StockReservation modeli + TTL

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-012
- **Amaç:** Checkout hold; sepet stok düşürmez
- **Kapsam:** TTL; durum AKTIF/SURESI_DOLDU/TUKETILDI
- **Test:** expire `now` enjekte
- **Kabul kriterleri:** Expired rezervasyon available’a döner

### [F4-021] Rezervasyon concurrency (select_for_update)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-020
- **Amaç:** Oversell engeli
- **Test:** TransactionTestCase paralel rezervasyon PG
- **Kabul kriterleri:** İkinci aşırı rezervasyon ValidationError

### [F4-022] Rezervasyon expire görevi (iskelet)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** F4-020; Celery kararı opsiyonel
- **Amaç:** Süresi dolmuş rezervasyonları toplu expire
- **Kapsam dışı:** Tam Celery prod kurulumu (F8)
- **Kabul kriterleri:** management command veya task ile deterministic test

### [F4-030] Cart / CartLine modelleri

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-001
- **Amaç:** Alıcıya özel geçici sepet
- **Kabul kriterleri:** Başka firma sepeti DoesNotExist/403

### [F4-031] Sepete satır ekleme (quote/varyant bağ)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-030, PriceQuote
- **Amaç:** Sepet satırı fiyat referansı (lock checkout’ta)
- **Gizlilik:** tedarikçi/maliyet yok
- **Kabul kriterleri:** Kör alan sızıntısı yok

### [F4-040] Checkout servisi

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-031, F4-020, lock_quote
- **Amaç:** Geçerli PriceLock + rezervasyon → sipariş adayı
- **Kapsam dışı:** Payment capture
- **Kabul kriterleri:** Expired lock/quote ile checkout fail
- **Idempotency:** checkout key

### [F4-041] Checkout fail audit durable

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** F4-040
- **Kabul kriterleri:** Fail audit rollback’te silinmez

### [F4-050] Order / OrderLine + durum makinesi

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-040
- **Amaç:** Kontrollü SM; serbest status string yok
- **Audit:** her transition
- **Kabul kriterleri:** Yasak geçiş PermissionDenied/ValidationError

### [F4-051] PriceLock → Order bağlama + satır fiyat snapshot

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-050, ADR-0010 L-11
- **Amaç:** Sipariş satırına quote tutarlarının kopyası; lock siparişe bağlanır
- **Kabul kriterleri:** Kur değişince geçmiş OrderLine tutarı sabit
- **Immutability:** snapshot sonradan değişmez

### [F4-052] Rezervasyonun siparişe tüketilmesi

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-051, F4-020
- **Amaç:** Reservation → consumed; movement satış
- **Kabul kriterleri:** Çift tüketim yok

### [F4-053] Sipariş iptal (stok iade hareketi; finans yok)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F4-052; U-004 (finans kısmı Blocked)
- **Kapsam:** Stok serbest bırakma; ödeme iadesi yok
- **Kabul kriterleri:** İptal sonrası available artar

### [F4-060] Buyer cart/order API (ince)

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-001, F4-050
- **Gizlilik:** buyer_quote kuralları
- **Kabul kriterleri:** Supplier token ile 404/403

### [F4-061] Platform ops sipariş listesi API/admin

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F4-050
- **Kabul kriterleri:** view_all olmadan çapraz tenant yok

### [F4-062] Minimal buyer sepet/sipariş ekranı

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F4-060
- **Kapsam:** Tek akış; portal bütünleşme Faz 9
- **Kabul kriterleri:** E2E smoke (manuel veya Playwright iskelet)

### [F4-070] Legacy stok alanlarını read-only / kaldırma dilimi

- **Faz:** Faz 4
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-012, F4-002
- **Kabul kriterleri:** Yazma yolu ledger dışı kapalı; migration güvenli

### [F5-001] Finans ADR (ledger + ödeme SM)

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Product
- **Bağımlılıklar:** F4-050, U-003, U-005
- **Amaç:** Onaylı finans modeli
- **Kapsam dışı:** Provider seçimi detayı
- **Kabul kriterleri:** ADR Kabul

### [F5-010] FinancialLedger / hareket modeli (append-only)

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F5-001
- **Amaç:** Silinemez finansal hareket; contra ile ters kayıt
- **Audit:** her hareket
- **Kabul kriterleri:** DELETE yasak (app+DB politika)
- **Decimal:** para birimi zorunlu

### [F5-011] Cari hesap (firma bakiyesi projeksiyonu)

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F5-010, U-005
- **Kabul kriterleri:** Alıcı başkasının carisini görmez

### [F5-012] Order ↔ PaymentIntent bağlama

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** F4-050, F5-010
- **Amaç:** Sipariş durum makinesi ile ödeme tutarlılığı
- **Kabul kriterleri:** Çift tahsilat yok
- **Idempotency:** payment intent key

### [F5-013] Finansal audit zorunlu alanlar

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** F5-010
- **Kabul kriterleri:** actor, amount, currency, order ref, success

### [F5-020] Ödeme sağlayıcı adapter arayüzü

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F5-012
- **Kapsam:** Port + fake adapter test
- **Kapsam dışı:** Canlı banka hesabı
- **Kabul kriterleri:** Adapter fail-closed
- **Secret:** env only

### [F5-021] Tahsilat kaydı + webhook iskeleti

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F5-020, PRE-idempotency
- **Kabul kriterleri:** Tekrarlayan webhook tek sonuç

### [F5-022] Tedarikçi hak ediş iskeleti (politika sonrası)

- **Faz:** Faz 5
- **Durum:** Blocked · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** U-006, F5-010
- **Kapsam:** Placeholder model; oran sabitleme yok
- **Kabul kriterleri:** U-006 olmadan production hesap yok

### [F5-023] İade / mahsup hareketleri

- **Faz:** Faz 5
- **Durum:** Blocked · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** U-004, F6-E03
- **Kabul kriterleri:** Politika metni + test

### [F5-030] Buyer finans özeti API (maskeli)

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F5-011, PRE-001
- **Gizlilik:** komisyon/marj yok
- **Kabul kriterleri:** Kör alan assert

### [F5-031] Platform finans ops ekranı/API

- **Faz:** Faz 5
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F5-010
- **Kabul kriterleri:** RBAC finance rolü

### [F6-001] QC ADR (tolerans, gram farkı)

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Product
- **Bağımlılıklar:** F4-050, U-008
- **Kabul kriterleri:** ADR Kabul

### [F6-010] QualityInspection modeli + SM

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-001
- **Audit:** geçişler
- **Kabul kriterleri:** Fail → shipment blok bayrağı

### [F6-011] Gram/ağırlık ölçüm kaydı

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-010, Decimal
- **Kabul kriterleri:** Tolerans dışı otomatik fail (konfig)

### [F6-012] Taş sertifika belge bağı (metadata)

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Backend
- **Bağımlılıklar:** Document domain iskelet
- **Kabul kriterleri:** Tenant’lı belge erişimi

### [F6-020] Shipment modeli + SM

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-010 (QC pass)
- **Kabul kriterleri:** QC fail iken create ValidationError
- **Kör havuz:** alıcı/tedarikçi kimlik maskesi

### [F6-021] Carrier adapter arayüzü + fake

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F6-020
- **Kabul kriterleri:** Fail-closed; secret yok kodda

### [F6-022] Teslimat kanıtı (POD) kaydı

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-020
- **Kabul kriterleri:** POD olmadan “teslim” geçişi opsiyonel politika

### [F6-023] Buyer sevkiyat takip API (maskeli)

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-020, PRE
- **Kabul kriterleri:** Tedarikçi kimliği yok

### [F6-030] Return/Dispute SM

- **Faz:** Faz 6
- **Durum:** Blocked · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** U-004, F6-020
- **Kabul kriterleri:** Finans hareketi politika sonrası

### [F6-031] İade stok hareketi

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F6-030, F4-011
- **Kabul kriterleri:** Ledger ile iade

### [F6-032] Platform uyuşmazlık ops kuyruğu

- **Faz:** Faz 6
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F6-030
- **Kabul kriterleri:** RBAC ops

### [PRE-001] DRF bağımlılık pin + INSTALLED_APPS

- **Faz:** PRE
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Infrastructure
- **Bağımlılıklar:** ADR-0002 süreci
- **Amaç:** Kodun import ettiği paket requirements’a girer
- **Kapsam dışı:** Celery zorunluluğu
- **Kabul kriterleri:** `makemigrations`/test yeşil; kullanılmayan paket yok

### [PRE-002] `/api/v1/health` + auth iskeleti

- **Faz:** PRE
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** PRE-001
- **Kabul kriterleri:** Unauth health public; korumalı route 401

### [PRE-003] API permission + tenant test iskeleti

- **Faz:** PRE
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Security
- **Bağımlılıklar:** PRE-002
- **Kabul kriterleri:** Örnek endpoint’te çapraz firma fail

### [PRE-004] OpenAPI şema yayını (taslak)

- **Faz:** PRE
- **Durum:** Backlog · **Öncelik:** P0 · **Tip:** Backend
- **Bağımlılıklar:** PRE-002
- **Kabul kriterleri:** schema endpoint üretir

### [PRE-005] Idempotency-Key sözleşme notu + middleware iskelet

- **Faz:** PRE
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-002
- **Kabul kriterleri:** Aynı key tekrarında aynı sonuç (en az bir POST örneği)

### [F7-010] Buyer API yüzey standardı

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003, F4-060
- **Gizlilik:** kör havuz zorunlu test
- **Kabul kriterleri:** Maliyet/tedarikçi sızıntı assert

### [F7-011] Supplier API yüzey standardı

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003
- **Kabul kriterleri:** Yalnız kendi teklif/iş; alıcı kimliği yok

### [F7-012] Admin/operations API

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-003, view_all
- **Kabul kriterleri:** Perm matrisi

### [F7-013] Rate limiting

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** PRE-002
- **Kabul kriterleri:** Limit aşımında 429

### [F7-014] Hata sözleşmesi (problem+json veya proje standardı)

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** PRE-002
- **Kabul kriterleri:** Doküman + test

### [F7-015] API versioning politikası

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Product
- **Bağımlılıklar:** PRE-004
- **Kabul kriterleri:** ADR notu

### [F7-020] Webhook outbox modeli

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** Order events
- **Kabul kriterleri:** Retry + idempotent delivery kaydı

### [F7-021] ERP adapter iskeleti (SAP hedefi)

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F7-020
- **Kapsam dışı:** Canlı SAP
- **Kabul kriterleri:** Fake ERP roundtrip test

### [F7-022] Ödeme/lojistik connector kayıt defteri

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Integration
- **Bağımlılıklar:** F5-020, F6-021
- **Kabul kriterleri:** Tek registry

### [F7-023] CRM sync iskeleti

- **Faz:** Faz 7
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Integration
- **Bağımlılıklar:** F7-020
- **Kabul kriterleri:** Opt-in mapping

### [F8-001] CI pipeline (lint + test PG)

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** —
- **Kabul kriterleri:** PR’da test koşar

### [F8-002] Structured logging standardı

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** —
- **Kabul kriterleri:** request_id; secret log yok

### [F8-003] Hata izleme (Sentry veya eşdeğer) bağlama planı

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** F8-002
- **Kabul kriterleri:** staging’de event görülür

### [F8-004] Backup/restore runbook

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Infrastructure
- **Bağımlılıklar:** PostgreSQL
- **Kabul kriterleri:** Dokümanlı restore tatbikatı

### [F8-005] Secret yönetimi kontrol listesi

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** —
- **Kabul kriterleri:** `.env` repo dışı; rotation notu

### [F8-006] Performans smoke (quote/lock/order kritik yollar)

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Backend
- **Bağımlılıklar:** F4-050
- **Kabul kriterleri:** Baseline raporu

### [F8-007] Güvenlik test paketi (tenant/IDOR regresyon)

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Security
- **Bağımlılıklar:** API yüzeyleri
- **Kabul kriterleri:** Checklist yeşil

### [F8-008] Operasyon runbook (deploy/migrate)

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Infrastructure
- **Bağımlılıklar:** F8-001
- **Kabul kriterleri:** Adım adım doküman

### [F8-009] Rate limit prod konfig

- **Faz:** Faz 8
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Infrastructure
- **Bağımlılıklar:** F7-013
- **Kabul kriterleri:** Ortam bazlı ayar

### [F9-001] Frontend teknoloji ADR (Next.js vs alternatif)

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Product
- **Bağımlılıklar:** PRE-001
- **Kabul kriterleri:** Ürün sahibi kabul

### [F9-010] Buyer dashboard iskeleti

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F9-001, F7-010
- **Kabul kriterleri:** Auth + tenant context

### [F9-011] Katalog arama/browse UI

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F9-010, search API
- **Gizlilik:** kör
- **Kabul kriterleri:** Maliyet sızıntısı yok

### [F9-012] Sepet/sipariş portal akışı

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F4-062, F7-010
- **Kabul kriterleri:** E2E checkout smoke

### [F9-013] Supplier dashboard + teklif yönetimi UI

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F7-011
- **Kabul kriterleri:** Alıcı kimliği görünmez

### [F9-014] Stok/teslimat görünümü (rol bazlı)

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** F4-012, F6-023
- **Kabul kriterleri:** Rol kesiti doğru

### [F9-015] Finansal self-service (alıcı)

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F5-030
- **Kabul kriterleri:** Maskeli özet

### [F9-016] Responsive + PWA temel

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P2 · **Tip:** Frontend
- **Bağımlılıklar:** F9-010
- **Kabul kriterleri:** Mobil smoke

### [F9-017] Self-service profil/adres

- **Faz:** Faz 9
- **Durum:** Backlog · **Öncelik:** P1 · **Tip:** Frontend
- **Bağımlılıklar:** firmalar adres API
- **Kabul kriterleri:** Başka firma adresi IDOR yok

### [U-001] ADR-0010 PriceLock varsayımları (L-01…L-11)

- **Faz:** Karar
- **Durum:** Bekliyor (L-01…L-10 kod hazır; resmi ADR Kabul yok; L-11 Faz 4)
- **Konu:** PriceLock sözleşmesinin ürün sahibi tarafından Kabul edilmesi
- **Neden gerekli:** Faz 4 Order bağlama gate’i (G1)
- **Etkilenen:** PriceLock, Order (Faz 4)
- **Önerilen:** §6.1 madde tablosu (kodla uyumlu)
- **Onaylayacak:** Ürün sahibi

### [U-002] Stok ölçü birimleri ve tolerans

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Adet / gram / karat; tolerans bandı
- **Etkilenen:** Inventory, QC (Faz 4–6)
- **Seçenekler:** (A) teklif modeline göre birim (B) çoklu birim aynı balance
- **Önerilen:** A — model bazlı birincil birim
- **Onaylayacak:** Ürün sahibi + operasyon

### [U-003] KDV / vergi davranışı

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Vergi hesaplama, saklama, gösterim
- **Etkilenen:** Pricing, Order, Finance (B-06 erteli)
- **Seçenekler:** Proforma devam / KDV motoru / dış e-fatura
- **Önerilen:** Faz 4’te vergi yok (mevcut B-06); ayrı ADR
- **Onaylayacak:** Mali müşavir + ürün sahibi

### [U-004] İade / iptal finansal kuralları

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** İade tutarı, stok, mahsup
- **Etkilenen:** Faz 5–6
- **Seçenekler:** Tam iade / kısmi / stok-only iptal
- **Önerilen:** Yok — uzman
- **Onaylayacak:** Finans + hukuk

### [U-005] Cari hesap ve muhasebe politikası

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Cari bakiyenin ticari anlamı; kapanış
- **Etkilenen:** Faz 5
- **Seçenekler:** Basit cari / tam muhasebe entegrasyonu
- **Önerilen:** Basit cari v1 + ERP sonra
- **Onaylayacak:** Mali müşavir

### [U-006] Tedarikçi ödeme vadesi ve hak ediş

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Ne zaman / nasıl hak ediş
- **Etkilenen:** Faz 5
- **Seçenekler:** Teslim sonrası N gün / QC pass / peşin
- **Önerilen:** Yok
- **Onaylayacak:** Ürün sahibi + finans

### [U-007] Platform komisyonu / servis bedeli (B-01)

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Görünür/gizli hizmet payı
- **Etkilenen:** Pricing, Finance, hukuk
- **Seçenekler:** Kodlama yok / görünür satır / gizli yedirme
- **Önerilen:** Hukuk öncesi **kodlama yok** (mevcut)
- **Onaylayacak:** Hukuk + ürün sahibi

### [U-008] Konsinye / emanet mülkiyet ve sorumluluk

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Stok mülkiyeti, risk
- **Etkilenen:** Inventory, Shipping
- **Seçenekler:** Yalnız platform deposu / tedarikçi konsinye
- **Önerilen:** Faz 4’te konsinye yok; sonra
- **Onaylayacak:** Hukuk + operasyon

### [U-009] Metal/kur ticari referans ve TRY dışı yuvarlama

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Referans fiyat; quantize
- **Etkilenen:** Pricing, Finance
- **Seçenekler:** Mevcut 0.01 HALF_UP geçici / PB bazlı
- **Önerilen:** Muhasebe doğrulaması sonrası
- **Onaylayacak:** Finans

### [U-010] Hukuki belge ve sözleşme gereklilikleri

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Proforma, sipariş formu, mesafeli satış vb.
- **Etkilenen:** Checkout, Document
- **Seçenekler:** —
- **Önerilen:** Yok
- **Onaylayacak:** Hukuk

### [U-011] Alıcı fiyat kırılımı görünürlüğü (B-02 genişleme)

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Satır kırılımı hukuk onayı
- **Etkilenen:** Pricing UI/API
- **Seçenekler:** Toplam only (mevcut) / kısmi kırılım
- **Önerilen:** Mevcut A
- **Onaylayacak:** Hukuk

### [U-012] Faz 4 HTTP yüzeyi: yalnız servis+admin mi, PRE-API zorunlu mu?

- **Faz:** Karar
- **Durum:** Bekliyor
- **Konu:** Cart/Order için erken DRF
- **Etkilenen:** PRE, Faz 4
- **Seçenekler:** (A) PRE zorunlu (B) önce service+admin test
- **Önerilen:** A — ince PRE
- **Onaylayacak:** Ürün sahibi / teknik sponsor

---

## 11. Ürün sahibi karar bekleyen konular

§10’daki **U-001…U-012** özeti. Agent bu tabloyu Kabul etmez.

| ID | Konu | Neden | Domain/Faz | Onay | Durum |
|----|------|-------|------------|------|-------|
| U-001 | ADR-0010 resmi Kabul | G1; L-01…L-10 kodlu, L-11 Faz 4 | PriceLock / F4 | Ürün sahibi | Bekliyor |
| U-002 | Stok birimleri/tolerans | Ledger şema | Inventory / F4–6 | Ürün+ops | Bekliyor |
| U-003 | KDV/vergi | Toplamlar | Pricing/Finance | Mali müşavir | Bekliyor |
| U-004 | İade/iptal finans | Return | F5–6 | Finans+hukuk | Bekliyor |
| U-005 | Cari/muhasebe | Finance | F5 | Mali müşavir | Bekliyor |
| U-006 | Hak ediş/vade | Settlement | F5 | Ürün+finans | Bekliyor |
| U-007 | B-01 servis payı | Pricing line | Pricing | Hukuk | Bekliyor |
| U-008 | Konsinye/emanet | WH ownership | Inventory | Hukuk+ops | Bekliyor |
| U-009 | Kur referans / TRY dışı quantize | ADR-0008 §6 | Pricing | Finans | Bekliyor |
| U-010 | Hukuki belgeler | Checkout metin | Document | Hukuk | Bekliyor |
| U-011 | B-02 kırılım genişleme | buyer_quote | Pricing | Hukuk | Bekliyor |
| U-012 | PRE-API vs admin-only F4 | G4 | PRE/F4 | Teknik sponsor | Bekliyor |

Ayrıca açık: B-01, B-06 (ADR-0008 kayıtlı).

---

## 12. Güncel proje durumu ve sıradaki adım

| Madde | Değer |
|-------|--------|
| Faz | **3.7 kod tamam** (L-01…L-10); Faz 4 **başlamadı** |
| Son işlev | PriceLock + L-04 TTL DB guard + L-07/L-10 RBAC/audit |
| Test | PriceLock 34 OK · suite 288 OK |
| Migration | `fiyatlama.0010` … `0012` |
| ADR-0010 | **Taslak** — resmi ürün Kabul bekliyor |
| Bekleyen U-* | U-001…U-012 |
| Doküman | Yalnız `docs/KUYUMBANK_MASTER.md` (+ `AGENTS.md`, skills, `backend/README.md`) |
| Sıradaki iş | (1) ADR-0010 ürün Kabul (U-001) (2) Faz 4 ADR taslağı F4-001 (3) U-012 — **açık talimat + Kabul olmadan Faz 4 kodu yok** |
| Gate | G1 ADR-0010 Kabul · G2 Faz4 ADR Kabul · G3 U-002/U-008 · G4 U-012 |

### Docs sadeleştirme (2026-11-08)

Kaldırıldı: `docs/analysis/`, `docs/architecture/`, `docs/decisions/`, kök handoff/faz raporları. Bilgi bu master’dadır.

---

*Son güncelleme: 2026-11-08 — Dilim 3.7 + docs tek kaynak.*
