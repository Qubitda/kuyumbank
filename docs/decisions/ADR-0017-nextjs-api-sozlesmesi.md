# ADR-0017 — Next.js tüketici + `/api/v1/` uyumluluk sözleşmesi

**Durum:** **Taslak** (ADR bütünü henüz Kabul değil — agent Kabul etmez)
**Bağımlılık:** ADR-0002/0003/0004 **Kabul**; PRE/F7; [ADR-0016](ADR-0016-faz9-frontend.md) **Supersede**
**Kod:** API-B1…B7 **Kabul** (ürün sahibi Qubit, 2026-11-09); ADR bütünü hâlâ **Taslak** (NX-3…12 açık)

## Sabit ürün yönü

| Konu | Karar |
|------|-------|
| Yeni Django HTML | **Yok** |
| Mevcut `/buyer/`, `/ops/` | **Korunur** |
| Yeni ürün UI | **Next.js** (`frontend/` B7 sonrası) |
| Backend | Mevcut servisleri güvenli REST ile sunmak |
| Deploy | Aynı-origin reverse proxy tercih |

## Madde durumları

| ID | Konu | Durum | Karar |
|----|------|-------|-------|
| **NX-1** | Kimlik | **Kabul** (Qubit, 2026-11-09) | Session; cookie HttpOnly + Secure (prod) + SameSite=Lax; CSRF zorunlu; tarayıcıda token yok; Token/Basic S2S |
| **NX-2** | Sayfalama | **Kabul** (Qubit, 2026-11-09) | `page` + `page_size` (ledger dahil); max page_size; deterministik sıra (`-pk`); tenant izolasyonu |
| **CORS** | Cross-origin | **Ertelendi** | Aynı-origin; ihtiyaç çıkarsa ayrı karar |
| NX-3 | Hata zarfı | Açık | B1’de uygulandı; ADR maddesi henüz Kabul değil |
| NX-4 | OpenAPI/drift | Açık | B1’de uygulandı |
| NX-5 | `/me` capabilities | Açık | B1’de uygulandı |
| NX-6 | Idempotency tüm yazmalar | Açık | Altyapı + kısmi uçlar; B2+ |
| NX-7 | Rol serializer ayrımı | Açık | B2 Buyer* |
| NX-8…12 | PriceLock alanları, allowed_actions, no-store, sürüm, katman | Açık | |

## Fazlar

Canlı B0–B7 tablosu **tek kaynak:** [MASTER §12.1b](../MASTER.md). Bu ADR’de kopya tutulmaz.

Özet (yalnız okuma kolaylığı; çelişide MASTER kazanır): B1…B7 **Kabul** — 2026-11-09 (Qubit).
