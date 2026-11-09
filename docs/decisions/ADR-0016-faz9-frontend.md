# ADR-0016 — Faz 9 frontend teknolojisi (F9-001) — SUPERSEDE

**Durum:** **Supersede** (ürün sahibi Qubit, 2026-11-09) — yerine [ADR-0017](ADR-0017-nextjs-api-sozlesmesi.md)
**Önceki durum:** **Kabul** (2026-11-09, FE-1 C→A Django template v1)
**Bağımlılık (tarihsel):** PRE/F7 API; F4-062 `/buyer/`; ADR-0002/0004 **Kabul**

> Bu ADR artık bağlayıcı ürün kararı değildir. F9-010/011 Django HTML dilimleri **kodda kalır** (silinmez); yeni ürün yüzeyi ve API sözleşmesi → **ADR-0017**.

## Neden supersede

Ürün sahibi (2026-11-09): asıl tüketici **Next.js App Router + TypeScript** (ayrı `frontend/`); backend `/api/v1/` bu mimariye uyumlu hale getirilecek. Yeni Django HTML ürün UI’sı açılmayacak. Mevcut `/buyer/`, `/ops/` şablonları kalır.

## Tarihsel kabul (FE-1…FE-5) — artık yürürlükte değil

| ID | Eski karar | Not |
|----|------------|-----|
| FE-1 | C→A Django template v1 | Supersede → ADR-0017 (Next.js birincil) |
| FE-2 | `/supplier/` Django | Supersede → tedarikçi UI Next.js; API B6 |
| FE-3 | Session portal; API Token ayrı | Supersede → session+CSRF API birincil (tarayıcı token yok) |
| FE-4 | PWA sonra | ADR-0017 kapsamında sonra |
| FE-5 | Minimal CSS | Next.js: Tailwind v4 + shadcn (frontend dizini) |

## Kod mirası (silinmez)

- `/buyer/` — F9-010 dashboard, F9-011 katalog, F4-062 sepet/sipariş, finans/onay/RFQ UI
- `/ops/finance/` — F5-032
- Yeni F9-012…015 **Django HTML büyütme** → iptal / ertelenmiş; yerine API B1–B7 + Next.js

## İlişkili

- Yerine: [ADR-0017](ADR-0017-nextjs-api-sozlesmesi.md)
- BACKLOG F9-001; MASTER §12
