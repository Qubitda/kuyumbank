---
name: testing-quality
description: >-
  Kuyumbank Django 6.1 testing standards: model, service, API, authorization,
  tenant isolation, edge cases, and concurrency tests on PostgreSQL. Use when
  writing, running, or reviewing tests under backend/config.
---

# Testing & Quality (Kuyumbank)

**Prepared for:** Django **6.1**  
**Official docs:** [Testing](https://docs.djangoproject.com/en/6.1/topics/testing/) · [TestCase](https://docs.djangoproject.com/en/6.1/topics/testing/tools/) · [Advanced testing](https://docs.djangoproject.com/en/6.1/topics/testing/advanced/)

## Hard rules

1. A task is not done until **relevant tests are written and executed**.
2. Never mark unrun tests as passed. If blocked, state the command and error (Ek kural A: DOĞRULANAMADI).
3. Use **PostgreSQL** for DB-backed tests (project default). Do not switch to SQLite to “make green” features that need constraints/`select_for_update`.
4. Prefer `SimpleTestCase` only for pure functions (e.g. `hesapla`).
5. Audit claims without file/line or command output are invalid.

## Required coverage by change type

| Change | Minimum tests |
|--------|----------------|
| Model / constraint | Model validation + DB constraint rejection |
| Service / state machine | Happy path + illegal transition + auth denial |
| Tenant-scoped read/write | Same-firm allow + cross-firm deny + platform path |
| Pricing | Decimal accuracy + ambiguity error + snapshot fields when quote exists |
| Stock / finance | Reservation TTL / oversell prevention; concurrency when risk exists |
| API (future) | Status codes, permission matrix, response masking (kör havuz) |

## How to run (this repo)

```text
cd backend/config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests --verbosity=1
```

Avoid bare `manage.py test fiyatlama` — discovery can import `admin`/`models` packages as tests. Prefer explicit `*.tests` modules.

Baseline (Dilim 3.6 sonrası, 2026-11-08): **254 tests OK** (`firmalar` + `urunler` + `fiyatlama` + `tanimlar`; PostgreSQL; +12 kör havuz/K-011).

## Migration review checklist

- Read generated migration file
- Note nullable→non-null, drop column, RenameField, RunPython data risk
- Call out irreversible steps in the task report

## Quality bar

- Fail loud on invariant violations
- No flaky time/sleep tests without freeze
- Do not assert on log secret contents
- Mirror rapor §12 acceptance themes when touching that domain
