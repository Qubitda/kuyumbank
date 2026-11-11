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
| `TRUSTED_PROXY_COUNT` | Hayır | `0` | Audit + login throttle XFF hop (proxy’de >0) |
| `SECURE_PROXY_SSL_HEADER` | Hayır | `False` | Proxy arkasında `True` |
| `LOG_LEVEL` | Hayır | `INFO` | F8-002 |
| `LOG_JSON` | Hayır | `False` | `True` → tek satır JSON + `request_id` |
| `DRF_THROTTLE_ANON/USER/BUYER/SUPPLIER/OPS` | Hayır | settings | F8-009; örn. `60/min` |
| `DRF_THROTTLE_LOGIN` / `LOGIN_THROTTLE_RATE` | Hayır | `10/min` | API + HTML login IP throttle |
| `LOGIN_THROTTLE_USERNAME_RATE` | Hayır | `20/min` | HTML login kullanıcı adı kovası |
| `API_BASIC_AUTH_ENABLED` | Hayır | `DEBUG` | Prod’da `False` (S2S = Token) |
| `DRF_THROTTLE_BASIC` | Hayır | `5/min` | Basic header IP limiti |
| `AUTH_TOKEN_TTL_SECONDS` | Hayır | `604800` | Token ömrü (7g); `purge_expired_tokens` |
| `PASSWORD_MIN_LENGTH` | Hayır | `12` | MinimumLengthValidator |
| `SESSION_COOKIE_AGE` | Hayır | `28800` | Mutlak oturum (8s) |
| `SESSION_IDLE_TIMEOUT` | Hayır | `1800` | Boşta kalma (30 dk); 0=kapalı |
| `IDEMPOTENCY_TTL_SECONDS` | Hayır | `86400` | Idempotency-Key saklama; `purge_idempotency_records` |
| `IDEMPOTENCY_LOCK_WAIT_SECONDS` | Hayır | `5` | `pg_try_advisory_lock` bekleme tavanı |
| `CONN_MAX_AGE` | Hayır | `60` | PG bağlantı yeniden kullanımı (sn) |
| `CACHE_BACKEND` / `CACHE_LOCATION` | Hayır | locmem | Prod multi-worker: db/redis + `createcachetable` |
| `PAYMENT_FAKE_FORCE_FAIL` | Hayır | `False` | Fake ödeme negatif test |
| `CARRIER_FAKE_FORCE_FAIL` | Hayır | `False` | Fake kargo negatif test |
| `SENTRY_DSN` | Hayır | boş | F8-003; boşsa SDK no-op (`sentry-sdk==2.69.1`) |
| `SENTRY_ENVIRONMENT` | Hayır | `development` | F8-003 |
| `API_DOCS_PUBLIC` | Hayır | `False` | `True` → Swagger/ReDoc/schema anon (yalnız kontrollü staging) |
| `SENTRY_TRACES_SAMPLE_RATE` | Hayır | `0.0` | F8-003; düşük başla |
| `PAYMENT_PROVIDER` | Hayır | `fake` | Canlı banka yok |
| `PAYMENT_WEBHOOK_SECRET` | Prod webhook için | boş | Boşsa webhook 401 (fail-closed) |
| `PAYMENT_WEBHOOK_REQUIRE_HMAC` | Hayır | `True` | Timestamp + Signature zorunlu |
| `PAYMENT_WEBHOOK_REPLAY_SECONDS` | Hayır | `300` | Replay penceresi |
| `PAYMENT_WEBHOOK_IP_ALLOWLIST` | Hayır | boş | CIDR/IP; boş=kapalı |
| `DRF_THROTTLE_WEBHOOK` | Hayır | `120/min` | Webhook anon throttle |
| `CARRIER_PROVIDER` | Hayır | `fake` | Canlı kargo yok |
| `SHIPMENT_POD_REQUIRED` | Hayır | `False` | POD gate |
| `QC_GRAM_TOLERANCE_PCT` / `_ABS` | Hayır | `0.50` / `0` | F6-011 |
| `HAS_POSITION_LIMIT` | Hayır | `0` | 0 = kapalı |
| `SUPPLIER_ACCRUAL_VADE_GUN` | Hayır | `0` | F5-022 |
| `CRM_SYNC_ENABLED` | Hayır | `False` | F7 opt-in |
| `CSRF_TRUSTED_ORIGINS` | Next yerel için | `[]` | örn. `http://localhost:3000` (NX-FE aynı-origin rewrite) |
| `SESSION_COOKIE_DOMAIN` / `CSRF_COOKIE_DOMAIN` | Hayır | boş | Boş = host-only; prod proxy’de gerekirse |

## 3. Yerel kurulum (geliştirme)

Tek venv: **`backend/.venv`** (`config/` altında oluşturma).

```bash
cd backend
python3.14 -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -r config/requirements.txt
cd config
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
  belgeler.tests piyasa.tests api.tests \
  --verbosity=1 --keepdb
python ../../scripts/docs_sync.py --check
```

Periyodik temizlik (cron önerisi):

```bash
python manage.py purge_idempotency_records
python manage.py purge_expired_tokens
python manage.py clearsessions
# Çoklu worker throttle için paylaşımlı cache:
# CACHE_BACKEND=django.core.cache.backends.db.DatabaseCache
# CACHE_LOCATION=kuyumbank_cache
# python manage.py createcachetable
```


Odaklı örnekler:

```bash
python manage.py test api.tests.test_security_f8_007 --keepdb
python manage.py test api.tests.test_api_b2_buyer_commerce --keepdb
# F9 HTML UI testleri silindi (ADR-0029); dashboard/katalog: /api/v1/me/dashboard/ + /api/v1/catalog/
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
| 9 | Periyodik işler | `expire_stale_reservations` (F4-022); `process_outbox` (F4-090); `process_email_queue` (ADR-0027); `evaluate_kur_alerts` (CAP-ALERT); `sync_binance_kur` / `sync_tcmb_kur` (CAP-PIYASA); `purge_idempotency_records`; `purge_expired_tokens`; `clearsessions`; cron/systemd önerilir |
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
- **Para:** yalnız `Decimal`; `float` yok. Quote/PriceLock **uygulama + DB trigger**; `LedgerEntry` trigger + CheckConstraint. `StockMovement` / `StockBalance` / `OrderLine` snapshot: uygulama immutability (+ Movement QuerySet ban); **DB trigger yok** — ham SQL/`bulk_*` riski bilinçli. ATP: `reserved+blocked ≤ on_hand` CheckConstraint.
- **Idempotency kilit:** `pg_try_advisory_lock` + `IDEMPOTENCY_LOCK_WAIT_SECONDS` (varsayılan 5s). Session-level; PgBouncer **transaction** modunda kullanmayın.
- **CONN_MAX_AGE:** varsayılan 60s (env ile). Prod cache: LocMem yasak uyarısı (`kuyumbank.W001`); `CACHE_BACKEND=db` + `createcachetable`.
- **Auth:** Admin login IP (`TRUSTED_PROXY_COUNT`) + username throttle; API login DRF throttle; Basic varsayılan yalnız `DEBUG`; Token TTL 7g + `purge_expired_tokens`; session idle 30 dk. Şifre/invite/verify: `/api/v1/auth/…`. Login: firma `aktif` + `onay_durumu=onayli` (platform hariç). **MFA:** `MFA_ENFORCE_PLATFORM=1` → platform e-posta OTP; act-as MFA gerektirir. Prod: `createcachetable`; fake: `ALLOW_FAKE_PROVIDERS=1`.
- **Webhook:** `X-Webhook-Timestamp` + `X-Webhook-Signature` (HMAC-SHA256 of `ts.body`); replay penceresi; opsiyonel IP allow-list.
- **Kur / CAP-PIYASA / CAP-ALERT:** Sync: §11b. Alert: `python manage.py evaluate_kur_alerts [--now=ISO]`; admin `KurAlertKurali` (`manage_kur`). Stale’de alert yok. Manuel kur + LKG/banner (`kur_servisi`). GoldXT `real_data/` kaldırıldı (ADR-0018 §GoldXT).
- **CAP-PANO (ADR-0020/0022):** Admin → Piyasa ürünleri (`manage_piyasa`); **Piyasa marj politikası** (global TL|%); **Piyasa kar politikası**; Darphane işçilik; listede baz alış/satış; **Kar yardımcısı** (pano kodu veya metal+ayar, birimli kesinti). Seed: `python manage.py seed_piyasa`. Servis: `baz_fiyat` / `pano_ozeti` / `cozumle_islem_birim_fiyati(PANO|MANUEL)` / `darphane_iscilik_listesi`.
- **CAP-MAHSUP-HTTP (ADR-0023):** `POST /api/v1/returns/{id}/mahsup/` (`finans.post_ledger`); approve gövde `{"mahsup": true}` (post_ledger yoksa 403). Ödeme iadesi yok (U-004).
- **CAP-PANO-PP9 (ADR-0024):** İç işlem `quote_from_islem_fiyati(kaynak=PANO|MANUEL, …)` → PriceQuote; sonra alıcı `lock_quote`. HTTP yok.
- **CAP-PANO-v2.1 (ADR-0025):** Ürün `olcek` GRAM|ONS|KG + `cikti_pb` TRY|USD; USD satırlar için taze USDTRY (`resolve_doviz_kuru`).
- **CAP-RAPOR-HTTP (ADR-0026):** `GET /api/v1/reports/orders/`, `/reports/buyer-behavior/`, `/ops/anomalies/ciro/?esik_ciro=`.
- **FE:** `cd frontend && npm run generate:api` → `lib/api/schema.d.ts`. Kapı: [API_READINESS](API_READINESS.md) **FRONTEND READY**.
- **CAP-ACTAS (ADR-0021) + ADR-0029:** `seed_demo_portals` → `demo_alici` / `demo_tedarikci`. Ürün yüzeyi: `/api/v1/` (HTML portal yok). Act-as: Admin aksiyon veya `POST /api/v1/act-as/start/` (`user_id`); stop: `POST /api/v1/act-as/stop/` veya `/act-as/stop/`. `FRONTEND_PORTAL_BASE_URL` doluysa redirect FE. Yetki: `firmalar.act_as_user`.
- **Kör havuz:** alıcı yüzeylerinde tedarikçi kimliği ve iç maliyet görünmez; log/export eklerken bu kuralı koruyun.
- **request_id (F8-002):** `X-Request-ID` middleware; log satırında `request_id=…`. Secret alanları log `extra`/mesajına yazmayın (`config.logging_utils.redact_mapping`).
- **API docs:** `/api/docs/` (Swagger), `/api/redoc/`, `/api/schema/` — `DEBUG` veya `API_DOCS_PUBLIC`; prod’da staff/platform. CI: `export_openapi.py --check` + `lint_openapi.py`.

## 9. Secret yönetimi (F8-005)

| Madde | Kural |
|-------|--------|
| Repo | `.env` commit edilmez; yalnız `.env.example` (placeholder) |
| Zip/arşiv sızıntısı | `backend/config/.env` zip’e girmemelidir. Sızdıysa: `SECRET_KEY` + DB şifresi + varsa token/SMTP **rotasyon** (değerleri dokümana yazma); zip’i imha et; git history’de yoksa yine de sırları değiştir |
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
6. Smoke: `/api/v1/health/` (liveness), `/api/v1/ready/` (DB), alıcı login, kritik quote→order yolu.
7. NX-FE handoff: [FRONTEND_HANDOFF](FRONTEND_HANDOFF.md).
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
python manage.py process_email_queue [--limit=100]
python manage.py seed_email_templates
```

## 11c. Bildirim outbox + e-posta kuyruğu (ADR-0027 **Kabul**)

Celery yok. Sıra zorunlu: önce outbox (domain event → `EmailDelivery`), sonra SMTP kuyruğu.

```text
# her 1–5 dk (cron / systemd timer)
cd /path/to/backend/config
python manage.py process_outbox
python manage.py process_email_queue --limit=100
```

Örnek cron (Linux):

```cron
*/2 * * * * cd /path/to/backend/config && /path/to/venv/bin/python manage.py process_outbox >>/var/log/kuyumbank-outbox.log 2>&1
*/2 * * * * cd /path/to/backend/config && /path/to/venv/bin/python manage.py process_email_queue --limit=100 >>/var/log/kuyumbank-email.log 2>&1
```

Windows Task Scheduler: aynı iki komutu 2 dk aralıkla, çalışma dizini `backend/config`.

E-posta: outbox handler `EmailDelivery` üretir; SMTP `process_email_queue` ile gider. DB SMTP boşsa Django `EMAIL_*` / console. İlk kurulumda bir kez: `seed_email_templates` + `seed_role_permissions` (bildirim perm’leri).

## 11d. Sandbox soft-launch (yol A) — checklist

Hedef: Admin + API + mevcut `/buyer` `/ops`; **gerçek banka/kargo yok**; Next portal sonra.

```text
# Ortam (değerleri loglama)
# DEBUG=False (veya lokal sandbox True)
# ALLOW_FAKE_PROVIDERS=1          # yol A bilinçli
# MFA_ENFORCE_PLATFORM=1          # platform/act-as OTP
# PASSWORD_RESET_BASE_URL=https://...
# INVITE_TTL_HOURS=72
# EMAIL_VERIFY_REQUIRED_FOR_WRITE=0   # IE-3; 1 → buyer yazma için e-posta doğrulama
# EMAIL_BACKEND=SMTP… (console yalnız demo)
# CACHE_BACKEND=DatabaseCache + CACHE_LOCATION=kuyumbank_cache

python manage.py createcachetable
python manage.py seed_role_permissions
python manage.py soft_launch_check --allow-fake [--require-mfa] [--strict]
python manage.py process_outbox
python manage.py process_email_queue --limit=50
```

Davet/doğrulama (ADR-0028 Taslak): `POST /api/v1/auth/invites/create|accept/` + `email-verify/`; link tabanı `PASSWORD_RESET_BASE_URL`.  
Cron: §11c. Yedek: §7 (`pg_dump` en az bir kez). Secret rotasyonu zip sızıntısı olduysa §9.  
Yol B (gerçek ödeme/kargo): ayrı talimat + ADR; `ALLOW_FAKE_PROVIDERS=0`.

## 12. Yeni geliştirici testi

Temiz bir klonla, yalnız bu doküman ve [MASTER](MASTER.md) ile şunlar yardımsız yapılabilmeli:

1. §3 adımlarıyla çalışan yerel ortam (admin'e giriş).
2. §4'teki tam test suite'in PostgreSQL'de koşması.
3. `python scripts/docs_sync.py --check` → `docs senkron: OK`.
4. Bir domain akışı için ilgili ADR ve servis dosyasını bulabilme (MASTER §2.5 + [decisions](decisions/README.md)).
5. F8-007 smoke: `python manage.py test api.tests.test_security_f8_007 --keepdb`.

Takıldığı adım, bu dokümanın eksik olduğu yerdir; düzeltilir.
