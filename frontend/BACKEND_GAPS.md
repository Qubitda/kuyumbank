# Frontend → Backend boşlukları (FAZ 3)

OpenAPI kaynağı: `docs/api/openapi-v1.json`. Aşağıdakiler **HTTP yüzünde yok**; FE uydurma endpoint yazmaz.

---

## GAP-F3-01 — Canlı borsa / piyasa panosu

| | |
|--|--|
| **İhtiyaç** | Portalda canlı (veya LKG) metal/kur panosu; alıcıya yalnızca görüntü |
| **Önerilen endpoint** | `GET /api/v1/piyasa/pano/` (tenant: authenticated; alanlar maskeli) |
| **İstek** | — (query: `olcek=ONS\|KG` opsiyonel) |
| **Yanıt örneği** | `{ "server_now": "...", "satirlar": [{ "kod": "AU24", "fiyat": "3125.50", "para_birimi": "TRY", "kaynak": "LKG", "guncelleme": "..." }] }` |
| **Ekran** | Header/dashboard borsa şeridi; fiyatlama bağlamı |
| **Not** | Django `piyasa` app + Admin var; `/api/v1` path yok |

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

## GAP-F3-03 — İşçilik (gr) + has hesabı (alıcı net)

| | |
|--|--|
| **İhtiyaç** | Quote yanıtında veya ayrı hesap API’sinde işçilik/has kırılımı; alıcı yalnız **net** görür |
| **Önerilen** | Mevcut `POST /quotes/` yanıtına opsiyonel `net_ozet` **veya** `POST /api/v1/quotes/preview/` |
| **Yanıt (alıcı)** | `{ "toplam_vergisiz": "...", "gram": "...", "gram_basi_vergisiz": "..." }` — maliyet/marj/tedarikçi **yok** |
| **Yanıt (yasak)** | `maliyet`, `marj`, `tedarikci_*`, iç işçilik kırılımı |
| **Ekran** | Katalog quote kartı; fiyatlama |
| **Not** | Bugün `BuyerQuote` net alanları var; işçilik/has ayrı satır olarak yok. Tedarikçi `iscilik_override` offer create’te var |

---

## GAP-F3-04 — Tedarikçi föy PDF/CSV içe aktarma

| | |
|--|--|
| **İhtiyaç** | Yükleme → önizleme → hatalı satır düzeltme → onay (teklif taslakları) |
| **Önerilen** | `POST /api/v1/supplier/offers/import/preview/` + `POST /api/v1/supplier/offers/import/commit/` |
| **İstek (preview)** | multipart `file` (csv/pdf) + `Idempotency-Key` |
| **Yanıt (preview)** | `{ "satirlar": [...], "hatalar": [{ "satir_no": 3, "hata": "..." }] }` |
| **İstek (commit)** | `{ "satirlar": [ { "varyant_id": 1, "fiyat_modeli": "GRAM", "birim_fiyat": "..." } ] }` |
| **Ekran** | Teklifler / tedarikçi portalı |
| **Not** | `bulk-orders` CSV alıcı siparişi içindir; teklif föyü değil |

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
