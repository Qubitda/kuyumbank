# FINAL REPORT — CRUD tamamlaması (API-only) + F9-017

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
| GET/PATCH | `/api/v1/me/profile/` | F9-017 profil (first_name/last_name) |
| GET/POST | `/api/v1/me/addresses/` | F9-017 liste/oluştur (`manage_users` yazma) |
| GET/PATCH/DELETE | `/api/v1/me/addresses/{id}/` | F9-017; IDOR → 404 |

OpenAPI: **105 path / 119 op** (`lint_openapi` OK).

---

## Commit listesi (bu görev)

| Commit | Özet |
|--------|------|
| `763ccb8` | feat(supplier): teklif create |
| `1602b22` | feat(ops): RFQ eşleştirme HTTP + docs/OpenAPI |
| *(FE)* | feature services + schema regenerate |
| *(pending)* | feat(firmalar): F9-017 profil/adres HTTP |

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
| Odaklı: F9-017 profile/address | **3 OK** |
| `makemigrations --check` | OK (migration yok) |
| `export_openapi` / `lint_openapi` | OK (105/119) |
| FE `tsc --noEmit` / `eslint` | OK |
| FE birim test runner | **KARAR GEREKTİ** — `frontend/package.json` test script yok; vitest eklenmedi |
| Full PG suite | **590 OK** (önceki koşu); F9-017 sonrası +3 odaklı — tam suite yeniden koşulmadı |

---

## crud-matrix kalan EKSİK

| Kaynak | Durum | Gerekçe |
|--------|-------|---------|
| bildirimler list HTTP | **KAPSAM DIŞI** | ADR-0027 outbox/admin |

EKSİK satırı kalmadı (imzasız boşluk yok).

---

## KARAR GEREKTİ

1. FE unit test altyapısı: `frontend/package.json` — test komutu tanımlı değil; bağımlılık eklenmedi.
2. ~~Profil/adres API şekli~~ — **kapandı uygulama ile** (güvenli varsayım): `/me/profile` + `/me/addresses`; yazma `manage_users`; hard delete; email PATCH yok.

## DOĞRULANAMADI

- Live `runserver` HTTP smoke (Client smoke kullanıldı).
- F9-017 sonrası full PG suite yeniden koşusu (yalnız odaklı 3+9 OK).
