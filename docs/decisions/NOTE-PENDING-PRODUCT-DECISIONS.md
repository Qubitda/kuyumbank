# NOTE — Bekleyen ürün / finans kararları (ADR-0019 dışı)

**Tarih:** 2026-11-10  
**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “go hepsini onaylıyorum”)  
**Ayır:** Object-level DRF → [ADR-0019](ADR-0019-object-level-drf.md); rapor HTTP → [ADR-0026](ADR-0026-rapor-http.md)

---

## FXQ — F12-011 TRY dışı yuvarlama (U-009)

| ID | Seçim | Durum |
|----|-------|--------|
| FXQ-1 | **A** — tüm PB `0.01` HALF_UP kalsın | **Kabul** |
| FXQ-2 | Ürün sahibi onayı (finans imza proxy) | **Kabul** |
| FXQ-3 | **A** — kayıtlar dokunulmaz | **Kabul** |

**Kapı:** FXQ-1=A → F12-011 kod **yok** (mevcut davranış).

---

## DYN — CAP-DYNPRICE (U-015)

| ID | Seçim | Durum |
|----|-------|--------|
| DYN-1 | **A** — kapalı kal | **Kabul** |
| DYN-2 | **A** — Quote/Lock/OrderLine immutable | **Kabul** |
| DYN-3 | — (DYN-1=A) | N/A |

**Kapı:** DYN-1=A → kod yok.

---

## I18N — F12-001

| ID | Seçim | Durum |
|----|-------|--------|
| I18N-1 | **A** — fiilen TR | **Kabul** |
| I18N-2 | — (TR only) | N/A |
| I18N-3 | **A** — katalog çeviri zorunlu değil | **Kabul** |
| I18N-4 | **A** — F12-010 sonra | **Kabul** (erteli) |

**Kapı:** TR-only → F12-010 kod şimdi yok.

---

## AI — F11-015

| ID | Seçim | Durum |
|----|-------|--------|
| AI-1 | **A** — yok (F10-021 skor yeter) | **Kabul** |
| AI-2 | **A** — kör havuz | **Kabul** |
| AI-3 | — | N/A |
| AI-4 | **A** — otomatik checkout/onay yasak | **Kabul** |

**Kapı:** AI-1=A → AI ajan kodu yok.
