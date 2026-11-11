# FINAL REPORT — Docs ↔ Kod API Audit

**Tarih:** 2026-11-11  
**Dal:** `adim-1-ilerleme`  
**Yöntem:** ADIM 0→5; kanıt = dosya/satır veya komut çıktısı. Tahmin yok.

---

## 1. Yapılan değişiklikler (dosya bazlı)

| Dosya | Sorumluluk |
|-------|------------|
| `docs/_audit/endpoint-inventory.md` | ADIM 0: doküman git tarihleri + Django/OpenAPI endpoint tablosu |
| `docs/_audit/drift-report.md` | ADIM 1: a/b/c drift listeleri |
| `docs/_audit/open-work.md` | ADIM 4: açık iş / stub / P0–P2 |
| `docs/_audit/endpoint-readiness.md` | ADIM 5: op bazlı hazırlık tablosu |
| `docs/_audit/smoke-results.json` | Smoke çıktısı |
| `docs/_audit/FINAL-REPORT.md` | Bu rapor |
| `docs/API_CONTRACT.md` | Path sayısı 98; HTML miras → ADR-0029 Deprecated |
| `docs/MASTER.md` | §12 HTML kartları Deprecated; güncelleme notu |
| `docs/BACKLOG.md` | F4-062 / F5-032 / F10-014/023 / F9-010/011/012 HTML Deprecated |
| `docs/ROADMAP.md` | Experience katmanı + gap/portal HTML iddiaları |
| `docs/RUNBOOK.md` | Silinmiş HTML test komutları → B2 API test |
| `docs/HISTORY.md` | Append: 2026-11-11 audit |
| `docs/decisions/ADR-0017-*.md` | `/buyer|/ops` → ADR-0029 supersede |
| `docs/api/openapi-v1.json` | Export (auth DTO enrich sonrası) |
| `backend/config/api/openapi_requests.py` | Password/MFA request şema + REQUEST_BINDINGS |
| `backend/config/api/openapi_components.py` | DetailOk / MfaVerifyOk + RESPONSE_BINDINGS |
| `scripts/smoke_api.py` | ADIM 5 smoke (Django Client / HTTP) |
| `scripts/_audit_*.py` | Envanter/rapor yardımcıları (tekrar üretilebilir) |
| `frontend/lib/api/schema.d.ts` | `npm run generate:api` yenileme |

**Kod davranışı (iş kuralı) değiştirilmedi.** Yalnız OpenAPI sözleşme zenginleştirme + döküman hizalama + smoke.

**Commit’ler (bu audit):**
- `ad2ee36` — `fix(api): OpenAPI password/MFA request and response DTO bindings`
- `59b6f5c` — `docs: API audit inventory, drift report, and HTML portal Deprecated sync`

---

## 2. Döküman ↔ kod uyum durumu (önce / sonra)

| Konu | Önce | Sonra |
|------|------|-------|
| OpenAPI path ↔ Django `/api/v1` ops | Uyumlu (only_oa=0) | Aynı; lint **OK** |
| Meta `/api/schema|docs|redoc` | Kodda var, OpenAPI paths’te yok | Bilinçli; drift-report’ta |
| API_CONTRACT path sayısı | **81** (bayat) | **98** |
| HTML `/buyer` “korunur” | API_CONTRACT / ROADMAP / BACKLOG / MASTER | **Deprecated** + API eşlenikleri |
| `lint_openapi` password/MFA | unbound / weak schema | **Kapatıldı** |
| FE → BE çağrıları | csrf/login/logout/me/health | Hepsi backend’de ✅ |

---

## 3. Hâlâ açık olan işler (öncelikli)

1. **P0/P1** Working tree’de ~130 dosya hâlâ uncommitted: ADR-0029 HTML silme, ADR-0028 invite/verify, `bildirim/`, migration’lar (bu audit commit’lerine **bilinçli dahil edilmedi**)  
2. **P1** Next portal dilimleri (MASTER §12.3) — ürün sahibi talimatı  
3. **P2** FE-SUITE tam PG suite yeşil kanıtı (bu oturumda full suite **çalıştırılmadı**)  
4. **P2** F6-032 uyuşmazlık ops UI; gerçek ödeme/kargo; staging Sentry event  
5. Bilinçli kapalı: CORS, RFQ eşleştirme HTTP, teklif create HTTP, Celery  

Detay: [`open-work.md`](open-work.md).

---

## 4. Endpoint hazırlık + smoke

| Metrik | Değer | Kanıt |
|--------|-------|-------|
| Django API/act-as route kaydı | 104 | `endpoint-inventory.md` |
| OpenAPI paths / ops | 98 / 106 | `openapi-v1.json`; `lint_openapi` OK |
| Hazırlık tablosu (test kanıtlı op) | 106 / 106 | `endpoint-readiness.md` |
| Smoke | **15/15 OK** | `smoke-results.json` (`django.test.Client` + ALLOWED_HOSTS override) |
| Live HTTP server smoke | **Çalıştırılmadı** | Ayrı `runserver` ayağa kaldırılmadı; Client yeterli route/auth gate için |

Odaklı test (bu oturum):  
`api.tests.test_api_b7_openapi` + `test_auth_qa_gates` + `test_api_nx_contract` → **13 OK**.

---

## 5. Doğrulanamayan maddeler ve nedenleri

| Madde | Neden |
|-------|-------|
| Tam Django test suite (MASTER §2.7 sayı) | Bu oturumda full suite koşulmadı; süre/ürün kilidi |
| Canlı `runserver` + HTTP `--base` smoke | Sunucu başlatılmadı; Client smoke kullanıldı |
| Prod DB migrate uygulanabilirliği | Üretim migrate yasak / onay yok |
| Staging Sentry event | Ortam yok (MASTER’da da DOĞRULANAMADI) |
| Prosperer runtime eşdeğerliği | Ürün hedefi; runtime DOĞRULANAMADI (MASTER §1.5) |

---

## ADIM özeti

| ADIM | Durum |
|------|--------|
| 0 Envanter | ✅ `endpoint-inventory.md` |
| 1 Drift | ✅ `drift-report.md` |
| 2 Bayat blok | ✅ dökümanlar koda hizalandı |
| 3 Eksik implement | ✅ eksik endpoint yok; OpenAPI auth DTO tamamlandı |
| 4 Open work | ✅ `open-work.md` |
| 5 Readiness + smoke | ✅ `endpoint-readiness.md` + `smoke_api.py` |
