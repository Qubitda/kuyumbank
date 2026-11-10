# ADR-0018 — CAP-PIYASA: Kur dayanıklılığı, kaynak merdiveni, batch, risk guardrail

**Durum:** **Kabul** (2026-11-10, ürün sahibi — açık uygulama talimatı)
**Bağımlılık:** ADR-0008 (kur/quote; B-04 yeniden tanım bu ADR ile), ADR-0010 (PriceLock), ADR-0003 (RBAC)
**Kapsam ID:** CAP-PIYASA — [BACKLOG](../BACKLOG.md) · [MASTER](../MASTER.md) §12.3
**Geçici referans:** kök `real_data/` (GoldXT örnek; **toptan port yok**; ürün sahibi sonra silebilir)

## Amaç

Kuyumculukta saniyelik kur + yüksek tutar + binlerce SKU için:

1. Canlı (Binance anlık) + resmi (TCMB EOD) çift katmanlı kur beslemesi
2. Hibrit kaynak: ürün / ayar / genel politika
3. Feed kopuşunda LKG + görünür uyarı; soft uydurma yok
4. Toplu canlı senkron ve manuel freeze (dry-run → atomik yayın)
5. Negatif marj, yuvarlama, çapraz kur sanity, geçmiş quote immutability

**Yeniden icat yok:** PriceLock = ADR-0010; `PriceQuote` immutability = ADR-0008 + PG trigger (`fiyatlama.0007`).

## B-04 ilişkisi

ADR-0008 B-04 (**Kabul**): tek aktif sağlayıcı; otomatik fallback yok; stale → hata; sessiz “son bilinen” yok.

Bu ADR B-04’ü şu kontrollü modele çeker (**Kabul** — yürürlükte):

- Tek **aktif anlık** sağlayıcı (Binance) kalır; soft provider hop yok.
- Stale’de **sessiz** LKG yasak; `feed_health=FEED_STALE_LKG` + banner ile son taze gözlem kullanılabilir.
- TCMB EOD / kriz `kaynak=manuel` snapshot = bilinçli düşüş; uydurma fiyat yok.
- Çapraz kur sanity aşımında yeni anlık aktif olmaz (LKG korunur).

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| CP-1 | **Precedence:** `Urun.fiyat_kaynagi` → `AyarMilyem.fiyat_kaynagi` → `KurPolitikasi.fiyat_kaynagi`. Enum: `CANLI_PIYASA` / `MANUEL_GIRIS` / (`MIRAS` yalnız ürün+ayar). |
| CP-2 | **Feed:** Binance anlık (`kaynak=api`) + TCMB EOD (`kaynak=tcmb`) + manuel dört göz; Decimal troy oz `31.1035`; float yasak. |
| CP-3 | **feed_health:** `FEED_OK` \| `FEED_STALE_LKG` \| `FEED_LOCKED_MANUEL` \| `FEED_FAIL`. LKG yalnız health yüzeyi ile; `0` fiyat yok. |
| CP-4 | **PriceLock:** satış/ödeme güvencesi ADR-0010; CAP-PIYASA yeni lock tablosu açmaz. |
| CP-5 | **Batch filtre:** Kategori (alt ağaç) / Ayar / Koleksiyon / id listesi. Tek tek sabitleme zorunlu değil. |
| CP-6 | **Canlı senkron batch:** dry-run (N, ortalama delta %, şok) → onay → publish; freeze kaldır + CANLI. |
| CP-7 | **Manuel freeze batch:** etkin fiyat → `Varyant.sabit_fiyat` mühür + `fiyat_tipi=sabit` + `fiyat_kaynagi=MANUEL`; fiyat uçurulmaz. |
| CP-8 | **Dry-run:** toplu yazım öncesi zorunlu önizleme; onaydan önce politika/ürün alanları yazılmaz. |
| CP-9 | **Şok eşiği:** `sok_esigi_yuzde` (varsayılan 5) — satır staging. |
| CP-10 | **Guardrail:** `toplam_vergisiz` maliyetin altında veya `min_marj_pct` altı → BLOKE; quote yok; batch satırı publish’e girmez. Maliyet = `ic_maliyet` / `maliyet_referans`. |
| CP-11 | **Yuvarlama:** ara kur/çarpım `0.000001` `ROUND_HALF_UP`; TRY ticari toplam + `sabit_fiyat` mühür `0.01` `ROUND_HALF_UP` (ADR-0008 TRY kuralı + U-009 ile uyumlu ara netleştirme). |
| CP-12 | **Çapraz kur sanity:** `XAUUSDT×USDTTRY` implied USDTRY vs TCMB USDTRY; `capraz_makas_esigi_yuzde` (varsayılan 2) aşımı → yeni anlık aktif olmaz; senkron publish red; otomatik serbest piyasa hop yok. |
| CP-13 | **Atomik publish:** tek `transaction.atomic()`; partial success yasak; aşırı büyük küme ayrı onaylı işlere bölünür (`max_batch_satir`). |
| CP-14 | **Immutability:** batch / kur politikası mevcut `PriceQuote` / `PriceLock` / `OrderLine` UPDATE etmez (trigger + app). |
| CP-15 | **Yetki:** `manage_kur`; `is_superuser` iş kısa yolu yok; kritik geçişler audit (+ fail durable). |
| CP-16 | **Celery yok;** sync management command + cron (RUNBOOK). |
| CP-17 | **`real_data/`:** yalnız geçici ürün/UX/feed referansı; Django’ya toptan kopyalanmaz; silinebilir. |

## Uygulama sırası (Kabul + açık talimat sonrası)

1. Model alanları: `fiyat_kaynagi`, `feed_health` yüzeyi, `kaynak=tcmb`, batch işlek/staging
2. `etkin_kaynak` + resolve kapıları (LKG, sanity, guardrail, quantize)
3. Binance + TCMB adaptör + sync komutları
4. Batch dry-run + atomic publish (senkron + freeze)
5. Odaklı PG testler + MASTER/BACKLOG/RUNBOOK

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Kabul** (2026-11-10) |
| Kod | Uygulama bu oturum |
| B-04 yürürlük güncellemesi | decisions README + ADR-0008 not |

## İlişkili

- [ADR-0008](ADR-0008-faz3b-kur-fiyatlama-quote.md) · [ADR-0010](ADR-0010-pricelock.md) · [ADR-0014](ADR-0014-karlilik-simulasyonu.md) (karlılık; quote gerçeği değil)
- BACKLOG `[CAP-PIYASA]` · MASTER §12.3
- Geçici: `real_data/README.md` (GoldXT)
