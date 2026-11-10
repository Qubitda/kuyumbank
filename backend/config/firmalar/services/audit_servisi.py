"""Kritik işlem audit kayıtları (ADR-0003, Faz 1.1 / ADR-0006 O3).

Başarısız deneme audit'i, domain yazım atomic'inin DIŞINDA yazılmalıdır.
Başarılı audit, ilgili yazımla aynı atomic içinde kalır.

Dış `transaction.atomic` içinde fail audit: ayrı DB bağlantısı ile yazılır
(parent rollback kaydı silmez).

ADR-0021 AA-9: act-as sırasında `actor` = gerçek operatör, `on_behalf_of` = hedef.
"""

import contextvars
import json
from contextlib import contextmanager

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from django.utils import timezone

from ..models.audit_olay import AuditOlay

_in_domain_atomic: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "kuyumbank_domain_atomic", default=False
)

# (real_actor, target) — ActAsMiddleware tarafından set edilir
_act_as_pair: contextvars.ContextVar[tuple | None] = contextvars.ContextVar(
    "kuyumbank_act_as_pair", default=None
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


@contextmanager
def act_as_audit_context(*, actor, target):
    """Act-as isteği süresince audit aktörünü gerçek operatöre bağlar."""
    token = _act_as_pair.set((actor, target))
    try:
        yield
    finally:
        _act_as_pair.reset(token)


def _resolve_audit_actors(actor, on_behalf_of=None):
    """Act-as aktifken actor→gerçek operatör, on_behalf_of→hedef (yoksa)."""
    pair = _act_as_pair.get()
    if pair is None:
        return actor, on_behalf_of
    real_actor, target = pair
    if on_behalf_of is None:
        on_behalf_of = target
    return real_actor, on_behalf_of


def client_ip(request) -> str | None:
    """İstek IP — TRUSTED_PROXY_COUNT kadar X-Forwarded-For sağdan güvenilir.

    TRUSTED_PROXY_COUNT=0 → yalnız REMOTE_ADDR (spoof'a karşı varsayılan).
    """
    if request is None:
        return None
    meta = getattr(request, "META", None) or {}
    remote = (meta.get("REMOTE_ADDR") or "").strip() or None
    trusted = int(getattr(settings, "TRUSTED_PROXY_COUNT", 0) or 0)
    if trusted <= 0:
        return remote
    forwarded = (meta.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if not forwarded:
        return remote
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if not parts:
        return remote
    # Sağdan trusted hop atla; kalan listenin sonu client
    idx = len(parts) - trusted - 1
    if idx < 0:
        return parts[0]
    return parts[idx]


def record_audit(
    *,
    actor,
    action: str,
    entity_type: str = "",
    entity_id: str = "",
    success: bool = True,
    detail: dict | None = None,
    reason: str = "",
    ip_address: str | None = None,
    changes: dict | None = None,
    on_behalf_of=None,
) -> AuditOlay:
    actor, on_behalf_of = _resolve_audit_actors(actor, on_behalf_of)
    return AuditOlay.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        on_behalf_of=(
            on_behalf_of if getattr(on_behalf_of, "pk", None) else None
        ),
        actor_firma=getattr(actor, "firma", None) if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        success=success,
        detail=detail or {},
        reason=reason or "",
        ip_address=ip_address or None,
        changes=changes or {},
    )


def _insert_audit_sidecar(**kwargs) -> AuditOlay:
    """Parent atomic rollback'inden bağımsız audit yazımı (ayrı bağlantı)."""
    alias = router.db_for_write(AuditOlay) or DEFAULT_DB_ALIAS
    table = AuditOlay._meta.db_table
    actor = kwargs.get("actor")
    on_behalf_of = kwargs.get("on_behalf_of")
    actor, on_behalf_of = _resolve_audit_actors(actor, on_behalf_of)
    actor_id = getattr(actor, "pk", None) if actor else None
    on_behalf_id = getattr(on_behalf_of, "pk", None) if on_behalf_of else None
    firma = getattr(actor, "firma", None) if actor else None
    firma_id = getattr(firma, "pk", None) if firma else None
    detail = kwargs.get("detail") or {}
    changes = kwargs.get("changes") or {}
    ip_address = kwargs.get("ip_address") or None
    created = timezone.now()

    conn = connections.create_connection(alias)
    try:
        conn.ensure_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table}
                    (actor_id, on_behalf_of_id, actor_firma_id, action, entity_type,
                     entity_id, success, detail, reason, ip_address, changes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s)
                RETURNING id
                """,
                [
                    actor_id,
                    on_behalf_id,
                    firma_id,
                    kwargs["action"],
                    kwargs.get("entity_type") or "",
                    str(kwargs.get("entity_id") or ""),
                    bool(kwargs.get("success", True)),
                    json.dumps(detail),
                    kwargs.get("reason") or "",
                    ip_address,
                    json.dumps(changes),
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
