---
name: multi-tenant-security
description: >-
  Kuyumbank multi-tenant firma isolation, RBAC, blind-pool (kör havuz) masking,
  and Django 6.1 security practices. Use when touching auth, permissions, firma
  scoping, API authorization, admin queryset filters, or sensitive data handling.
---

# Multi-Tenant Security (Kuyumbank)

**Prepared for:** Django **6.1**  
**Framework refs (not this skill):** [Security](https://docs.djangoproject.com/en/6.1/topics/security/) · [Auth](https://docs.djangoproject.com/en/6.1/topics/auth/) · [CSRF](https://docs.djangoproject.com/en/6.1/ref/csrf/)

Normative product rules: rapor K-002, K-003, K-005, §8. Deep audit: `docs/architecture/faz0-tenant-guvenlik-denetimi.md`.  
Approved Faz 1 decisions: `docs/decisions/ADR-0003-faz1-kimlik-rbac.md` (8 platform roles; firma NOT NULL; no silent superuser tenant bypass; K-004 ownership; distributed Meta.permissions; multi-surface isolation tests).  
Findings must use DOĞRULANDI / DOĞRULANAMADI / PLANLAMA BULGUSU with file/line or command evidence. Do not implement Faz 1 without explicit user go-ahead.

## Tenant model

- Every business user has exactly one `firma` (`firmalar.Kullanici`).
- Exactly one platform firm (`Firma.platform_mu` unique constraint).
- Default deny: if scope is unclear, deny.

## Mandatory rules

1. **Never trust** client-supplied `firma_id`, `tedarikci_id`, `alici_id`. Derive tenant from `request.user.firma_id` (or explicit platform permission).
2. Every query/service that returns firm data must apply tenant scope (or documented platform permission).
3. Out-of-scope object: prefer **404** over 403 when existence must stay hidden (rapor §6.1 / §12.1).
4. Platform power = explicit permission codes — not “is staff” alone. `is_superuser` is break-glass only (K-003); do not use it in normal business flows.
5. Role assignment only through `firmalar.services.rol_servisi.assign_user_role` (or successor). Keep Group sync consistent with `rol`.
6. Passive and API must share the same authorization checks for domain mutations (K-021).

## Kör havuz (blind pool)

| Actor | Must not see |
|-------|----------------|
| Buyer | Supplier identity, supplier SKU, cost, margin, offer IDs |
| Supplier | Buyer firm name/contact (except platform-controlled task logistics) |
| Platform | (sees all — audited) |

Do not expose supplier fields on buyer-facing serializers/admin inlines. Logs must not dump PII/finance beyond role need.

## Django security baseline (project)

- `SECRET_KEY`, DB password from env; `DEBUG=False` in production
- HTTPS + secure cookies + HSTS when not DEBUG (already in settings)
- CSRF middleware on; avoid `csrf_exempt` unless unavoidable
- No sensitive data in logs or error responses
- Future API: auth on every endpoint; throttle auth; CORS explicit

## Tests required for any tenant-touching change

- Same-firm allow / cross-firm deny
- Platform allow with permission / deny without
- Buyer cannot read supplier identity fields
- IDOR attempt with swapped PK returns 404/deny
