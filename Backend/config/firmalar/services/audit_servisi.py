"""Kritik işlem audit kayıtları (ADR-0003, Faz 1.1 / ADR-0006 O3).

Başarısız deneme audit'i, domain yazım atomic'inin DIŞINDA yazılmalıdır.
Başarılı audit, ilgili yazımla aynı atomic içinde kalır.

Dış `transaction.atomic` içinde fail audit: ayrı DB bağlantısı ile yazılır
(parent rollback kaydı silmez).
"""

import contextvars
import json
from contextlib import contextmanager

from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from django.utils import timezone

from ..models.audit_olay import AuditOlay

_in_domain_atomic: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "kuyumbank_domain_atomic", default=False
)


@contextmanager
def domain_atomic():
    """Ürün/teklif yazım transaction'ı — fail audit bu bloğun dışında olmalı."""
    token = _in_domain_atomic.set(True)
    try:
        with transaction.atomic():
            yield
    finally:
        _in_domain_atomic.reset(token)


def record_audit(
    *,
    actor,
    action: str,
    entity_type: str = "",
    entity_id: str = "",
    success: bool = True,
    detail: dict | None = None,
    reason: str = "",
) -> AuditOlay:
    return AuditOlay.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        actor_firma=getattr(actor, "firma", None) if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        success=success,
        detail=detail or {},
        reason=reason or "",
    )


def _insert_audit_sidecar(**kwargs) -> AuditOlay:
    """Parent atomic rollback'inden bağımsız audit yazımı (ayrı bağlantı)."""
    alias = router.db_for_write(AuditOlay) or DEFAULT_DB_ALIAS
    table = AuditOlay._meta.db_table
    actor = kwargs.get("actor")
    actor_id = getattr(actor, "pk", None) if actor else None
    firma = getattr(actor, "firma", None) if actor else None
    firma_id = getattr(firma, "pk", None) if firma else None
    detail = kwargs.get("detail") or {}
    created = timezone.now()

    conn = connections.create_connection(alias)
    try:
        conn.ensure_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table}
                    (actor_id, actor_firma_id, action, entity_type, entity_id,
                     success, detail, reason, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                RETURNING id
                """,
                [
                    actor_id,
                    firma_id,
                    kwargs["action"],
                    kwargs.get("entity_type") or "",
                    str(kwargs.get("entity_id") or ""),
                    bool(kwargs.get("success", True)),
                    json.dumps(detail),
                    kwargs.get("reason") or "",
                    created,
                ],
            )
            new_id = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    return AuditOlay.objects.get(pk=new_id)


def record_audit_durable(**kwargs) -> AuditOlay:
    """Fail audit — domain_atomic içinde yasak; dış atomic'te sidecar yazar.

    Sidecar, commit edilmemiş actor FK'sinde (Django TestCase) IntegrityError
    verebilir; bu durumda aynı bağlantıya düşülür (test görünürlüğü korunur,
    production'da actor zaten commit'lidir → sidecar kalıcıdır). ADR-0006 O3.
    """
    if _in_domain_atomic.get():
        raise RuntimeError(
            "record_audit_durable: domain_atomic() içinde çağrılamaz "
            "(rollback fail audit'i siler). Çağrıyı domain yazım bloğunun "
            "DIŞINA alın."
        )
    conn = transaction.get_connection()
    if conn.in_atomic_block:
        from django.db import IntegrityError

        try:
            return _insert_audit_sidecar(**kwargs)
        except IntegrityError:
            return record_audit(**kwargs)
    return record_audit(**kwargs)
