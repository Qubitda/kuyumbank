# Kuyumbank

Jewelry B2B commerce platform (Django modular monolith).

## Dokümantasyon (tek kaynak)

| Bilgi | Dosya |
|-------|--------|
| AI agent çalışma kuralları | [`AGENTS.md`](AGENTS.md) |
| Ürün / mimari / ADR / backlog / güncel durum | [`docs/MASTER.md`](docs/MASTER.md) |
| Kurulum, migrate, test, runserver | [`backend/README.md`](backend/README.md) |
| Next.js iskelet (NX-FE) | [`frontend/README.md`](frontend/README.md) |

Kanonik durum: `docs/MASTER.md` §2 + §12. Dağınık faz raporu / ikinci yol haritası yok.

## Hızlı başlangıç

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r config\requirements.txt
cd config
copy .env.example .env
# .env: SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
python manage.py migrate
python manage.py seed_role_permissions
python manage.py bootstrap_platform
python manage.py seed_tanimlar
python manage.py createsuperuser
python manage.py runserver
```

Ortam yolu ve ayrıntı: [`backend/README.md`](backend/README.md) → **Ortam kurulumu**.

## Teknoloji

- Python 3.12–3.14 · Django **6.1.2** · PostgreSQL · `psycopg`
- HTTP: Django Admin (`/admin/`) + `/api/v1/` (B1–B7) + `/buyer/` `/ops/` miras HTML — DRF 3.18.3
- Frontend: Next.js `frontend/` (NX-FE iskelet; aynı-origin API rewrite)
- Domain app’ler: `firmalar` … `kalite` + `api` (ADR-0004)

Güncel faz / sıradaki iş: master **§12**.