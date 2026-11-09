# ADR-0013 — Faz 6 QC + lojistik paket (tolerans, inspection, shipment sınırı)

**Durum:** **Kabul** (ürün sahibi Qubit/Emre, 2026-11-09)
**Bağımlılık:** F4-050 Order UYGULANDI; U-002 (birim Kabul A); U-008 (konsinye F4 dışı); ADR-0003-add (Quality/Logistics `view_all` yok)
**Kod:** Kabul tasarım sınırları bağlar; her dilim (F6-010…) ayrı uygulama + test. Bu mesajda F6-010 açık talimat.

> F6-001 kartı. Amaç: gram/adet QC ve sevkiyat kapısı için bağlayıcı sınırlar.

## Amaç

Sipariş sonrası kalite kontrolü (ölçüm + tolerans) ve QC PASS olmadan sevkiyatın açılamaması.  
Kör havuz ve Decimal kuralları bozulmaz.

## Kapsam dışı (bu ADR)

- Konsinye/emanet mülkiyet (U-008) — v1 yalnız sahipli depo/stok yolu
- İade/uyuşmazlık finansı (F6-030) — U-004 Kabul: v1 stok-only; ödeme iadesi yok (2026-11-09)
- Gerçek kargo provider / Celery (F6-021 fake port; F8)
- B-01 / B-06
- Account Hierarchy (F10)

## Kabul kararları (F6-K1…K12)

| ID | Karar |
|----|--------|
| F6-K1 | Paketler (ADR-0004): app **`kalite`** (QualityInspection + ölçüm); app **`lojistik`** (Shipment + POD + carrier port — F6-020+). |
| F6-K2 | **Beklenen gram:** GRAM satırında OrderLine → PriceLock → quote `gram`; ADET satırında adet sayımı. Dönüşüm yok (U-002). |
| F6-K3 | **Tolerans:** bağıl ±% (`QC_GRAM_TOLERANCE_PCT`) + isteğe bağlı mutlak taban (`QC_GRAM_TOLERANCE_ABS`). Float yasak. |
| F6-K4 | Tolerans dışı → otomatik FAIL (F6-011); override yalnız `manage_qc_override` + gerekçe ≥10 + audit. |
| F6-K5 | SM: `TASLAK → OLCUMDE → PASS \| FAIL` (veya `IPTAL`); yalnız `kalite.services`; her geçiş audit. |
| F6-K6 | Shipment create: siparişte PASS yoksa veya FAIL/`shipment_blok` varsa `ValidationError` (F6-020). |
| F6-K7 | Kör havuz: alıcıya tedarikçi/maliyet yok; tedarikçi kendi warehouse. |
| F6-K8 | `PLATFORM_QUALITY` / `PLATFORM_LOGISTICS` dar perm; **`view_all_tenants` yok**. |
| F6-K9 | Ölçüm append-ish; sessiz UPDATE yok; Decimal. |
| F6-K10 | Taş sertifika metadata + tenant belge (F6-012); storage ayrı. |
| F6-K11 | Carrier Port + Fake; fail-closed; secret yok. |
| F6-K12 | Return/Dispute bu ADR dışı (U-004). |

## Açık sorular — Kabul cevapları (2026-11-09)

| # | Soru | Cevap |
|---|------|--------|
| 1 | Tolerans tipi | **İkisi:** bağıl ±% + isteğe bağlı mutlak taban (F6-K3) |
| 2 | QC birimi | **Sipariş bazlı v1**; `order_line` nullable rezerv (satır sıkılaştırma F6-011+) |
| 3 | PASS sonrası rework | Yeni inspection açılır; eski PASS tarihsel; sessiz geri alma yok |
| 4 | POD | **Opsiyonel** (F6-022 politika) |

## Uygulama sırası

1. F6-001 / bu ADR **Kabul** ← yapıldı  
2. **F6-010** QualityInspection + SM + perm seed ← sıradaki  
3. F6-011 ölçüm + tolerans motoru  
4. F6-020 Shipment + QC gate (`lojistik` app)  
5. F6-021…023 → F6-012 → F6-030/031 (U-004) **UYGULANDI**

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-09) |
| F6-K1…K12 | **Onay** |
| Açık sorular 1–4 | **Cevaplandı** (yukarı) |
| Kod / migration | Dilim dilim (F6-010 bu tur) |

## İlişkili

- BACKLOG: F6-001…032; U-002; U-008; U-004
- ROADMAP §4 Faz 6; MASTER §12.3
