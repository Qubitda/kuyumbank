# Kuyumbank Frontend Architecture

**Durum:** NX-FE iskelet + feature/domain katman iskeleti (2026-11-09)  
**Politika:** [ADR-0017](../../docs/decisions/ADR-0017-nextjs-api-sozlesmesi.md) · API: [API_CONTRACT](../../docs/API_CONTRACT.md)  
**Backend paralel:** ADR-0004 (`models` / `services` / `selectors`) → FE `types` / `services` / `hooks` + `components`

## 1. Amaç

Django modular monolith’teki **domain app** sınırlarını Next.js tarafında **feature klasörleri** olarak korumak:

| Backend app | Frontend feature | Tipik portal yüzeyi |
|-------------|------------------|---------------------|
| `firmalar` | `features/firmalar` | org, kullanıcı, onay (kullanıcılar ayrı Django app değil) |
| `tanimlar` | `features/tanimlar` | PB, kur, kanal (çoğunlukla ops) |
| `urunler` | `features/urunler` | katalog browse |
| `fiyatlama` | `features/fiyatlama` | quote / PriceLock |
| `stok` | `features/stok` | ATP / depo (rol kesitli) |
| `siparis` | `features/siparis` | cart / checkout / order / RFQ |
| `finans` | `features/finans` | cari, ödeme, credit |
| `kalite` | `features/kalite` | QC inspection |
| `lojistik` | `features/lojistik` | shipment / iade |
| `belgeler` | `features/belgeler` | taş sertifika vb. |
| — | `features/auth` | login / session / CSRF (çapraz kesit) |

`api` Django paketi FE’de feature değildir; HTTP istemcisi `src/lib/api` altındadır.

## 2. Klasör ağacı

```text
frontend/src/
├── app/                          # Yalnız routing + ince sayfa kompozisyonu
│   ├── layout.tsx
│   ├── page.tsx                  # NX-FE durum /me smoke
│   ├── (auth)/login/             # URL: /login
│   └── (portal)/                 # Route group — URL’ye yazılmaz
│       ├── layout.tsx            # ileride NX-SHELL
│       ├── firmalar/
│       │   ├── page.tsx
│       │   ├── loading.tsx
│       │   ├── error.tsx
│       │   └── _components/      # yalnız bu route’a özel (private)
│       ├── tanimlar/ …
│       ├── urunler/ …
│       ├── fiyatlama/ …
│       ├── stok/ …
│       ├── siparis/ …
│       ├── finans/ …
│       ├── kalite/ …
│       ├── lojistik/ …
│       └── belgeler/ …
├── features/                     # Domain mantığı (Django app ≈ feature)
│   └── <domain>/
│       ├── components/           # domain UI
│       ├── types/                # API/OpenAPI uyumlu tipler
│       ├── services/             # apiFetch sarmalayıcıları
│       ├── hooks/                # client hooks
│       ├── schemas/              # Zod (RHF)
│       └── index.ts              # public API (sığ barrel)
├── components/
│   ├── ui/                       # shadcn ortak primitives (NX-SHELL)
│   └── layout/                   # shell parçaları
├── lib/
│   ├── api/                      # client, Problem+JSON, CSRF
│   ├── format/                   # para / tarih / gram
│   └── utils.ts
└── types/                        # çapraz feature ortak tipler
```

## 3. Katman eşlemesi (Django ↔ FE)

| Django (ADR-0004) | Frontend | Kural |
|-------------------|----------|--------|
| `models/` | `features/*/types` (+ OpenAPI) | Alan uydurma yok |
| `services/` | `features/*/services` | RBAC/tenant backend’de; FE keşif için `/me` |
| `selectors/` | `features/*/services` veya server fetch | Liste/filtre sunucuda |
| `admin/` / templates | `app/(portal)/*/page.tsx` | İnce; iş UI feature’da |
| — | `features/*/hooks` | Yalnız client etkileşim |
| — | `features/*/schemas` | Form girişi; fiyat otoritesi backend |

## 3b. Katı proje kuralları

Workspace: [`.cursor/rules/kuyumbank-hard-rules.mdc`](../../.cursor/rules/kuyumbank-hard-rules.mdc) (**alwaysApply**).

Özet: feature/domain klasör · backend-first hesap · UI≠güvenlik · sözleşme versiyonlama · Card/gradient yasağı · `tabular-nums` · sahte API yok.

## 4. Import kuralları (bağlayıcı)

1. **`app` → `features` / `components` / `lib`** — sayfa feature’ı import eder; feature `app` import etmez.
2. **Feature → feature yok** — çapraz ihtiyaç varsa `lib/` veya ortak `types/`; gerekirse üst feature’a taşı.
3. **Public API** — dışarıdan yalnız `features/<x>` (`index.ts`). Derin `features/x/components/...` importundan kaçın.
4. **Sığ barrel** — `index.ts` seçilmiş export; zincirleme re-export yok.
5. **Token yok** — tarayıcıda DRF Token; session + CSRF ([NX-1](../../docs/decisions/ADR-0017-nextjs-api-sozlesmesi.md)).
6. **Kör havuz** — buyer DTO’da tedarikçi/maliyet alanı gösterme; supplier RFQ’da alıcı kimliği yok.

## 5. App Router standartları

Her portal domain route’unda:

| Dosya | Görev |
|-------|--------|
| `page.tsx` | Server Component varsayılan; feature compose |
| `loading.tsx` | Segment Suspense UI |
| `error.tsx` | Client error boundary (`"use client"`) |
| `_components/` | Yalnız bu segment’e özel UI (route değil) |

Rol bazlı URL önekleri (`/buyer`, `/supplier`) sonraki NX-SHELL diliminde eklenebilir; şimdiki path’ler domain adıyla hizalı (`/urunler`, `/siparis`, …). Yetki yine API + `/me.capabilities`.

## 6. Shared / core

| Yol | İçerik |
|-----|--------|
| `components/ui/` | Button, Input, Table, Dialog — shadcn (kurulum NX-SHELL) |
| `lib/api/` | `apiFetch`, `ApiError`, CSRF |
| `lib/format/` | `formatMoney`, `formatGram`, `formatDateTime` |
| `types/` | `ProblemDetail` vb. ortak |

## 7. Yeni feature ekleme

1. `src/features/<domain>/{components,types,services,hooks,schemas}/` + `index.ts`
2. `src/app/(portal)/<domain>/{page,loading,error}.tsx` (+ isteğe `_components/`)
3. Tipleri OpenAPI / presenter’dan doğrula; uydurma
4. Yazma uçlarında `Idempotency-Key` (`apiFetch` seçeneği)

## 8. Bilinçli sonraki dilimler

- **NX-SHELL:** shadcn primitives + `(portal)/layout` nav
- **NX-BUYER:** katalog / sepet / sipariş sayfa doldurma
- Django `/buyer/` `/ops/` HTML **silinmez**
