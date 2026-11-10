# Kuyumbank frontend (NX-FE)

Next.js App Router + TypeScript iskeleti. Normatif API: repo kökü [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) + [`docs/api/openapi-v1.json`](../docs/api/openapi-v1.json). Politika: [ADR-0017](../docs/decisions/ADR-0017-nextjs-api-sozlesmesi.md).

## Mimari

Feature/domain rehberi: [`docs/FRONTEND_ARCHITECTURE.md`](docs/FRONTEND_ARCHITECTURE.md).

- `src/features/<django-app>` — components / types / services / hooks / schemas
- `src/app/(portal)/<domain>` — `page` / `loading` / `error` (+ `_components`)
- `src/lib/api` — session + CSRF istemci

## Ne var / ne yok

| Var | Yok (bilinçli) |
|-----|----------------|
| App Router, Tailwind v4, Geist, Zod | shadcn tam kit (NX-SHELL) |
| Aynı-origin `/api/v1/*` rewrite → Django | CORS |
| Session + CSRF istemci (`lib/api`) | Tarayıcıda Token |
| Domain route iskeleti (10 app) | Dolu katalog/sepet UI |
| OKLCH grayscale token’lar | Celery / GraphQL |

Django `/buyer/` ve `/ops/` HTML **silinmez**.

## Yerel çalıştırma

1. Backend: `backend/config` → `runserver` (PG + migrate zaten).
2. Django `.env`:
   ```text
   CSRF_TRUSTED_ORIGINS=http://localhost:3000
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```
3. Frontend:
   ```bash
   cp .env.example .env.local
   npm install
   npm run dev
   ```
4. Aç: http://localhost:3000 — health/me smoke; giriş `/login`.

`DJANGO_ORIGIN` varsayılan `http://127.0.0.1:8000`.

## Komutlar

```bash
npm run lint
npm run build
```
