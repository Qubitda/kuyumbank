# Frontend ↔ API

Normatif kaynaklar (repo kökü):

- [`docs/API_CONTRACT.md`](../../docs/API_CONTRACT.md)
- [`docs/api/openapi-v1.json`](../../docs/api/openapi-v1.json)
- [ADR-0017](../../docs/decisions/ADR-0017-nextjs-api-sozlesmesi.md)

İstemci: `src/lib/api/client.ts` — session cookie, `X-CSRFToken`, `credentials: "include"`, yazmada Idempotency-Key yardımcısı. Alan uydurma yok.

Mimari: [`FRONTEND_ARCHITECTURE.md`](FRONTEND_ARCHITECTURE.md) (`features/*` ↔ Django apps).
