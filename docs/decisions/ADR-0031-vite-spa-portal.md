# ADR-0031 — Vite SPA portal (Next App Router yerine)

**Durum:** **Kabul** (ürün sahibi Qubit, 2026-11-12 — “2 ile devam et / son karar”)  
**Bağımlılık:** [ADR-0017](ADR-0017-nextjs-api-sozlesmesi.md) API sözleşmesi (NX-1…12) **korunur**; UI runtime bu ADR ile netleşir  
**İlişki:** ADR-0017’deki “Yeni ürün UI = Next.js” satırı bu ADR ile **supersede** (yalnız UI runtime; `/api/v1` kuralları aynı)

## Bağlam

`side/frontend-removed` üzerinde Vite + React SPA üretildi; `next/link` / `next/navigation` shim’leri ve `App.tsx` switch router hedef mimariden saptı. B2B portal oturumlu; SSR/RSC getirisi düşük.

## Karar

| Konu | Karar |
|------|-------|
| FE runtime | **Vite + React + TypeScript SPA** (`frontend/`) |
| Routing | **React Router** (dinamik segment + 404); Next shim **yasak** |
| Veri | **TanStack Query** altyapısı; ham `useEffect` yeni dilimlerde tercih edilmez |
| Hata | **ErrorBoundary**; Next `error.tsx` / `loading.tsx` kullanılmaz |
| Auth / API | ADR-0017 NX-1…12: session+CSRF, same-origin `/api` proxy → Django |
| AI Studio | `GEMINI_*`, `metadata.json`, `DISABLE_HMR` **yok** |
| Next dönüş | Yalnız yeni ADR + açık SSR/SEO ihtiyacı ile |

## Sonuçlar

- Portal dilimleri Vite üzerinde OpenAPI’ye bağlanır.
- MASTER / FRONTEND_ARCHITECTURE Next App Router varsayımını Vite SPA olarak günceller.
- ADR-0017 API maddeleri geçerlidir; “Next.js UI” iddiası bu ADR’dir.
