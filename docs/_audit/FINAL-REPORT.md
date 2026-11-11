# FINAL REPORT — Frontend öncesi backend kapanış

**Tarih:** 2026-11-11  
**Dal:** `adim-1-ilerleme`  
**Amaç:** Döküman↔kod uyumu + rol bazlı kanıt + portal boşluk kararları

---

## Önce / sonra

| Metrik | Önce (bayat iddia) | Sonra (export) |
|--------|--------------------|----------------|
| OpenAPI paths | 98 / 102 (dağınık) | **105** |
| OpenAPI ops | 106 / 112 | **119** |
| Full suite | 588 vs 590 çelişkisi | **594 OK** (`full-suite-log.txt`) |
| Smoke | anon-only `smoke_api.py` | **`--matrix`** → 119 op · **309/309** check |
| API_READINESS §7.3 | KISMİ | **TAMAM** (log + matrix) |
| ROADMAP #4 | «Eşleştirme HTTP yok» | **UYGULANDI** (create + match) |
| API_CONTRACT §2.1 | «teklif create HTTP yok» | **create var** |

Doğrulama: `python scripts/export_openapi.py --check` OK · `lint_openapi` paths=105 schemas=111 operationIds=119.

---

## Eklenen / değişen endpoint’ler (bu kapanış + CRUD)

| Metot | Path | Durum |
|-------|------|-------|
| POST | `/supplier/offers/` | UYGULANDI (handler + test) |
| GET/POST | `/ops/rfq-lines/{line_id}/matches|match-candidates/` | UYGULANDI |
| POST | `/ops/rfq-matches/{id}/approve|reject/` | UYGULANDI |
| GET/PATCH | `/me/profile/` | UYGULANDI (F9-017) |
| GET/POST/PATCH/DELETE | `/me/addresses/` | UYGULANDI (F9-017) |
| GET | `/ops/finance/` | OpenAPI DTO düzeltmesi → `OpsFinanceSummary` |

Teklif SM geçersiz geçiş (deactivate on TASLAK) → **409** (`raise_drf(..., as_conflict=True)`).

---

## Smoke kanıtı

| Koşu | Sonuç |
|------|--------|
| `python scripts/smoke_api.py --matrix` | **ok** · ops=119 · checks=309/309 · CSRF login/me/logout dahil · wrong_role + invalid_body |
| `endpoint-readiness.md` | Bu koşudan yeniden üretildi (T = matrix sonucu) |
| `--base http://127.0.0.1:8000` | **DOĞRULANAMADI** — WinError 10061 (runserver yok) |

---

## Portal bazlı boşluk kararları

| Madde | Karar | Gerekçe |
|-------|-------|---------|
| Supplier `/orders|/shipments` | **FE v1 dışı / KAPSAM DIŞI** | Kör havuz; ADR’de tedarikçi sipariş list HTTP yok — ops shipment/QC yüzeyi var |
| Teklif create→submit→versions→deactivate | **UYGULANDI** | + 409 test `test_offer_invalid_transition_409` |
| Org update/deactivate, limit CRUD, belge HTTP | **FE v1 dışı** | `API_READINESS` §4 imza |
| Profil/adres | **UYGULANDI** | F9-017 |
| Ops sipariş iptal | **OL-2 kapalı** | `API_READINESS` §3 |
| F6-032 uyuşmazlık kuyruğu | **P2 FE** | Backend: returns + `manage_return`; ayrı ops queue UI |
| Bildirim list/okundu HTTP | **KAPSAM DIŞI** | ADR-0027 outbox/admin |
| `/catalog/?q=` | **VAR** | `catalog.py` term filtresi |
| Liste page/ordering | **VAR** | `api.pagination` NX-2 |

---

## Suite / kapılar

| Kapı | Sonuç |
|------|--------|
| Odaklı offer/RFQ/profile/CSRF | OK |
| `makemigrations --check` | OK |
| `export_openapi --check` / `lint_openapi` | OK 105/119 |
| FE `tsc` / `eslint` | önceki tur OK; generate:api güncel |
| FE birim test | **KARAR GEREKTİ** — `FRONTEND_ARCHITECTURE.md:170` «FE test Yok»; vitest eklenmedi |
| Full PG suite | **594 OK** (`full-suite-log.txt`, ~16.4 dk) |

---

## HTML tarama

```
rg -i "render\(|TemplateView|template_name|HttpResponse\(.*<html" backend/config
```

Portal TemplateView / HTML route: **yok**. Kalan: `bildirim.template_servisi.render` (e-posta) · `urunler.admin` admin template.

---

## ADIM 2 FE-BE altyapı

| Madde | Durum |
|-------|--------|
| Next `/api/v1` rewrite | **VAR** `frontend/next.config.ts` |
| CSRF_TRUSTED_ORIGINS / SameSite / cookie domain | env + DEBUG Next localhost defaults |
| CSRF flow test | `test_fe_session_csrf_flow` |
| `apiFetch` problem+json + Idempotency-Key | **VAR** `frontend/src/lib/api/client.ts` |
| CORS | ADR-0017 erteli (değişmedi) |

---

## `_audit` klasörü

Kanıt dosyaları tutulur: `FINAL-REPORT.md`, `endpoint-readiness.md`, `smoke-matrix-results.json`, `smoke-results.json`, `full-suite-log.txt`, `crud-matrix.md`.  
Geçici envanter (`_raw_inventory.json`, `_git_docs.txt`, `open-work.md`, `drift-report.md`, `endpoint-inventory.md`) kaldırılır — sonuçlar bu raporda.

---

## KARAR GEREKTİ

1. FE unit-test runner / vitest — `frontend/docs/FRONTEND_ARCHITECTURE.md:170` + bağımlılık yasağı.
2. Supplier order/shipment self-service HTTP — kör havuz + ADR yok; ürün kararı gerekir.

## DOĞRULANAMADI

1. Live `runserver` HTTP smoke (`--base`) — bağlantı reddedildi (sunucu kapalı).
