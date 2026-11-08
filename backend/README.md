# Kuyumbank backend

Django **6.1** modular monolith. Project package lives in `config/`.

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

Ops: `audit_user_assignments` (firma/rol tutarlılığı). Admin: http://127.0.0.1:8000/admin/

## Checks and tests

```powershell
cd backend\config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests --verbosity=1
```

Prefer explicit test module paths (see `.cursor/skills/testing-quality/SKILL.md`).

## Apps

| App | Role |
|-----|------|
| `firmalar` | Firms, users, RBAC, audit |
| `tanimlar` | Metals, rate provider/policy (`kur_servisi`), channels (quote TTL) |
| `urunler` | Catalog (platform ownership, approval) |
| `fiyatlama` | Offers (lifecycle/versioning), contracts (K-007/K-008), metal price math |

Phase status (code): Faz 1–2.1 done; Faz 3a **3.1–3.2** done; Faz 3b Dilim **3.3–3.6** done (kur, fiyat, PriceQuote, kör havuz/K-011). Next: **3.7** PriceLock (talimatla).  
Agent rules: repo root `AGENTS.md`. Architecture: `docs/architecture/` (`mevcut-mimari.md`, `faz3-4-uygulama-raporu.md`).
