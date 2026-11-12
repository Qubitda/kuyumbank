# Kuyumbank — Agent Talimatı

Bu dosya proje genelinde bağlayıcıdır. Teknik doğruluk ve veri güvenliği, hızdan önce gelir.
Proje bağlamını burada tekrar etme; kanonik durum için master’a git.

## Proje (kısa)

Jewelry B2B platform. Django modular monolith. Alıcı–tedarikçi **kör havuz**; fiyat **snapshot/kilit**; stok **ledger + rezervasyon**; `siparis` **Cart → Checkout → Order** (+ iptal/IADE).

## İlk okuma sırası

1. Bu `AGENTS.md`
2. `docs/MASTER.md` — özellikle **§2** (gerçek durum) ve **§12** (sıradaki adım)
3. Görevle ilgili **tek** skill (aşağıdaki tablo)
4. İlgili mevcut kod (model/servis/test) — yeniden yazmadan önce

Kurulum komutları: `docs/RUNBOOK.md` + kök `README.md` → `backend/README.md`.

## Bilgi kaynakları (tek sahiplik)

| Bilgi | Tek kaynak |
|-------|------------|
| Agent kuralları / yasaklar / süreç | **Bu dosya** |
| Canlı durum, standartlar, §12 | **`docs/MASTER.md`** |
| ADR / kararlar | **`docs/decisions/`** |
| İş havuzu / U-* | **`docs/BACKLOG.md`** |
| Yol haritası / capability gap | **`docs/ROADMAP.md`** |
| Faz tarihçesi | **`docs/HISTORY.md`** |
| Kurulum / işletim | **`docs/RUNBOOK.md`** + `README.md` |
| Veri sözlüğü (otomatik) | **`docs/DATA_DICTIONARY.md`** |
| API insan özeti (B7; OpenAPI normatif) | **`docs/API_CONTRACT.md`** + **`docs/api/openapi-v1.json`** |
| Frontend-ready kapısı | **`docs/API_READINESS.md`** |
| Framework API | Django 6.1 docs / kaynak |
| İş/mimari skill | `.cursor/skills/*` (Django resmi skill değil) |

`docs/` düzeni: her bilgi tek yerde (MASTER + decisions/BACKLOG/ROADMAP/HISTORY/RUNBOOK/DATA_DICTIONARY/API_CONTRACT + openapi). 
Yeni oturum: **bu dosya → `docs/MASTER.md` §2 + §12**.  
`SESSION_HANDOFF` / durum raporu / ikinci yol haritası / dağınık özet **üretilmez**. Cursor indeksindeki silinmiş dosya adı kanıt sayılmaz (diskte `Test-Path` / `ls`). 
AUTO blokları ve veri sözlüğü: `python scripts/docs_sync.py` (+ CI `--check`).

## Hedef runtime

- Python: 3.12–3.14 (geliştirme: 3.14.6)
- Django: **6.1.x** (pin: 6.1.2)
- DB: PostgreSQL (`backend/config/requirements.txt`)
- `manage.py`: `backend/config/`
- **Frontend:** Vite + React Router + TanStack Query (`frontend/`) — [ADR-0031](docs/decisions/ADR-0031-vite-spa-portal.md) **Kabul**. Next.js App Router / `next/*` shim **yasak**.
- FE paket yöneticisi: **npm** (`package-lock.json`); `bun.lock` commit edilmez.
- FE boşlukları: `frontend/BACKEND_GAPS.md` (sahte endpoint yok).
- Yerel demo kimlik: `paa` dosyası **repoya girmez** (gitignore).

## Django docs vs proje skill’leri

- Django docs/kaynak = framework kullanımı için normatif.
- `.cursor/skills/` = yalnız Kuyumbank kuralları; Django docs yerine geçmez.

## Görev yürütme protokolü (token tasarrufu)

1. Master §2 / §12 + ilgili ADR / backlog kartına bak.
2. Yalnız görev dosyalarını oku; tüm repoyu yeniden tarama.
3. Kabul edilmiş ADR’yi yeniden tartışma; Taslak’ı kendi kendine Kabul etme.
4. Analiz yeterliyse kodla; bitince master’ı güncelle (kod + test + docs birlikte).
5. Odak test → (dilim kapanışında / kullanıcı isterse) suite. PG kısıtını SQLite ile “geçti” sayma.
5b. **Vite FE dilim (ADR-0031):** `frontend` altında `npm run build` / `npm run dev` (varsayılan host `127.0.0.1`; LAN için `npm run dev:lan`). Vite `/api` proxy → Django. Same-origin session/CSRF; Django doğrudan 200 smoke sayılmaz. E2E: `npm run test:e2e` (Playwright).
6. Üretim `migrate` / secret / yıkıcı git **kullanıcı onayı olmadan yok**.
7. Rapor: Tamamlananlar / Testler / Riskler / Sonraki faz (+ değişen dosyalar).

## Skill yükleme (görev başına bir)

| Görev | Skill |
|-------|--------|
| Model, ORM, servis, migration, admin | `.cursor/skills/django-engineering/SKILL.md` |
| Tenant, RBAC, kör havuz, API yetki | `.cursor/skills/multi-tenant-security/SKILL.md` |
| Katalog, teklif, fiyat, stok, sipariş kuralları | `.cursor/skills/business-domain/SKILL.md` |
| Test yazma / çalıştırma | `.cursor/skills/testing-quality/SKILL.md` |

## Faz sırası (bağlayıcı)

Kod: ilgili ADR **Kabul** + açık talimat olmadan o fazın uygulaması başlamaz (`docs/decisions/`).

1. Faz 0 — standartlar (tarihsel)
2. Faz 1 — firma, kullanıcı, RBAC, izolasyon
3. Faz 2 — katalog
4. Faz 3 — teklif / fiyatlama / quote / PriceLock (ADR-0010 **Kabul**)
5. Faz 4 — stok → rezervasyon → cart → checkout → order (+ bulk/PRE)
6. Faz 5+ — finans, QC, API, ops — `docs/MASTER.md` §12 + ROADMAP

Canlı durum: master **§2** + **§12**. Finans ADR-0012 **Kabul**.

## Temel iş kuralları

- Kullanıcı tek firmaya bağlı; platform firması tekil.
- Firma verisi tenant-scoped; client `firma_id` / `tedarikci_id` güvenilmez.
- Kör havuz: alıcı↔tedarikçi kimlik/maliyet sızıntısı yok.
- Katalog platform; teklif tedarikçi; alıcı fiyatı quote.
- Fiyat: Decimal; siparişte snapshot zorunlu (`OrderLine` + L-11 `price_lock`).
- Stok: Movement (immutable) ≠ Balance (projeksiyon) ≠ Reservation (TTL hold); sipariş tüketimi SATIS, iptal IADE.
- Kritik işlem audit; fail audit `domain_atomic` dışında durable; AuditOlay UPDATE/DELETE yasak.
- Alanın modelde olması kuralın uygulandığı anlamına gelmez.

## Teknik standartlar

- Django public API; domain logic serviste (ADR-0004 paketleri).
- `transaction.atomic` / stok-finans: `select_for_update` + DB constraint.
- Decimal; secret koda/log’a yazılmaz.
- Onaysız toplu refactor / ölü soyutlama yok.

## Test ve migration

- Yeni özellik: model + service + (varsa) API + yetki + tenant + sınır test; concurrency → PG.
- Çalıştırılmayan test başarılı gösterilmez.
- `makemigrations` üretilebilir; **üretim migrate kullanıcı onayı**.
- Migration’ı oku; veri kaybı riskini açıkla.
- Test etiketi: `fiyatlama.tests` (bare `fiyatlama` `admin`/`models` import hatası üretebilir).

## Ek kural A — Kanıt etiketleri

- **DOĞRULANDI** — dosya/satır veya komut çıktısı
- **DOĞRULANAMADI** — ortam/erişim yok
- **PLANLAMA BULGUSU** — mimari; runtime yok

## Ek kural C — Fayda/maliyet

Önce işlev + güvenlik + ticari doğruluk; sonra odaklı test; gereksiz mükemmelleştirme yok. P0 güvenlik/finans derhal; P2 kaydet-akışı-kesme.

## Yasaklar

- `.env` / secret çıktıya yazma
- İzinsiz üretim DB / migrate / DB silme
- `git reset --hard` / force push / kullanıcı değişikliklerini ezme
- Uygulanmamış özelliği UYGULANDI yazma
- Kabul ADR’yi ajanın Kabul etmesi

## Belirsizlik

Net gereksinim → uygula. Eksik detay → güvenli varsayım + `docs/decisions/` **Taslak** ADR. Veri kaybı / finans / güvenlik / geri dönülemez mimari → dur, karar iste.
