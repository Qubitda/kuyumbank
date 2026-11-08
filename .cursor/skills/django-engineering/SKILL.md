---
name: django-engineering
description: >-
  Kuyumbank Django 6.1 engineering standards for models, ORM, services,
  migrations, admin, and Decimal/transaction patterns. Use when implementing or
  reviewing backend/config Python, models, services, migrations, or admin.
---

# Django Engineering (Kuyumbank)

**Prepared for:** Django **6.1** · Python 3.12–3.14  
**Official docs (framework only — not a Kuyumbank skill):** [Django 6.1](https://docs.djangoproject.com/en/6.1/) · [Coding style](https://docs.djangoproject.com/en/6.1/internals/contributing/writing-code/coding-style/) · [Migrations](https://docs.djangoproject.com/en/6.1/topics/migrations/) · [Transactions](https://docs.djangoproject.com/en/6.1/topics/db/transactions/) · [Source](https://github.com/django/django)

This skill states **project** engineering rules. For framework behavior, read Django docs directly. Do not paste Django manuals here.

## Project layout

- Settings: `backend/config/config/settings.py`
- Apps: `firmalar`, `tanimlar`, `urunler`, `fiyatlama`, `stok` under `backend/config/` (`siparis` yok)
- Manage: `backend/config/manage.py`
- HTTP: yalnız admin (`config/urls.py`); DRF yok
- **Binding structure:** ADR-0004 — see `docs/KUYUMBANK_MASTER.md` §3 / §6

### ADR-0004 package layout (per app)

```text
<app>/
  models/          # one primary model per file; __init__.py re-exports
  services/        # writes + business rules
  selectors/       # reads / querysets (tenant-scoped reads live here)
  admin/           # ModelAdmin modules
  serializers/     # only when API exists
  views/           # thin HTTP only; only when API/UI views exist
  tests/           # split by topic (incl. tenant isolation)
  urls.py          # when the app exposes URLs
  apps.py
```

Do not create empty `views/` / `serializers/` “for later”. Do not mass-refactor WIP without explicit approval — new/touched code must follow ADR-0004.

## Rules

1. Use Django **public** APIs only. No private `_` internals, no custom mini-framework.
2. Keep views/admin/serializers thin. Business rules live in `services/`; reads in `selectors/` (ADR-0004).
3. Prefer ORM; avoid raw SQL unless justified. Prevent N+1 with `select_related` / `prefetch_related`.
4. Money and metal math: `decimal.Decimal` only — never `float`. Build Decimals from strings (`Decimal(str(x))`), not from floats. Monetary values carry an explicit currency code (ISO 4217); never add amounts of different currencies.
5. Multi-step writes that must succeed together: `transaction.atomic()`.
6. Concurrent stock/finance updates: `select_for_update()` on the correct row + conditional update + DB constraints; do not rely on read-check-write alone.
7. Integrity: prefer DB `constraints`, `unique`, `CheckConstraint`, `PROTECT` FKs where the business rule is absolute. For date-range overlap rules (e.g. active price contracts, K-008) prefer a PostgreSQL exclusion constraint; otherwise a locked service check.
8. Migrations: generate with Django; read the file before commit. Flag data-loss risk explicitly. Test the reverse migration on an empty DB. Never delete rows to satisfy a NOT NULL/unique constraint; the migration must fail safely instead. No production migrate without approval.
9. Validation has three layers: serializer/form (user-facing errors), service (workflow and cross-model rules), DB constraint (structural invariants). `Kullanici.save()` calls `full_clean()` for **all** users, including superusers (ADR-0003-02); do not spread that pattern to hot-path models blindly (see report K-017).
10. Do not add dependencies without need. Pin direct dependencies only in `backend/config/requirements.txt` (ADR-0002).
11. No secrets in code. Use env via existing `django-environ` pattern. `.env` never enters the repo or archives.
12. Admin and future API must call the **same** service functions for state changes.
13. No circular imports; preserve model/admin/test discovery when moving files.
14. Report every changed file and its responsibility in the phase output.

## Authorization, tenant scope and audit

15. Permission decisions use Django `has_perm` or the central permission wrapper backed by the role-permission matrix. No `if user.is_superuser: allow`, no scattered `if rol == ...` switches (ADR-0003).
16. Authorization and ownership checks run **before** entering the business `atomic` block.
17. Audit writes: a denied or failed attempt is recorded in its **own** transaction, independent of the business `atomic` (so it cannot roll back), and the exception is raised afterwards. A successful transition writes its audit row in the **same** `atomic` as the state change. Service tests must prove the failure audit row survives (use `TransactionTestCase`, or call the service outside the test's wrapping transaction).
18. Tenant-scoped reads go through selectors (e.g. `katalog_tenant`). Admin `get_queryset`, inline querysets and `formfield_for_foreignkey` must use the same selector; the client-supplied `firma_id` is never trusted.
19. Test tenant isolation on every surface separately: admin, services, selectors, related objects (ADR-0003-05). Critical integration and concurrency tests run on PostgreSQL, not SQLite.

## Anti-patterns

- Business status fields updated with ad-hoc `QuerySet.update` outside the owning service
- Dual sources of truth (e.g. two stock fields) without a single inventory model; never auto-sum conflicting stock values during migration
- Importing models as scripts without app context
- Leaving dead abstractions “for later”
- Audit rows written inside the same transaction that then raises
- Superuser used as a business permission shortcut
