<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Kuyumbank Frontend — Agent kuralları (bağlayıcı)

Kök: repo `AGENTS.md` + `docs/MASTER.md` §2/§12 + `docs/BACKEND_MAP.md`.  
Mimari: `docs/FRONTEND_ARCHITECTURE.md`.  
Cursor: `.cursor/rules/06-integration-gates.mdc` (**alwaysApply**).

## Dilim kapanış kapısı (atlanamaz)

1. `npm run build` — derleme.
2. **`npm run smoke`** — same-origin rewrite üzerinden CSRF → login → `/me/` → health.
3. Django `127.0.0.1:8000` doğrudan yeşil olsa bile smoke **sayılmaz**.
4. `next.config` / proxy / CSRF / cookie / auth client değiştiyse smoke zorunlu.

```bash
# Her iki sunucu ayaktayken:
cd frontend && npm run smoke
# SMOKE_USER=demo_ops SMOKE_PASS=DemoPortal1! npm run smoke
```

## Entegrasyon gerçekleri

- Tarayıcı API yolu yalnız `/api/v1/*` (Next rewrite → `DJANGO_ORIGIN`).
- Trailing slash: Django `APPEND_SLASH`. Rewrite destination `.../:path*/` + `skipTrailingSlashRedirect: true` — **bozma**.
- Session + CSRF; tarayıcıda DRF Token yok.
- UI capability gizleme ≠ güvenlik.
- Kör havuz: buyer’da tedarikçi kimlik/maliyet yok.
- Alan/endpoint uydurma yok — OpenAPI + BACKEND_MAP.

## Yasak “bitti” iddiası

Yalnız TypeScript/build yeşili, yalnız doğrudan Django smoke, veya “muhtemelen çalışır” ile dilim kapatılmaz.
