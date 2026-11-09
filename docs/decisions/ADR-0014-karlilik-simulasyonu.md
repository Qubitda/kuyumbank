# ADR-0014 — İç karlılık simülatörü (Excel A/B; ticari quote dışı)

**Durum:** **Kabul** (ürün sahibi Qubit, 2026-11-09)
**Bağımlılık:** ADR-0008 fiyat motoru UYGULANDI; B-01 / B-06 ayrı politika
**Kod:** `fiyatlama.services.karlilik_simulasyonu` — saf Decimal yardımcı; migration yok

## Amaç

Perakende Excel (maden + işçilik → gr maliyet → marj veya hedef toplam → banka/işletme/GV → net kar) hesabını **iç karar desteği** olarak sunmak.  
**PriceQuote / PriceLock / OrderLine ticari gerçeğini bu ADR tek başına değiştirmez**; quote bağlama ayrı uygulama dilimi + talimat.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| KS-1 | Simülatör `fiyatlama.services` altında; HTTP/admin zorunlu değil (v1). |
| KS-2 | Mod A `MARJ_PCT`: gr_satis = gr_maliyet × (1+kar%). |
| KS-3 | Mod B `HEDEF_TOPLAM`: hedef / gram → gr_satis; örtük kar türetilir. |
| KS-4 | Banka / işletme / GV yalnız simülasyon çıktısı; ledger/cari/PI yazmaz. |
| KS-5 | B-06 KDV ve B-01 platform pay bu ADR’de yok. |
| KS-6 | Quote’a “hedef toplam” fiyat modeli **izinli tasarım**; uygulama ayrı dilim + açık talimat. |

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-09, Qubit) |
| Kod (saf sim) | UYGULANDI |
| Quote entegrasyonu | PLANLANDI (KS-6; talimat sonrası) |

## İlişkili

- MASTER §12; BACKLOG
- Test: `fiyatlama.tests.test_karlilik_simulasyonu`
