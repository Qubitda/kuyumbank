# ADR-0023 — İade mahsup HTTP (OL-8 açılımı)

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — “diğer fazlara geç” → MASTER §12 Mahsup HTTP)  
**Bağımlılık:** ADR-0019 OL-8 (mahsup HTTP bu ADR ile **açılır**); F5-023 `mahsup_servisi`; API-B3 returns  
**Kapsam ID:** CAP-MAHSUP-HTTP — [BACKLOG](../BACKLOG.md) · [MASTER](../MASTER.md) §12

## Amaç

`mahsup_servisi.iade_mahsup` için REST yüzeyi. U-004: **ödeme iadesi yok**; yalnız cari ALACAK mahsup.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| MH-1 | `POST /api/v1/returns/{id}/mahsup/` — ONAYLANDI iade; idempotent; `finans.post_ledger` zorunlu. |
| MH-2 | `POST /api/v1/returns/{id}/approve/` gövde: isteğe `{"mahsup": true}` → `return_servisi.onayla(..., mahsup=True)` (actor’da `post_ledger` yoksa 403; onay geri alınır). |
| MH-3 | Buyer yüzeyi mahsup yazmaz; ops/finance. Tenant: mevcut return scope + `view_all_tenants`. |
| MH-4 | Presenter: `finans_mahsup_yapildi`; `allowed_actions` += `mahsup` (ONAYLANDI ∧ ¬mahsup ∧ `post_ledger`). |
| MH-5 | Rapor HTTP (OL-7) **hâlâ kapalı**. Ödeme iadesi endpoint **yok**. |
| MH-6 | OpenAPI + odaklı test; FE yok. |

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** (2026-11-10) |
| Kod + OpenAPI + test | Bu dilim |

## İlişkili

- [ADR-0019](ADR-0019-object-level-drf.md) OL-8 · F5-023 · `test_mahsup_f5_023`
