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
python manage.py seed_role_permissions
python manage.py bootstrap_platform
python manage.py seed_tanimlar
python manage.py createsuperuser
python manage.py runserver
```

Ops: `audit_user_assignments` (firma/rol tutarlılığı). Admin: http://127.0.0.1:8000/admin/

## Checks and tests

```powershell
cd Backend\config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests --verbosity=1
```

Prefer explicit test module paths (see `.cursor/skills/testing-quality/SKILL.md`).

## Apps

| App | Role |
|-----|------|
| `firmalar` | Firms, users, RBAC, audit |
| `tanimlar` | Metals, rates, channels |
| `urunler` | Catalog (platform ownership, approval) |
| `fiyatlama` | Offers (lifecycle/versioning), contracts, metal price math |

Phase status (code): Faz 1–2.1 done; Faz 3a dilim **3.1** (teklif yaşam döngüsü) done; quote/kur = ADR-0008 (Taslak).  
Agent rules: repo root `AGENTS.md`. Architecture: `docs/architecture/` (incl. `faz3-1-uygulama-raporu.md`).
