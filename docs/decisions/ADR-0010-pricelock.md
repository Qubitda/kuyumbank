# ADR-0010 — PriceLock (L-01…L-11)

**Durum:** **Kabul** (ürün sahibi, 2026-11-08)
**Uygulama:** L-01…L-11 UYGULANDI (L-11 = F4-051 `OrderLine.price_lock`)
**Kanıt:** migration `fiyatlama.0010–0012` + `siparis.0003`; `test_price_lock.py` + `test_order_f4_050.py`

> Bu dosya master §6.1'den taşındı (2026-11-09).

L-01…L-11 kodda **UYGULANDI** (L-11 = F4-051 `OrderLine.price_lock`).

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
| L-11 | UYGULANDI | `OrderLine.price_lock` OneToOne + satır snapshot; immutable (F4-051; `siparis.0003`) |

**Açık ürün notu (matris):** `PLATFORM_FINANCE` on-behalf opt-in şimdilik **yok**. `ALICI_YONETICI` / `ALICI_ONAYLAYICI` `lock_quote` almaz.

## Kapanış

**Kabul (ürün sahibi 2026-11-08):** L-01…L-10; L-11 → Faz 4 (**uygulandı** F4-051).  
**Kanıt:** mig `fiyatlama.0010–0012` + `siparis.0003`; `test_price_lock.py` + `test_order_f4_050.py`.
