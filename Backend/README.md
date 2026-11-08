# Kuyumbank Backend

Django **6.1** modular monolith. Project package lives in `config/`.

## Requirements

- Python 3.12–3.14
- PostgreSQL
- Dependencies: `config/requirements.txt`

## Setup

```powershell
cd Backend\config
python -m pip install -r requirements.txt
copy .env.example .env
# Edit .env: SECRET_KEY, DB_*
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/

## Checks and tests

```powershell
cd Backend\config
python manage.py check
python manage.py test urunler.tests fiyatlama.tests.test_fiyat_hesaplama --verbosity=1
```

Prefer explicit test module paths (see `.cursor/skills/testing-quality/SKILL.md`).

## Apps

| App | Role |
|-----|------|
| `firmalar` | Firms and users |
| `tanimlar` | Metals, rates, channels |
| `urunler` | Catalog |
| `fiyatlama` | Contracts, offers, price math |

Agent rules: repo root `AGENTS.md`. Architecture: `docs/architecture/`.
