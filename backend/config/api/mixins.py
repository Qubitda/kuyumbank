"""PRE-005 — Idempotent POST yardımcıları."""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.services import idempotency_servisi as idem


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "Idempotency-Key aynı ama istek gövdesi farklı."
    default_code = "idempotency_conflict"


class IdempotencyMixin:
    """Firma-scoped Idempotency-Key yardımcıları (POST örnek view'larda kullan).

    5xx saklanmaz. Auth + firma `permission_classes` ile gelmeli.
    """

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
