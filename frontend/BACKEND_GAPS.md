# Frontend → Backend boşlukları (FAZ 3)

OpenAPI kaynağı: `docs/api/openapi-v1.json`. Aşağıdakiler **HTTP yüzünde yok**; FE uydurma endpoint yazmaz.

---

## GAP-F3-01 — Canlı borsa / piyasa panosu — **UYGULANDI** (2026-11-12)

| | |
|--|--|
| **İhtiyaç** | Portalda canlı (veya LKG) metal/kur panosu; alıcıya yalnızca görüntü |
| **Uygulama** | `GET /api/v1/piyasa/pano/?olcek=ONS\|KG\|GRAM` — `PiyasaPanoView` + `present_buyer_pano` |
| **Yanıt** | `{ "server_now", "olcek", "satirlar": [{ "kod", "ad", "fiyat", "para_birimi", "olcek", "kaynak", "guncelleme", "banner" }] }` |
| **Yasak** | `alis_marj`, `satis_marj`, `marj_modu`, detay/saf kur |
| **Ekran** | Header `PiyasaPanoStrip` |
| **Kanıt** | `api.tests.test_piyasa_pano_f301` |

---

## GAP-F3-02 — Global kâr marjı (admin/ops)

| | |
|--|--|
| **İhtiyaç** | Ops/admin için global marj politikası okuma/yazma |
| **Önerilen endpoint** | `GET/PATCH /api/v1/ops/piyasa/marj-politikasi/` |
| **İstek** | `{ "marj_orani": "0.085", "aktif": true }` (string Decimal) |
| **Yanıt** | Politika DTO + `server_now` |
| **Ekran** | Ops ayarlar / fiyatlama admin paneli |
| **Not** | `PiyasaMarjPolitikasi` model var; API yok. Alıcıya **asla** marj kırılımı dönülmemeli |

---

## GAP-F3-03 — İşçilik (gr) + has hesabı (alıcı net) — **UYGULANDI** (2026-11-12)

| | |
|--|--|
| **İhtiyaç** | Quote yanıtında işçilik/has; alıcı yalnız **net** görür |
| **Uygulama** | `BuyerQuote` + `net_ozet`: `iscilik_vergisiz` (ISCILIK satır tutarı), `has_gram` (gram×katalog milyem) |
| **Yanıt (alıcı)** | mevcut net alanlar + `iscilik_vergisiz` / `has_gram` / `net_ozet` — maliyet/marj/tedarikçi/satır listesi **yok** |
| **Yanıt (yasak)** | `maliyet`, `marj`, `tedarikci_*`, ham `iscilik`, `kanal_marj` |
| **Ekran** | `BuyerNetPriceCard` |
| **Kanıt** | `fiyatlama.tests.test_faz3_6_kor_havuz_k011.Faz36KorHavuzK011Tests.test_buyer_net_ozet_iscilik_and_has` |

---

## GAP-F3-04 — Tedarikçi föy CSV içe aktarma — **UYGULANDI** (2026-11-12; PDF sonra)

| | |
|--|--|
| **İhtiyaç** | Yükleme → önizleme → hatalı satır → commit (taslak teklifler) |
| **Uygulama** | `POST /supplier/offers/import/preview/` + `…/commit/` (`teklif_import_servisi`) |
| **Preview** | multipart `file` **veya** JSON `{csv}`; PDF → 400 |
| **Commit** | `{ "satirlar": [...] }` — hepsi geçerliyse atomic taslak; aksi yazma yok |
| **CSV** | `fiyat_modeli` + (`varyant_id`\|`sku`); opsiyonel gram/birim_fiyat/iscilik_override/… |
| **Ekran** | Teklifler sekmesi föy paneli |
| **Kanıt** | `api.tests.test_supplier_offer_import_f304` |

---

## GAP-F3-05 — Özel üretim: montür/taş katalog + üretim siparişi SM

| | |
|--|--|
| **İhtiyaç** | Montür seç → taş seç → üretim siparişi → durum takibi (ayrı state machine) |
| **Önerilen** | `GET /api/v1/catalog/monturler/`, `GET /api/v1/catalog/taslar/` + RFQ line alanları `montur_varyant_id`, `tas_specs[]` **veya** üretim order tipi |
| **Mevcut** | `POST /rfqs/` `talep_tipi=OZEL_URETIM`; line: `varyant_id?`, `miktar`, `aciklama`, `birim` |
| **Ekran** | Teklifler → Özel taleplerim (şu an aciklama’ya kodlanmış metin) |
| **Not** | `hedef_ayar` / `hedef_gram` OpenAPI create şemasında **yok**; FE bunları `aciklama` içine yazar |

---

## GAP-F3-06 — RFQ ↔ tedarikçi teklif bağlama

| | |
|--|--|
| **İhtiyaç** | Tedarikçi teklifini belirli RFQ satırına bağlama |
| **Önerilen** | `POST /supplier/offers/` body’ye `rfq_id` / `rfq_line_id` |
| **Mevcut** | Offer create yalnız `varyant_id` + fiyat alanları; RFQ ayrı kör havuz listesi |
| **Ekran** | Teklif hazırla modalı |

---

---

# FAZ 4 — Finans / Stok / Lojistik / Kalite

## GAP-F4-01 — Sevkiyat taşıyıcı alanı

| | |
|--|--|
| **İhtiyaç** | Dispatch’te taşıyıcı firma (`tasiyici`) + OpsShipment yanıtında gösterme |
| **Önerilen** | `TakipNoRequest` / `OpsShipment`’e `tasiyici?: string` |
| **Mevcut** | `POST .../dispatch/` yalnız `TakipNoRequest.takip_no` |
| **Ekran** | Lojistik sevk modalı |

## GAP-F4-02 — QC ölçüm: ayar + gram ayrı alan

| | |
|--|--|
| **İhtiyaç** | Ölçülen ayar ve gram ayrı Decimal alanlar |
| **Önerilen** | `OpsMeasurementRequest`: `olculen_ayar`, `olculen_gram` (string) **veya** yapılandırılmış `olculen` |
| **Mevcut** | `{ order_line_id, olculen, override_gerekce? }` — tek string |
| **Ekran** | Kalite ölçüm modalı (FE `olculen`’e `ayar=…;gram=…` yazar)

## GAP-F4-03 — Depo listesi (warehouse picker)

| | |
|--|--|
| **İhtiyaç** | Stok düzeltmede depo seçimi (id ezberletmeden) |
| **Önerilen** | `GET /api/v1/supplier/warehouses/` → `{ id, ad, kod }` |
| **Mevcut** | Adjust body’de ham `warehouse_id` |
| **Ekran** | Stok düzeltme formu |

## GAP-F4-04 — İade sebep / mahsup tutarı yüzeyi

| | |
|--|--|
| **İhtiyaç** | BuyerReturn’de `sebep`, `mahsup_tutari` (string Decimal) |
| **Önerilen** | OpenAPI `BuyerReturn` genişletmesi |
| **Mevcut** | `id`, `durum`, `order_id?`, `allowed_actions?`, `server_now?` |
| **Ekran** | Lojistik iade tablosu |

## GAP-F4-05 — Alıcı sevkiyat / POD self-service

| | |
|--|--|
| **İhtiyaç** | Alıcı kendi `/shipments/` listesinde takip + POD onayı |
| **Önerilen** | Mevcut `GET /shipments/` yeterli; POD alıcı path’i netleştir |
| **Mevcut** | POD yalnız `POST /ops/shipments/{id}/pod/` |
| **Ekran** | Alıcı sipariş/lojistik (ops ekranı ayrı)

---

---

# FAZ 5 — Org / Tanımlar / Belgeler / Profil / Dashboard / Raporlar

## GAP-F5-01 — Merkezi belge kasası

| | |
|--|--|
| **İhtiyaç** | Tek `GET /documents/` (tip, ref, dosya URL, tenant) |
| **Önerilen** | `GET /api/v1/documents/?tip=&order_id=` |
| **Mevcut** | FE sevkiyat/sipariş/ledger/iade/QC aggregate (composite) |
| **Ekran** | Belgeler |

## GAP-F5-02 — Tanım CRUD (fiyat grubu / ayar / kur)

| | |
|--|--|
| **İhtiyaç** | Ops tanımlar: fiyat grubu, ayar-milyem, metal/döviz kuru okuma-yazma |
| **Önerilen** | `GET/POST /api/v1/ops/definitions/{kaynak}/` |
| **Mevcut** | Yalnız `GET /sales-channels/` (read-only) |
| **Ekran** | Tanımlar |

## GAP-F5-03 — Firma listesi (tenant dışı)

| | |
|--|--|
| **İhtiyaç** | Platform ops için firma arama (kör havuz dışı, yetkili) |
| **Önerilen** | `GET /api/v1/ops/firmalar/?q=` |
| **Mevcut** | Görünür firma yalnız `/me/` |
| **Ekran** | Firmalar (ops) |

---

*Güncelleme: 2026-11-12 — FAZ 3–5 gaps*
