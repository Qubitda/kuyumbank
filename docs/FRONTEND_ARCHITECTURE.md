# Kuyumbank Frontend Architecture

## 1. Amaç

Django modular monolith’teki **domain app** sınırlarını Next.js tarafında **feature klasörleri** olarak korumak.

> **Uyarı (2026-11-10 denetim):** Aşağıdaki tablo **hedef isimlendirme**dir. Klasör varlığı API entegrasyonu veya ürün ekranı anlamına gelmez; canlı durum → **§9**.

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

### 1.1 Dilim kapanış (entegrasyon)

| Kapı | Komut / kural |
|------|----------------|
| Derleme | `npm run build` |
| Same-origin smoke | **`npm run smoke`** (CSRF→login→`/me`→health via `:3000` rewrite) |
| Agent kuralı | `.cursor/rules/06-integration-gates.mdc` · `frontend/AGENTS.md` |

Django `127.0.0.1:8000` doğrudan yeşil → entegrasyon OK **sayılmaz**.

## 2. Klasör ağacı

```text
frontend/src/
├── app/                          # Yalnız routing + ince sayfa kompozisyonu
│   ├── layout.tsx
│   ├── page.tsx                  # NX-FE durum /me smoke
│   ├── (auth)/login/             # URL: /login
│   └── (portal)/                 # Route group — URL’ye yazılmaz
│       ├── layout.tsx            # NX-SHELL PortalShell
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

- **NX-SHELL:** **UYGULANDI** — shadcn Button/Input/Label/Dialog + PortalShell + light/dark
- **NX-BUYER:** katalog / sepet / sipariş sayfa doldurma
- Django ürün HTML portal **yok** (ADR-0029); yalnız `/admin/` + `/api/v1/` — Next portal dilimleri

---

## 9. Mimari uyum denetimi (2026-11-10)

**Kapsam:** Kod envanteri + canlı veri akışı; yeni özellik / büyük refactor yok.  
**Kaynaklar:** `backend/config/*` domain app’ler · `frontend/src/{app,features,lib}` · `api/urls.py` · ADR-0017 · API_CONTRACT · OpenAPI.

### 9.1 Özet cevaplar

| # | Soru | Cevap (kanıtlı) |
|---|------|-----------------|
| 1 | İki mimari gerçekten uyumlu mu? | **Hedef isimlendirme uyumlu; işlevsel entegrasyon KISMİ.** Klasör ↔ Django app paralel iskelet var; canlı FE↔API yalnız auth/health. |
| 2 | FE karşılığı olmayan domain’ler? | `integrations` (BE paket; FE feature yok — bilinçli). `api` HTTP yüzeyi FE feature değildir (`lib/api`). Canlı ürün UI: Next iskelet + API (ADR-0029; Django HTML portal kaldırıldı). |
| 3 | Yanlış domain’e bağlı feature? | **Yok** (domain feature’lar henüz API’ye bağlanmamış; yanlış wiring yok). |
| 4 | API sözleşmeleri tutarlı mı? | Auth/`/me`/`capabilities`: FE tipleri ↔ `present_me` **uyumlu**. Commerce DTO’ları FE’de **yok**. OpenAPI birçok response şeması zayıf (`array` stub) — normatif kod + presenter. |
| 5 | Yetki/tenant doğru yerde mi? | **Evet (backend).** FE `firma_id` göndermez; `capabilities` keşif. Portal route’larda auth gate yok (placeholder; veri yok). |
| 6 | Kritik mimari sorunlar? | (A) İsim izomorfizmi ≠ entegrasyon. (B) Next iskelet henüz commerce doldurulmamış (ADR-0029 API-only BE). (C) Feature `services/types` boş → NX-BUYER öncesi sözleşme doldurulmalı. |
| 7 | Gerekli düzeltmeler? | Doküman netliği (bu §). Küçük: `HealthResponse.service?`. Büyük refactor **yok**. Sonraki ürün dilimi: feature service ↔ OpenAPI path eşlemesi (NX-BUYER/SHELL). |

### 9.2 Backend envanter (DOĞRULANDI)

| App | Rol | Not |
|-----|-----|-----|
| `tanimlar`…`belgeler` | Domain (ADR-0004) | `services/` dolu; iş kuralı burada |
| `api` | HTTP / presenter / permission | FE feature değil |
| `integrations` | ERP/CRM/EDI stub | FE yok |
| `config` | settings/urls | `/admin/`, `/api/v1/`, `/act-as/` (redirect) |

Canlı ürün HTTP: `/api/v1/*` (B1–B7 + act-as + invite); Admin. Django `/buyer|/supplier|/ops` HTML **kaldırıldı** (ADR-0029).

### 9.3 Frontend envanter (DOĞRULANDI)

| Yol | Gerçek durum |
|-----|----------------|
| `features/auth` | **Canlı:** LoginForm, SessionPanel, Zod `loginSchema` (form henüz şemayı bağlamıyor) |
| `features/{firmalar…belgeler}` | **İskelet:** `services/types/hooks/components` çoğunlukla `export {}`; schemas’ta `_stub` Zod |
| `app/(portal)/<domain>` | Placeholder (`DomainPlaceholder`); API çağrısı yok |
| `lib/api/client.ts` | Merkezi `apiFetch` + CSRF + session; rewrite `next.config.ts` → Django |
| FE test | **Yok** (`*.test.*` / `*.spec.*` 0) |

§1 tablosu = **hedef isimlendirme** (NX-FE iskeleti). Bu tablo “API bağlı ürün ekranı” iddiası değildir.

### 9.4 Domain eşleşme matrisi

| Backend | FE feature | Durum | Kanıt |
|---------|------------|-------|-------|
| `firmalar` | `features/firmalar` | Kısmi eşleşme (iskelet) | route + boş service; org/approval API path’leri `/org-units/`, `/approvals/` |
| `tanimlar` | `features/tanimlar` | Kısmi (iskelet) | CAP-PIYASA/kur çoğunlukla ops/admin; FE API yok |
| `urunler` | `features/urunler` | Kısmi (iskelet) | Buyer katalog API: `/api/v1/catalog/` (view `api`, servis `urunler`) |
| `fiyatlama` | `features/fiyatlama` | Kısmi (iskelet) | HTTP: `/quotes/`, `/price-locks/` |
| `stok` | `features/stok` | Kısmi (iskelet) | Supplier `/supplier/stock/`; ATP servis BE’de; FE yok |
| `siparis` | `features/siparis` | Kısmi (iskelet) | HTTP: carts/checkouts/orders/rfqs/bulk (API) |
| `finans` | `features/finans` | Kısmi (iskelet) | HTTP: `/finance/*`, `/credit/*`, `/payments` |
| `kalite` | `features/kalite` | Kısmi (iskelet) | HTTP: `/ops/inspections/*` |
| `lojistik` | `features/lojistik` | Kısmi (iskelet) | HTTP: `/shipments/`, `/returns/`, ops shipment |
| `belgeler` | `features/belgeler` | Kısmi (iskelet) | Domain servis var; B7’de ayrı belgeler REST yüzeyi sınırlı |
| — | `features/auth` | Tam eşleşme (çapraz) | `api/views/auth.py` + `me.py` |
| `integrations` | — | Frontend karşılığı yok | Bilinçli |
| `api` | `lib/api` | Katman eşleşmesi (feature değil) | Doğru |

**Backend karşılığı yok (FE-only):** yok (auth çapraz kesit).

### 9.5 Canlı veri akışları

**A — Auth (tek tam Next akışı)**

```text
app/(auth)/login/page.tsx
  → features/auth/LoginForm
  → lib/api/client.login
  → POST /api/v1/auth/login/  (rewrite → Django)
  → api.views.auth.AuthLoginView
  → authenticate + login + present_me (capabilities_servisi)
  → MeResponse (session cookie)

app/page.tsx SessionPanel
  → GET /health/ + GET /me/ + POST /auth/logout/
```

Kanıt: `frontend/src/lib/api/client.ts`; `backend/config/api/views/auth.py`; `api/services/capabilities_servisi.py`.

**B — Portal domain sayfaları**

```text
app/(portal)/siparis/page.tsx → DomainPlaceholder
  (feature service çağrısı yok; Django /api/v1/orders|carts… kullanılmıyor)
```

**C — Canlı ürün UI**

```text
Next `app/(portal)/*` → `/api/v1/*` (ADR-0029; Django HTML portal yok)
```

### 9.6 Sözleşme notları (auth)

| Alan | Backend `present_me` | FE `MeResponse` |
|------|----------------------|-----------------|
| `id`, `username`, `rol`, `firma_id` | var | var |
| `firma.{id,ad,alici_mi,tedarikci_mi,platform_mu,aktif}` | var | var |
| `capabilities.*` (18 bayrak) | var | birebir |
| Health `service` | `"kuyumbank"` | FE tipinde opsiyonel eksik (runtime OK) |

OpenAPI `GET /me/` response şeması jenerik `array` — **FE için yetersiz**; kod/presenter otorite.

### 9.7 Mimari sınırlar

| Kontrol | Sonuç |
|---------|-------|
| FE’de fiyat/milyem hesabı | Yok (grep boş) |
| Feature → feature import | Yok (yalnız `app` → `auth`) |
| API client merkezi mi? | Evet `lib/api` |
| RBAC/tenant | Backend (`IsAuthenticatedWithFirma`, object-level ADR-0019); FE gizleme yok (henüz UI yok) |
| Ortak katman şişmesi | `route-states` ince; `components/ui` README (NX-SHELL) |

### 9.8 Hedef vs mevcut

| Hedef | Mevcut |
|-------|--------|
| BE: app → service → API | **Sağlanıyor** (B1–B7) |
| FE: route → feature → API client | **Yalnız auth** |
| Domain sınırları FE’de | Klasör düzeyinde **evet**; veri/DTO düzeyinde **hayır (henüz)** |

**Sonraki güvenli dilim (ürün talimatı ile):** NX-SHELL + bir buyer dikey (ör. `urunler` ← `/catalog/` + `siparis` ← carts/orders); tip/service’leri OpenAPI+presenter’dan doldur; HTML silinmez.
