# Open Work (ADIM 4)

**Tarih:** 2026-11-11  
**Tarama:** `backend/config` (migrations/`__pycache__`/tests hariç TODO|FIXME|HACK|XXX|NotImplementedError) + MASTER §12.3 + API_CONTRACT §4 + `lint_openapi` (önce/sonra).

## Kod içi TODO/FIXME/NotImplemented

| Öncelik | Dosya:satır | Açıklama | Önerilen çözüm |
|---------|-------------|----------|----------------|
| — | — | `rg` ile **eşleşme yok** (DOĞRULANDI 2026-11-11) | — |

## Bilinçli stub / fake (ürün kararı — silinmez)

| Öncelik | Dosya | Açıklama | Önerilen çözüm |
|---------|-------|----------|----------------|
| P2 | `backend/config/integrations/erp/fake.py` | FakeERPAdapter (F7) | Canlı ERP bağlanınca registry |
| P2 | `backend/config/integrations/crm/fake.py` | FakeCRMAdapter | Aynı |
| P2 | `backend/config/integrations/edi/punchout.py` | Punchout inbound ack-only | Canlı EDI tüketici |
| P2 | `finans.payments` fake adapter | Fail-closed fake ödeme | Gerçek provider (yol B) |
| P2 | `lojistik.carriers` fake | Fake kargo label | Canlı carrier |

## Döküman / OpenAPI boşlukları (bu audit’te kapatılanlar)

| Öncelik | Bulgu | Durum |
|---------|-------|--------|
| P0 | `lint_openapi`: password-reset/change + MFA request/response unbound | **Kapatıldı** — `openapi_requests.py` + `openapi_components.py` + export |
| P1 | API_CONTRACT OpenAPI path sayısı **81** (gerçek 98) | **Kapatıldı** |
| P1 | HTML `/buyer` “korunur” iddiası (ADR-0029 ile çelişki) | **Kapatıldı** (Deprecated notları) |

## MASTER §12.3 / ürün açık iş

| Öncelik | ID | Açıklama | Önerilen çözüm |
|---------|-----|----------|----------------|
| P1 | NX / F9 Next portal | API READY; ürün dilim talimatı bekliyor | Ürün sahibi talimatı |
| P2 | F6-032 | Platform uyuşmazlık ops kuyruğu UI | Next ops dilimi |
| P2 | FE-SUITE | Tam PG suite yeşil kanıtı eksik (MASTER §2.7) | Onaylı full suite koşusu |
| P2 | F8-003 staging | Sentry staging event | Staging DSN + event |
| — | FE v1 dışı | RFQ eşleştirme / belge / limit / release HTTP | Bilinçli kapalı (`API_READINESS` §4) |

## Endpoint kalite boşlukları (kalan)

| Öncelik | Dosya/konu | Açıklama | Önerilen çözüm |
|---------|------------|----------|----------------|
| P2 | Meta routes OpenAPI dışı | `/api/schema|docs|redoc/` + `/api/v1/schema/` paths’te yok | Bilinçli (UI/meta); drift-report’ta işaretli |
| P2 | Admin act-as redirect | `/act-as/start|stop/` OpenAPI dışı | Bilinçli; API eşleniği `/api/v1/act-as/*` var |
| P1 | `__pycache__` HTML artıkları | Silinmiş `*_ui` / HTML test pyc | `pyc` temizliği (opsiyonel) |
| P2 | ADR-0027/0028/0029 | Diskte var; `git log` → NO_GIT_HISTORY | Commit (bu audit veya ayrı) |

## Migration / model

| Öncelik | Bulgu | Not |
|---------|-------|-----|
| — | Bu turda model değişikliği yok | `makemigrations` gerekmedi |
| P2 | Üretim migrate | Kullanıcı onayı olmadan çalıştırılmaz (AGENTS) |

## Test edilmeyen / zayıf yüzeyler

Odaklı API dilim testleri mevcut (B1–B7, NX, auth QA). Tam suite bu oturumda **çalıştırılmadı** → FE-SUITE kanıtı **DOĞRULANAMADI** (ortam süresi / ürün kilidi).
