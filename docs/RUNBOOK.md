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

## 4. Test ve kontrol

```bash
cd backend/config
python manage.py test firmalar urunler fiyatlama.tests tanimlar stok siparis api.tests --keepdb
python manage.py makemigrations --check --dry-run     # pending migration olmamalı
python ../../scripts/docs_sync.py --check             # doküman bayat mı / kırık link var mı
```


- Eşzamanlılık ve kalıcılık kanıtı gereken testler `TransactionTestCase` olmalıdır (ADR-0007 operasyon notu).
- Son suite koşusu sonucu [MASTER](MASTER.md) §2.7'de elle tutulur; script test koşmaz.

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
| 9 | Periyodik işler | `expire_stale_reservations` (F4-022); `process_outbox` (F4-090); cron/systemd önerilir |
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
- **Kör havuz:** alıcı yüzeylerinde tedarikçi kimliği ve iç maliyet görünmez; log/export eklerken bu kuralı koruyun.

## 9. Yeni geliştirici testi

Temiz bir klonla, yalnız bu doküman ve [MASTER](MASTER.md) ile şunlar yardımsız yapılabilmeli:

1. §3 adımlarıyla çalışan yerel ortam (admin'e giriş).
2. §4'teki tam test suite'in PostgreSQL'de koşması.
3. `python scripts/docs_sync.py --check` → `docs senkron: OK`.
4. Bir domain akışı için ilgili ADR ve servis dosyasını bulabilme (MASTER §2.5 + [decisions](decisions/README.md)).

Takıldığı adım, bu dokümanın eksik olduğu yerdir; düzeltilir.
