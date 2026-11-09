# Karar kayıtları (ADR) — indeks

**Kural:** ADR metni Kabul sonrası değişmez; değişiklik için yeni ADR (`Yerine geçen:` alanı). Agent bir ADR'yi kendi başına **Kabul etmez**.
**Canlı durum** bu tablodadır; ADR dosyalarının içindeki geçmiş "Taslak/öneri" ifadeleri arşiv anısıdır.

| ID | Konu | Karar (özet) | Durum | Faz | Domain | Uygulama | Kanıt |
|----|------|--------------|-------|-----|--------|----------|-------|
| [ADR-0001](ADR-0001-agent-standartlari.md) | Agent standartları | Skill yolu, faz sırası, kanıt etiketleri | **Kabul** | 0 | — | UYGULANDI (AGENTS) | AGENTS.md |
| [ADR-0002](ADR-0002-runtime-ve-bagimliliklar.md) | Runtime | Django 6.1 pin, PG, requirements disiplini | **Kabul** | 0 | Infra | UYGULANDI | requirements.txt |
| [ADR-0003](ADR-0003-faz1-kimlik-rbac.md) | Kimlik/RBAC | 8 platform rolü, firma NOT NULL, dağıtık perm, izolasyon | **Kabul** | 1 | Identity | UYGULANDI | firmalar app |
| [ADR-0003-add](ADR-0003-addendum-view-all-scope.md) | view_all scope | Quality/logistics/support’tan view_all çıkarıldı | **Kabul** | 1 | Identity | UYGULANDI | yetki matrisi |
| [ADR-0004](ADR-0004-modular-python-organizasyon.md) | Modüler paket | models/services/selectors/admin/tests | **Kabul** | 1+ | Tümü | UYGULANDI | paket ağacı |
| [ADR-0005](ADR-0005-katalog-platform-ownership.md) | Katalog ownership | Platform; olusturan_firma; K1–K6 | **Kabul** | 2 | Catalog | UYGULANDI | urunler |
| [ADR-0005-bekleyen](ADR-0005-bekleyen-kararlar.md) | K1–K6 bekleyen | KAPANDI → 0005’e taşındı | **Kapandı** | 2 | Catalog | — | tarihsel |
| [ADR-0006](ADR-0006-faz2-1-kararlar.md) | Faz 2.1 | B1–O6 (eşleştirme, onay kilidi, audit O3) | **Kabul** | 2.1 | Catalog/Teklif | UYGULANDI | testler |
| [ADR-0007](ADR-0007-faz3-fiyatlama.md) | Faz 3a | Teklif SM, versiyon swap, K-007/K-008 | **Kabul** | 3.1–3.2 | Supplier/Pricing | UYGULANDI | 0005–0006 mig |
| [ADR-0008](ADR-0008-faz3b-kur-fiyatlama-quote.md) | Faz 3b | Üç model, kur, quote, B-02…B-06, PriceLock tanımı | **Kabul** | 3.3–3.7 | Pricing | 3.3–3.7 kod | 0007–0012 |
| [ADR-0009](ADR-0009-admin-yuzey-sertlestirme.md) | Admin H1–H5 | Admin yüzey sertleştirme | **Kabul** | 3.1+ | Admin | UYGULANDI | admin tests |
| [ADR-0010](ADR-0010-pricelock.md) | PriceLock L-01…L-11 | Tek lock/quote; TTL=quote; L-07 perm; L-11 OrderLine | **Kabul** | 3.7+F4 | PriceLock+Order | L-01…L-11 UYGULANDI | 0010–0012; siparis.0003 |
| [ADR-0011](ADR-0011-faz4-ticari-cekirdek.md) | Faz 4 ticari çekirdek | Stok üçlüsü + cart/order + Lock→Order | **Kabul** | 4 | Inventory/Order | F4 dilim 1–8 + PRE-001…004 UYGULANDI | [ADR-0011](ADR-0011-faz4-ticari-cekirdek.md) |
| [ADR-0012](ADR-0012-medusa-p0-p1-paketi.md) | Medusa-türev P0/P1 (audit/FX/hedge/cari) | F5 paket sınırları F5-K1…K10 | **Kabul** (2026-11-09, Emre) | 5 | Audit/Finance | Tasarım Kabul; kod ayrı talimat | [ADR-0012](ADR-0012-medusa-p0-p1-paketi.md) |
| [ADR-0013](ADR-0013-faz6-qc-lojistik.md) | Faz 6 QC + lojistik | F6-K1…K12 tolerans/inspection/shipment gate | **Kabul** (2026-11-09) | 6 | Quality/Logistics | F6-010…023 + F6-012 UYGULANDI; F6-030 politika | [ADR-0013](ADR-0013-faz6-qc-lojistik.md) |
| [ADR-0014](ADR-0014-karlilik-simulasyonu.md) | İç karlılık sim (Excel A/B) | P&L sim + KS-6 hedef toplam (uygulama ayrı) | **Kabul** (2026-11-09, Qubit) | — | Pricing (yardımcı) | Sim UYGULANDI; quote dilimi PLANLANDI | `karlilik_simulasyonu` |
| B-01 | Servis payı | v1 kapalı (0); hukuk metni gelene kadar kalem yok | **Kabul** (2026-11-09, Qubit) | 3+ | Pricing | Kod yok (bilinçli) | ADR-0008 |
| B-02 | Alıcı görünürlük | Yalnız toplam (+ gram başı) | **Kabul** | 3.6 | Pricing | UYGULANDI | buyer_quote |
| B-03 | Quote TTL | Kanal bazlı; ≤ kur max gecikme | **Kabul** | 3.3–3.5 | Pricing | UYGULANDI | SatisKanali |
| B-04 | Kur sağlayıcı | Tek aktif; fallback yok | **Kabul** | 3.3 | Pricing | UYGULANDI | KurSaglayici |
| B-05 | Kur tipi | Alıcı/tedarikçi ayrı | **Kabul** | 3.3 | Pricing | UYGULANDI | KurPolitikasi |
| B-06 | Vergi | KDV yok / proforma devam | **Kabul** (2026-11-09, Qubit; erteli politika sabit) | 3 | Pricing | Bilinçli yok | ADR-0008 §2.9 |

### Çelişki / kapanmış drift

| Konu | Not |
|------|-----|
| G0–G2 | 3.7 commit + ADR-0010/0011 Kabul — kapandı |
| U-002 birim | Teklif `fiyat_modeli` → ADET/GRAM; **dönüşüm yok**; legacy alanlar ADET |
| Prosperer parity | Hedef kıyas; runtime DOĞRULANAMADI |

### Değişiklik kaydı

- 2026-11-09: ADR arşivi tek master dosyasından ayrı dosyalara taşındı; ADR-0001'e doküman düzeni değişiklik **önerisi** eklendi (U-016).
- 2026-11-09 (Emre): **U-016** → ADR-0001 doküman düzeni **Kabul**; **ADR-0012** Kabul (tasarım; kod ayrı talimat). U-003…007, 009…011, U-013…015 **Kabul** (Önerilen; dış onaylı kartlarda ürün sahibi override). B-01/B-06 dokunulmadı. Ayrıntı: [BACKLOG](../BACKLOG.md).
- 2026-11-09: **ADR-0013** Faz 6 QC/lojistik **Taslak** (F6-001); Kabul + talimat olmadan F6-010 kodu yok.
- 2026-11-09 (Qubit/Emre): **ADR-0013 Kabul** (soru cevapları kayıtlı); F6-010 `kalite` app UYGULANDI.
