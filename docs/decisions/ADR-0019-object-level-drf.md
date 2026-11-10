# ADR-0019 — Object-level DRF (nesne RBAC matrisi)

**Durum:** **Kabul** (2026-11-10, ürün sahibi — OL-1…OL-11 **Öneri A**)  
**Bağımlılık:** ADR-0003 (+ view_all addendum) **Kabul**; API-B1…B7 **Kabul**; ADR-0017 NX madde **Kabul** (ADR bütünü Taslak)  
**Kod:** OL-11 dilimi — Permission + selector; yeni HTTP yok (rapor/mahsup kapalı)  
**Kapsam dışı:** FXQ / DYN / I18N / AI → [NOTE-PENDING-PRODUCT-DECISIONS](NOTE-PENDING-PRODUCT-DECISIONS.md)

## 1. Amaç

`/api/v1/` nesne erişim kurallarını rol × kaynak × işlem olarak dondurmak; IDOR / tenant / SoD testlenebilir Permission + selector.

## 2. Sabit güvenlik (S-1…S-6)

| ID | Kural |
|----|--------|
| S-1 | Client `firma_id` / `alici_firma_id` / `tedarikci_id` yok sayılır |
| S-2 | Çapraz tenant → **404** |
| S-3 | Kör havuz |
| S-4 | capabilities ≠ güvenlik |
| S-5 | Alıcı yazma ≠ ops yazma yüzeyi |
| S-6 | Deny durable audit (servis örnekleri) |

## 3. Matris (bağlayıcı — Öneri A)

Commerce **W**: `ALICI_YONETICI` + `ALICI_SATINALMACI`.  
Commerce **R** (W yok): `ALICI_ONAYLAYICI`, `ALICI_DENETCI`, `ALICI_FINANS`.  
Ops order iptal HTTP: **yok**. SUPPORT tenant R: **yok**. Rapor/Mahsup HTTP: **yok**.

## 4. OL kararları (Kabul)

| ID | Seçim | Özet |
|----|-------|------|
| OL-1 | **A** | Permission + selector |
| OL-2 | **A** | Ops iptal HTTP kapalı |
| OL-3 | **A** | Denetçi yalnız GET |
| OL-4 | **A** | Onaylayıcı commerce W yok |
| OL-5 | **A** | SUPPORT R yok |
| OL-6 | **A** | Supplier RFQ havuzu B6 |
| OL-7 | **A** | Rapor HTTP bu ADR dışı |
| OL-8 | **A** | Mahsup HTTP bu ADR dışı |
| OL-9 | **A** | Çapraz tenant 404 |
| OL-10 | **A** | Yeni object perm yok |
| OL-11 | **A** | Permission + Order/Cart/Quote IDOR test; yeni uç yok |

## 5. Onay özeti

| ID | Seçim | İmza / tarih |
|----|-------|--------------|
| OL-1…OL-11 | **A** (tümü) | Ürün sahibi **Kabul** 2026-11-10 |

**ADR bütünü:** **Kabul** (2026-11-10).

## 6. Uygulama (OL-11)

- `api.permissions`: `IsBuyerCommerceRead` / `IsBuyerCommerceWrite` / `Has*ObjectAccess`
- Buyer commerce yazma view’leri write permission
- Detay: selector + `check_object_permissions`
- Test: `api.tests.test_object_level_adr0019`

## 7. İlişkiler

- [NOTE-PENDING](NOTE-PENDING-PRODUCT-DECISIONS.md) · BACKLOG `[SEC-OBJECT-DRF]` · MASTER §12.3
