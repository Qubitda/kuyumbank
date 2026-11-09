"""HTTP Idempotency-Key kayıt / çakışma (PRE-005 + API-B1 TTL)."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import IdempotencyRecord

HEADER = "Idempotency-Key"


def ttl_seconds() -> int:
    return int(getattr(settings, "IDEMPOTENCY_TTL_SECONDS", 86400))


def _cutoff():
    return timezone.now() - timedelta(seconds=ttl_seconds())


def require_key(request) -> str:
    key = getattr(request, "idempotency_key", None)
    if not key:
        raw = request.headers.get(HEADER) or ""
        key = raw.strip() or None
    if not key:
        raise ValidationError({"detail": f"{HEADER} zorunlu."})
    if len(key) > 128:
        raise ValidationError({"detail": f"{HEADER} en fazla 128 karakter."})
    return key


def storage_key(*, actor_id: int, client_key: str) -> str:
    """Y2: DB anahtarı firma+actor scoped (client key 128 sınırını aşmaz).

    Aynı kullanıcı + aynı client key → aynı storage key (retry).
    Farklı kullanıcı → farklı storage key (platform firma çakışması yok).
    """
    digest = hashlib.sha256(
        f"{int(actor_id)}\0{client_key}".encode("utf-8")
    ).hexdigest()
    return digest  # 64 hex ≤ 128


def request_hash(*, method: str, path: str, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.upper().encode("utf-8"))
    h.update(b"\0")
    h.update(path.encode("utf-8"))
    h.update(b"\0")
    h.update(body or b"")
    return h.hexdigest()


def _is_fresh(record: IdempotencyRecord) -> bool:
    created = getattr(record, "created_at", None)
    if created is None:
        return True
    return created >= _cutoff()


def lookup(*, firma_id: int, key: str) -> IdempotencyRecord | None:
    """`key` burada storage_key (actor-scoped) olmalı."""
    record = IdempotencyRecord.objects.filter(firma_id=firma_id, key=key).first()
    if record is None:
        return None
    if not _is_fresh(record):
        # Süresi dolmuş — yeni istek kabul; kayıt silinir (yeniden kullanılabilir key)
        IdempotencyRecord.objects.filter(pk=record.pk).delete()
        return None
    return record


def cached_response(record: IdempotencyRecord) -> Response:
    return Response(record.response_body, status=record.status_code)


def store(
    *,
    firma_id: int,
    key: str,
    method: str,
    path: str,
    request_hash_value: str,
    status_code: int,
    response_body: Any,
    actor=None,
) -> IdempotencyRecord:
    """Tamamlanmış yanıtı saklar; çakışmada mevcut (taze) kaydı döner.

    `key` storage_key (actor-scoped) olmalıdır.
    """
    body = response_body if isinstance(response_body, (dict, list)) else {"detail": response_body}
    payload = body if isinstance(body, dict) else {"data": body}

    def _create() -> IdempotencyRecord:
        return IdempotencyRecord.objects.create(
            firma_id=firma_id,
            key=key,
            method=method.upper(),
            path=path[:255],
            request_hash=request_hash_value,
            status_code=status_code,
            response_body=payload,
            olusturan=actor,
        )

    try:
        with transaction.atomic():
            return _create()
    except IntegrityError:
        existing = IdempotencyRecord.objects.filter(firma_id=firma_id, key=key).first()
        if existing is None:
            raise
        if not _is_fresh(existing):
            IdempotencyRecord.objects.filter(pk=existing.pk).delete()
            with transaction.atomic():
                return _create()
        return existing


def encode_response_data(response: Response) -> dict:
    data = response.data
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"items": data}
    try:
        return json.loads(json.dumps(data, default=str))
    except (TypeError, ValueError):
        return {"detail": str(data)}
