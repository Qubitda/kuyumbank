"""HTTP Idempotency-Key kayıt / çakışma (PRE-005)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import IdempotencyRecord

HEADER = "Idempotency-Key"


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


def request_hash(*, method: str, path: str, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.upper().encode("utf-8"))
    h.update(b"\0")
    h.update(path.encode("utf-8"))
    h.update(b"\0")
    h.update(body or b"")
    return h.hexdigest()


def lookup(*, firma_id: int, key: str) -> IdempotencyRecord | None:
    return IdempotencyRecord.objects.filter(firma_id=firma_id, key=key).first()


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
    """Başarılı tamamlanmış yanıtı saklar; çakışmada mevcut kaydı döner."""
    body = response_body if isinstance(response_body, (dict, list)) else {"detail": response_body}
    try:
        with transaction.atomic():
            return IdempotencyRecord.objects.create(
                firma_id=firma_id,
                key=key,
                method=method.upper(),
                path=path[:255],
                request_hash=request_hash_value,
                status_code=status_code,
                response_body=body if isinstance(body, dict) else {"data": body},
                olusturan=actor,
            )
    except IntegrityError:
        existing = lookup(firma_id=firma_id, key=key)
        if existing is None:
            raise
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
