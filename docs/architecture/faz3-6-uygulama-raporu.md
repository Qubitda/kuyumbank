# Dilim 3.6 — Kör havuz + K-011

**Tarih:** 2026-11-08  
**ADR:** ADR-0008 **Kabul** §2.8 / B-02; kanonik K-011  
**Önkoşul checkpoint:** `b516893` (Dilim 3.4–3.5)  
**Kapsam dışı:** PriceLock (3.7), stok/sipariş (Faz 4), DRF (Faz 7), B-01/B-06.

## K-011 çözüm

| Model | Sorumluluk | Karar |
|-------|------------|-------|
| `urunler.UrunTasi` | Katalog / vitrin taş özelliği (ProductStone) | **Korundu** (isim aynı) |
| `fiyatlama.TeklifTasMaliyeti` | Teklif taş maliyet satırı (OfferStoneCost) | **Yeniden adlandırıldı** (`UrunTasi` → `TeklifTasMaliyeti`) |

- Birleştirme yok: alanlar, PB ve fiyat motoru kullanımı farklı.
- Quote taş bedeli yalnız `TeklifTasMaliyeti` (+ `related_name=taslar`); katalog `bedel` hesaba sızmaz.
- Migration: `fiyatlama.0008_faz3_6_k011_teklif_tas_maliyeti` (`RenameModel`).
- Geçici alias: `fiyatlama.models.UrunTasi = TeklifTasMaliyeti` (deprecated).

## Kör havuz / B-02

- `selectors/buyer_quote.py`: `get_quote_for_actor` / `get_buyer_quote_view` / `present_buyer_quote`
- Alıcı DTO: ürün bilgisi + `toplam_vergisiz` + PB + geçerlilik/durum + isteğe bağlı gram başı; **satır kırılımı yok**
- Kapsam dışı / tedarikçi → `BuyerQuoteNotFound` (404 semantiği; varlık sızdırılmaz)
- `PriceQuoteAdmin`: alıcıya yalnız güvenli alanlar; teklif/maliyet/kur/`hesap_girdisi`/inline gizli
- `TeklifTasMaliyeti`: alıcı queryset/modül yok; tedarikçi yalnız kendi teklifi

## Dosyalar

- `fiyatlama/models/teklif_tas_maliyeti.py` (+ `urun_tasi.py` kaldırıldı)
- `fiyatlama/migrations/0008_faz3_6_k011_teklif_tas_maliyeti.py`
- `fiyatlama/selectors/buyer_quote.py`, `tenant.py`, `admin/admin.py`
- `fiyatlama/tests/test_faz3_6_kor_havuz_k011.py`
