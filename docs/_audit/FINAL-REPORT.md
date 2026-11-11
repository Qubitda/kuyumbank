# FINAL REPORT — CRUD tamamlaması (API-only)

**Tarih:** 2026-11-11  
**Dal:** `adim-1-ilerleme`  
**Mimari kilit:** ADR-0029 API-only · FE feature services (UI sayfa yok)

---

## Eklenen endpoint’ler

| Metot | Path | Not |
|-------|------|-----|
| POST | `/api/v1/supplier/offers/` | `teklif_servisi.taslak_olustur` → 201 JSON |
| GET | `/api/v1/ops/rfq-lines/{line_id}/match-candidates/` | F10-021 aday |
| GET/POST | `/api/v1/ops/rfq-lines/{line_id}/matches/` | liste / öner |
| POST | `/api/v1/ops/rfq-matches/{id}/approve/` | onay → line.varyant |
| POST | `/api/v1/ops/rfq-matches/{id}/reject/` | red + neden |

OpenAPI: **102 path / 112 op** (`lint_openapi` OK).

---

## Commit listesi (bu görev)

| Commit | Özet |
|--------|------|
| `763ccb8` | feat(supplier): teklif create |
| `1602b22` | feat(ops): RFQ eşleştirme HTTP + docs/OpenAPI |
| *(FE)* | feature services + schema regenerate |

---

## HTML tarama (doğrulama eki)

```
rg -i "render\(|TemplateView|template_name|HttpResponse\(.*<html" backend/config
```

Portal eşleşme: **yok**. Kalan: `bildirim.template_servisi.render` (e-posta ADR-0027) · admin toplu-red `engines.from_string` (paket `admin/base_site`).

---

## Suite / kapılar

| Kapı | Sonuç |
|------|--------|
| Odaklı: offer create + RFQ match | **2 OK** |
| `makemigrations --check` | OK |
| `export_openapi` / `lint_openapi` | OK (102/112) |
| FE `tsc --noEmit` / `eslint` | OK |
| FE birim test runner | **KARAR GEREKTİ** — `frontend/package.json` / `frontend/AGENTS.md` test script yok; vitest eklenmedi (mimari bağımlılık yasağı) |
| Full PG suite | koşum notu: smoke matrix ayrı; full suite FINAL sonrası |

---

## crud-matrix kalan EKSİK

| Kaynak | Durum | Gerekçe |
|--------|-------|---------|
| profile/adres CRUD | **EKSİK** | F9-017; firmalar adres HTTP yüzeyi henüz yok — `docs/BACKLOG.md` F9-017 |
| bildirimler list HTTP | **KAPSAM DIŞI** | ADR-0027 outbox/admin |

---

## KARAR GEREKTİ

1. FE unit test altyapısı: `frontend/AGENTS.md` + `package.json` — test komutu tanımlı değil; bağımlılık eklenmedi.
2. Profil/adres API şekli (F9-017) — ADR alan sözleşmesi netleşmeden implement yok.

## DOĞRULANAMADI

- Live `runserver` HTTP smoke (Client smoke kullanıldı).
