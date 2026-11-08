# Kuyumbank backend

Django **6.1** modular monolith. Project package: `config/`.

## Proje bağlamı

Tek kanonik doküman: repo kökünden [`docs/KUYUMBANK_MASTER.md`](../docs/KUYUMBANK_MASTER.md)  
Agent kuralları: [`AGENTS.md`](../AGENTS.md)

## Requirements

- Python 3.12–3.14
- PostgreSQL
- Dependencies: `config/requirements.txt`

## Setup

```powershell
cd backend\config
python -m pip install -r requirements.txt
copy .env.example .env
# Edit .env: SECRET_KEY, DB_*
python manage.py migrate
python manage.py seed_role_permissions
python manage.py bootstrap_platform
python manage.py seed_tanimlar
python manage.py createsuperuser
python manage.py runserver
```

Ops: `audit_user_assignments`. Admin: http://127.0.0.1:8000/admin/

## Checks and tests

```powershell
cd backend\config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests --verbosity=1
```

## Apps

| App | Role |
|-----|------|
| `firmalar` | Firms, users, RBAC, audit |
| `tanimlar` | Metals, FX/metal rates, channels |
| `urunler` | Catalog |
| `fiyatlama` | Offers, contracts, quote, PriceLock |

Phase status: see master §12 (3.7 PriceLock coded; Faz 4 not started).
