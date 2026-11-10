# ADR-0024 — Pano/MANUEL → PriceQuote bağlama (ADR-0020 PP-9)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “ok kalan işten devam et”)  
**Bağımlılık:** ADR-0020 PP-9; ADR-0014 KS-6 `hedef_toplam`; ADR-0022  
**Kapsam ID:** CAP-PANO-PP9 — [MASTER](../MASTER.md) §12.3

## Amaç

İç işlemde `cozumle_islem_birim_fiyati(PANO|MANUEL)` çıktısını ticari **PriceQuote**’a bağlamak; OrderLine snapshot lock üzerinden (L-11) gelir. Buyer self-service değil.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| PQ-1 | Servis: `piyasa.services.quote_baglama.quote_from_islem_fiyati`. |
| PQ-2 | `etkin_birim × gram` → `pricing_service.quote(..., hedef_toplam=)` (KS-6). |
| PQ-3 | Yetki: platform + (`manage_piyasa` ∨ `manage_sozlesme`). |
| PQ-4 | `hesap_girdisi` ek: `birim_kaynak`, `piyasa_urun_kod`, `taraf`, `baz_birim`, `etkin_birim`, `feed_*`. |
| PQ-5 | HTTP/OpenAPI bu dilimde **yok** (servis + test). |
| PQ-6 | Mevcut buyer quote yolu değişmez; `hedef_toplam` yoksa davranış aynı. |

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10) |
| Kod + test | Bu dilim |
| HTTP | Yok |

## İlişkili

- [ADR-0020](ADR-0020-piyasa-panosu-baz-fiyat.md) · [ADR-0014](ADR-0014-karlilik-simulasyonu.md)
