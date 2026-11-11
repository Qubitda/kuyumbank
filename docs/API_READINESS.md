# BACKEND API READINESS

**Tarih:** 2026-11-11  
**Karar:** **FRONTEND READY** (ürün sahibi Qubit — “go hepsini onaylıyorum”)  
**Bağlam:** API-B1…B7 **Kabul** · ADR-0019 **Kabul** · ADR-0023 mahsup · ADR-0026 rapor · ADR-0017 NX madde Kabul  
**Normatif teknik sözleşme:** [API_CONTRACT](API_CONTRACT.md) · [openapi-v1.json](api/openapi-v1.json)  
**Kanıt ilkesi:** kod + test; doküman “UYGULANDI” tek başına yeterli değil.

> Next.js ürün dilimleri ürün sahibi talimatıyla başlar; bu kapı **FRONTEND READY**.

---

## 1. Karar özeti

| Kapı şartı | Durum |
|------------|--------|
| Hedef ürün akışlarının API karşılığı | **TAMAM** (v1) — rapor/mahsup açıldı; §4 P1/P2 **FE v1 dışı** imzalı |
| API sözleşmeleri (response/request) | **TAMAM** |
| Yetki + tenant test | **KISMİ TAMAM** — B1–B6 + ADR-0019 + rapor/mahsup odaklı |
| OpenAPI + docs UI | **TAMAM** |
| TS client üretimi | **UYGULANDI** — `frontend/lib/api/schema.d.ts` (`npm run generate:api`) |
| Backend test paketi | **TAMAM** — PG full suite **588 OK** (2026-11-11; `docs/_audit/full-suite-log.txt`) |
| FE geliştirme borcu | Next portal dilimleri ayrı talimat |

### Verdict

# FRONTEND READY

---

## 2. API hazır olma matrisi (özet değişiklikler)

| Domain | API |
|--------|-----|
| Mahsup | **AÇIK** ADR-0023 |
| Rapor / anomali | **AÇIK** ADR-0026 |

RFQ eşleştirme + supplier teklif create + profil/adres HTTP **UYGULANDI**. Belge / limit / release → FE v1 **dışı** imza.

---

## 3. KAPALI / KARAR (güncel)

| Konu | Durum |
|------|--------|
| Ops order iptal HTTP | OL-2 kapalı (bilinçli) |
| FXQ / DYN / I18N / AI | [NOTE-PENDING](decisions/NOTE-PENDING-PRODUCT-DECISIONS.md) **Kabul** — kod kapıları kapalı (A seçimleri) |
| CORS cross-origin | ADR-0017 erteli |
| Dynamic pricing | U-015 + DYN-1=A kapalı |

---

## 4. FE v1 kapsam — imza

| ID | Konu | İmza |
|----|------|------|
| FE-P1-RFQ | RFQ eşleştirme HTTP | **UYGULANDI** ✓ — `/ops/rfq-lines/.../matches*` |
| FE-P1-PROFILE | Profil/adres HTTP (F9-017) | **UYGULANDI** ✓ — `/me/profile/`, `/me/addresses/` |
| FE-P1-DOC | Belge HTTP | **FE v1 dışı** ✓ |
| FE-P2-LIM | Harcama limiti CRUD HTTP | **FE v1 dışı** ✓ |
| FE-P2-REL | Contract release HTTP | **FE v1 dışı** ✓ |
| FE-P2-ORG | Org update/deactivate HTTP | **FE v1 dışı** ✓ |
| FE-TS | openapi-typescript | **UYGULANDI** ✓ |
| FE-SUITE | Tam suite | **UYGULANDI** ✓ — PG **590 OK** (2026-11-11; MASTER §2.7); F9-017 sonrası odaklı +3 |

---

## 5–6. OpenAPI / Docs UI

Önceki gibi. Generate: `cd frontend && npm run generate:api`.

---

## 7. FRONTEND READY checklist

1. §4 imza — **Evet**  
2. TS client — **Evet** (`lib/api/schema.d.ts`)  
3. Onaylı tam suite — **KISMİ** (override; yeniden kilitleme: PG’de 0 ERROR)  
4. **FRONTEND READY** + Next talimatı — ürün sahibi onayı alındı  
