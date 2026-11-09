"""PRE-005 / B2 — Idempotent yazma; aynı firma+key PG'de serileştirilir."""

from __future__ import annotations

import hashlib

from django.db import connection
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.services import idempotency_servisi as idem


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "Idempotency-Key aynı ama istek gövdesi farklı."
    default_code = "idempotency_conflict"


def _advisory_lock_id(firma_id: int, key: str) -> int:
    digest = hashlib.sha256(f"{firma_id}\0{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF


class IdempotencyMixin:
    """Firma-scoped Idempotency-Key; eşzamanlı aynı key → tek işlem (PG advisory)."""

    _IDEMP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._idempotency_acquire(request)

    def finalize_response(self, request, response, *args, **kwargs):
        try:
            return super().finalize_response(request, response, *args, **kwargs)
        finally:
            self._idempotency_release(request)

    def handle_exception(self, exc):
        try:
            return super().handle_exception(exc)
        finally:
            self._idempotency_release(getattr(self, "request", None))

    def _idempotency_acquire(self, request) -> None:
        if request.method.upper() not in self._IDEMP_METHODS:
            return
        key = getattr(request, "idempotency_key", None) or (
            (request.headers.get("Idempotency-Key") or "").strip() or None
        )
        firma_id = getattr(getattr(request, "user", None), "firma_id", None)
        if not key or not firma_id:
            return
        lock_id = _advisory_lock_id(int(firma_id), key)
        cursor = connection.cursor()
        cursor.execute("SELECT pg_advisory_lock(%s)", [lock_id])
        request._idempotency_advisory = {"cursor": cursor, "lock_id": lock_id}

    def _idempotency_release(self, request) -> None:
        if request is None:
            return
        meta = getattr(request, "_idempotency_advisory", None)
        if not meta:
            return
        request._idempotency_advisory = None
        cursor = meta["cursor"]
        try:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [meta["lock_id"]])
        finally:
            cursor.close()

    def idempotency_begin(self, request) -> Response | None:
        """Önbellek hit → Response; aksi halde None (işleme devam)."""
        key = idem.require_key(request)
        firma_id = request.user.firma_id
        body = getattr(request, "body", b"") or b""
        path = request.path
        rh = idem.request_hash(method=request.method, path=path, body=body)
        existing = idem.lookup(firma_id=firma_id, key=key)
        if existing is not None:
            if existing.request_hash != rh:
                raise IdempotencyConflict()
            return idem.cached_response(existing)
        request._idempotency = {
            "key": key,
            "firma_id": firma_id,
            "path": path,
            "request_hash": rh,
            "method": request.method,
        }
        return None

    def idempotency_commit(self, request, response: Response) -> Response:
        meta = getattr(request, "_idempotency", None)
        if meta is None or response.status_code >= 500:
            return response
        idem.store(
            firma_id=meta["firma_id"],
            key=meta["key"],
            method=meta["method"],
            path=meta["path"],
            request_hash_value=meta["request_hash"],
            status_code=response.status_code,
            response_body=idem.encode_response_data(response),
            actor=getattr(request, "user", None),
        )
        return response
