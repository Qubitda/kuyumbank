# Kuyumbank

Jewelry B2B commerce platform (Django modular monolith).

## Dokümantasyon (tek kaynak)

| Bilgi | Dosya |
|-------|--------|
| AI agent çalışma kuralları | [`AGENTS.md`](AGENTS.md) |
| Ürün / mimari / ADR / backlog / güncel durum | [`docs/KUYUMBANK_MASTER.md`](docs/KUYUMBANK_MASTER.md) |
| Kurulum, migrate, test, runserver | [`backend/README.md`](backend/README.md) |

`docs/` altında yalnız `KUYUMBANK_MASTER.md` tutulur. Dağınık faz raporu / ikinci yol haritası yok.

## Hızlı başlangıç

```powershell
cd backend\config
python -m pip install -r requirements.txt
copy .env.example .env
# .env: SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
python manage.py migrate
python manage.py seed_role_permissions
python manage.py bootstrap_platform
python manage.py seed_tanimlar
python manage.py createsuperuser
python manage.py runserver
```

Ayrıntı ve test komutları: [`backend/README.md`](backend/README.md).

## Teknoloji

- Python 3.12–3.14 · Django **6.1.2** · PostgreSQL · `psycopg`
- HTTP: Django Admin (`/admin/`) + ince PRE API (`/api/v1/`) — DRF 3.18.3
- Uygulamalar: `firmalar`, `tanimlar`, `urunler`, `fiyatlama`, `stok`, `siparis`, `api`

Güncel faz / sıradaki iş: master **§12**.