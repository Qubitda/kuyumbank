# Kuyumbank — Kurulum ve işletim (RUNBOOK)

> Kaynak: `backend/config/config/settings.py`, `requirements.txt`, yönetim komutları, ADR-0002/0007.  
> **Henüz hosting/üretim ortamı yok** (ADR-0007: "hosting henüz yok"); üretim satırları şablon ve kontrol listesidir,
> işaretli olanlar **DOĞRULANAMADI**. Durum etiketleri için bkz. [MASTER](MASTER.md).

## 1. Gereksinimler

| Bileşen | Sürüm / not |
|---------|-------------|
| Python | 3.12–3.14 (geliştirme: 3.14.6) |
| Django | 6.1.2 (pin) |
| PostgreSQL | Zorunlu. Testler PG ile çalışır; **SQLite ile "geçti" sayılmaz** (constraint / trigger / exclusion) |
| Paketler | `requirements.txt` (yalnız doğrudan bağımlılık; ADR-0002) |
| Celery / Redis | **Yok** (F8). Periyodik işler cron/systemd timer ile `manage.py` komutlarıdır |

## 2. Ortam değişkenleri

`settings.py` `environ.Env` ile `backend/config/.env` dosyasını (varsa) okur; gerçek ortam değişkenleri de çalışır.
**`.env` sürüm kontrolüne girmez** (bkz. §6; [SEC-001](BACKLOG.md)).

| Değişken | Zorunlu | Varsayılan | Not |
|----------|---------|-----------|-----|
| `SECRET_KEY` | Evet | — | Yoksa proje bilerek açılmaz |
| `DEBUG` | Hayır | `False` | Yalnız geliştirmede `True` |
| `ALLOWED_HOSTS` | Prod'da evet | `[]` | Virgülle ayrılmış; `DEBUG` iken boşsa `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Evet | — | |
| `DB_HOST`, `DB_PORT` | Hayır | `localhost`, `5432` | |
| `EMAIL_BACKEND` | Hayır | console backend | Prod'da SMTP backend verilir |
| `SECURE_SSL_REDIRECT` | Hayır | `True` (`DEBUG=False` iken) | |
| `SECURE_HSTS_SECONDS` | Hayır | `3600` | Sorunsuzsa artırın |
| `PLATFORM_BRAND_NAME` | Hayır | boş | Boşsa SEO fallback yalnız ürün/kategori adı |
| `VARYANT_GRAM_BANDI_ORAN` | Hayır | `0.05` | Gram bandı göreli toleransı (ADR-0005 K3) |
| `TRUSTED_PROXY_COUNT` | Hayır | `0` | AUD-001b X-Forwarded-For hop |
| `SECURE_PROXY_SSL_HEADER` | Hayır | `False` | Proxy arkasında `True` |
| `LOG_LEVEL` | Hayır | `INFO` | F8-002 |
| `LOG_JSON` | Hayır | `False` | `True` → tek satır JSON + `request_id` |
| `DRF_THROTTLE_ANON/USER/BUYER/SUPPLIER/OPS` | Hayır | settings | F8-009; örn. `60/min` |
| `SENTRY_DSN` | Hayır | boş | F8-003; boşsa SDK no-op (`sentry-sdk==2.69.1`) |
| `SENTRY_ENVIRONMENT` | Hayır | `development` | F8-003 |
| `SENTRY_TRACES_SAMPLE_RATE` | Hayır | `0.0` | F8-003; düşük başla |
| `PAYMENT_PROVIDER` | Hayır | `fake` | Canlı banka yok |
| `PAYMENT_WEBHOOK_SECRET` | Prod webhook için | boş | Boşsa webhook 401 (fail-closed) |
| `CARRIER_PROVIDER` | Hayır | `fake` | Canlı kargo yok |
| `SHIPMENT_POD_REQUIRED` | Hayır | `False` | POD gate |
| `QC_GRAM_TOLERANCE_PCT` / `_ABS` | Hayır | `0.50` / `0` | F6-011 |
| `HAS_POSITION_LIMIT` | Hayır | `0` | 0 = kapalı |
| `SUPPLIER_ACCRUAL_VADE_GUN` | Hayır | `0` | F5-022 |
| `CRM_SYNC_ENABLED` | Hayır | `False` | F7 opt-in |
| `CSRF_TRUSTED_ORIGINS` | Next yerel için | `[]` | örn. `http://localhost:3000` (NX-FE aynı-origin rewrite) |
| `SESSION_COOKIE_DOMAIN` / `CSRF_COOKIE_DOMAIN` | Hayır | boş | Boş = host-only; prod proxy’de gerekirse |

## 3. Yerel kurulum (geliştirme)

```bash
cd backend/config
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env oluşturun (§2 tablosu); PostgreSQL'de veritabanı + kullanıcı hazır olmalı
python manage.py migrate
python manage.py seed_role_permissions      # rol -> permission matrisi (idempotent)
python manage.py bootstrap_platform --help  # platform firması + firmasız kullanıcı backfill
python manage.py createsuperuser            # ADR-0003-02: kullanıcı firmasız olamaz → platform firmasına bağlayın
python manage.py runserver
```

Geliştirme verisi için yönetim komutları (otomatik liste: [MASTER](MASTER.md) §2.7): `seed_tanimlar`,
`seed_fiyat_gruplari`, `seed_urunler`. Atama denetimi (salt okunur): `audit_user_assignments`.

### 3.1 Next.js iskelet (NX-FE)

```bash
# Django .env: CSRF_TRUSTED_ORIGINS=http://localhost:3000
cd frontend
cp .env.example .env.local   # DJANGO_ORIGIN=http://127.0.0.1:8000
npm install
npm run dev                  # http://localhost:3000 → /api/v1 rewrite
```

Ayrıntı: [`frontend/README.md`](../frontend/README.md).

## 4. Test ve kontrol

CI ile aynı paket listesi (`.github/workflows/ci.yml`):

```bash
cd backend/config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test \
  firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests \
  stok.tests siparis.tests finans.tests kalite.tests lojistik.tests \
  belgeler.tests api.tests \
  --verbosity=1 --keepdb
python ../../scripts/docs_sync.py --check
```

Odaklı örnekler:

```bash
python manage.py test api.tests.test_security_f8_007 --keepdb
python manage.py test siparis.tests.test_buyer_ui_f4_062 --keepdb
# F9-010/011 testleri yalnız Kova B WIP diskteyse: test_buyer_dashboard_f9_010 (HEAD’te yok)
```

- **Yalnız `fiyatlama` (bare) çalıştırmayın** — `admin`/`models` import hatası riski; `fiyatlama.tests` kullanın (AGENTS).
- Eşzamanlılık/kalıcılık: `TransactionTestCase` + PostgreSQL (ADR-0007).
- Son full suite sonucu [MASTER](MASTER.md) §2.7’de elle tutulur; `docs_sync` test koşmaz.

## 5. Migration politikası

- **Üretimde `migrate` ürün sahibi onayı olmadan çalıştırılmaz** (AGENTS).
- Veri silerek `NOT NULL` yapılmaz; çok adımlı (ekle → doldur → NOT NULL → kaldır) ve geri dönüşü planlı migration yazılır.
- K-008 sözleşme çakışma kısıtı `btree_gist` uzantısı ister; yerelde doğrulandı. **DOĞRULANAMADI:** üretim hosting'inde
  `CREATE EXTENSION` yetkisi. Kurulamazsa ADR-0007 §2.3'teki servis kilidi yolu kullanılır.

## 6. Üretime çıkmadan önce (kontrol listesi)

Aşağıdaki maddeler kod/ayar okumasına dayanır; **henüz üretimde doğrulanmadı**.

| # | Kontrol | Durum (2026-11-09 kod okuması) |
|---|---------|-------------------------------|
| 1 | `DEBUG=False`; güçlü `SECRET_KEY`; `ALLOWED_HOSTS` dolu | Ayar mekanizması var; değerler ortama bağlı |
| 2 | `.env` repoda izlenmiyor; `.env.example` var; DB şifresi güçlü/rotasyonlu | `.env` ignore + example **UYGULANDI**; rotasyon prosedürü işletim sorumluluğu |
| 3 | Reverse proxy arkasında `SECURE_PROXY_SSL_HEADER` | Env ile açılır (`SECURE_PROXY_SSL_HEADER=True`); varsayılan kapalı |
| 4 | HSTS süresi | Varsayılan 3600 sn; kademeli artırın |
| 5 | API kimliği | `TokenAuthentication` + Basic (401) + Session **UYGULANDI** (SEC-001) |
| 6 | API throttle | anon/user throttle **UYGULANDI** |
| 7 | `collectstatic` (`STATIC_ROOT=staticfiles`) | Yapılacak |
| 8 | E-posta | Varsayılan console; SMTP backend verilmeli |
| 9 | Periyodik işler | `expire_stale_reservations` (F4-022); `process_outbox` (F4-090); `evaluate_kur_alerts` (CAP-ALERT); `sync_binance_kur` / `sync_tcmb_kur` (CAP-PIYASA); cron/systemd önerilir |
| 10 | Yedek ve geri yükleme provası | **DOĞRULANAMADI** (§7) |
| 11 | CI yeşil (test + `makemigrations --check` + `docs_sync --check`) | workflow + `scripts/docs_sync.py` **UYGULANDI** (OPS-001) |

## 7. Yedekleme ve geri yükleme (şablon — üretimde doğrulanacak)

```bash
# yedek (özel biçim, sıkıştırılmış)
pg_dump --format=custom --file=kuyumbank_$(date +%F).dump "$DATABASE_URL"
# geri yükleme (boş bir veritabanına)
pg_restore --clean --if-exists --no-owner --dbname="$TARGET_DB_URL" kuyumbank_YYYY-MM-DD.dump
```

Hosting seçilince: yedek sıklığı, saklama süresi, **geri yükleme provası** (en az çeyrek başına bir kez) ve sorumlu kişi bu bölüme yazılır.

## 8. Operasyon notları

- **Fail audit:** `record_audit_durable` ayrı DB bağlantısı (sidecar) açar; yoğun reddedilen istekte bağlantı sayısını izleyin (ADR-0006 O3).
  `domain_atomic()` içinde çağrılırsa `RuntimeError` verir — çağrı yazım bloğunun **dışında** olmalı.
- **Stok:** `StockBalance` doğrudan düzenlenmez; yalnız ledger servisi yazar. Rezervasyon expire yolu için F4-022 durumuna bakın ([BACKLOG](BACKLOG.md)).
- **Para:** yalnız `Decimal`; `float` yok. Quote/PriceLock/Movement değişmezdir (uygulama + DB trigger); düzeltme yeni kayıtla yapılır.
- **Kur / CAP-PIYASA / CAP-ALERT:** Sync: §11b. Alert: `python manage.py evaluate_kur_alerts [--now=ISO]`; admin `KurAlertKurali` (`manage_kur`). Stale’de alert yok. Manuel kur + LKG/banner (`kur_servisi`). Geçici örnek: kök `real_data/` (silinebilir).
- **Kör havuz:** alıcı yüzeylerinde tedarikçi kimliği ve iç maliyet görünmez; log/export eklerken bu kuralı koruyun.
- **request_id (F8-002):** `X-Request-ID` middleware; log satırında `request_id=…`. Secret alanları log `extra`/mesajına yazmayın (`config.logging_utils.redact_mapping`).

## 9. Secret yönetimi (F8-005)

| Madde | Kural |
|-------|--------|
| Repo | `.env` commit edilmez; yalnız `.env.example` (placeholder) |
| Rotasyon | `SECRET_KEY`, DB şifresi, `PAYMENT_WEBHOOK_SECRET` — olay sonrası + periyodik (işletim) |
| Dağıtım | Secret’lar host secret store / CI secrets; log/artifact’a yazılmaz |
| Kod | `env(...)`; hardcode yasak (AGENTS) |

## 10. Deploy / migrate (F8-008 — şablon)

Hosting henüz yok (**DOĞRULANAMADI**). Hedef sıra:

1. CI yeşil (`.github/workflows/ci.yml`: docs_sync, `check`, makemigrations, suite).
2. Bakım penceresi + DB yedek (§7).
3. Kod deploy (immutable artifact tercihen).
4. **`migrate` yalnız ürün sahibi onayı ile** (AGENTS); rollback planı (önceki dump).
5. `seed_role_permissions` (idempotent) gerekirse.
6. Smoke: `/api/v1/health/`, alıcı login, kritik quote→order yolu.
7. `X-Request-ID` + hata oranı izleme (Sentry planı §11).

## 11. Hata izleme (F8-003)

1. `sentry-sdk==2.69.1` pinli; `config/sentry_init.py` — `SENTRY_DSN` boşsa no-op.
2. `before_send` PII/secret scrub (`redact_mapping` / `scrub_message`).
3. Env: `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` (varsayılan 0).
4. Staging kabul: DSN set + bilerek 500 → event (ürün sahibi staging’de **DOĞRULANAMADI** bu oturumda).
5. Smoke test: `python manage.py test api.tests.test_sentry_f8_003 --keepdb`.

## 11b. CAP-PIYASA kur sync (ADR-0018)

Celery yok; cron + management command:

```text
python manage.py sync_binance_kur --username <manage_kur> --metal-kod AU [--xauusdt N --usdttry N --skip-capraz]
python manage.py sync_tcmb_kur --username <manage_kur> --pb USD --kur <TRY>
```

Stale feed → quote `hesap_girdisi.feed_health=FEED_STALE_LKG` + `feed_banner` (sessiz LKG yok).

```text
python manage.py evaluate_kur_alerts [--now=ISO]
python manage.py process_outbox
```

## 12. Yeni geliştirici testi

Temiz bir klonla, yalnız bu doküman ve [MASTER](MASTER.md) ile şunlar yardımsız yapılabilmeli:

1. §3 adımlarıyla çalışan yerel ortam (admin'e giriş).
2. §4'teki tam test suite'in PostgreSQL'de koşması.
3. `python scripts/docs_sync.py --check` → `docs senkron: OK`.
4. Bir domain akışı için ilgili ADR ve servis dosyasını bulabilme (MASTER §2.5 + [decisions](decisions/README.md)).
5. F8-007 smoke: `python manage.py test api.tests.test_security_f8_007 --keepdb`.

Takıldığı adım, bu dokümanın eksik olduğu yerdir; düzeltilir.
