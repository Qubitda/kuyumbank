"""HTTP middleware — PRE-005 Idempotency-Key + F8-002 request_id + B1 no-store."""

from __future__ import annotations

import uuid

from config.logging_utils import request_id_var

_NO_STORE_PREFIX = "/api/v1/"
_NO_STORE_SKIP = (
    "/api/v1/health/",
    "/api/v1/ready/",
    "/api/v1/schema/",
)


class IdempotencyKeyMiddleware:
    """`Idempotency-Key` başlığını `request.idempotency_key` olarak bağlar.

    Zorunluluk ve yanıt önbelleği view mixin / serviste (auth sonrası firma scope).
    """

    HEADER = "Idempotency-Key"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = request.headers.get(self.HEADER) or request.META.get(
            "HTTP_IDEMPOTENCY_KEY", ""
        )
        request.idempotency_key = (raw or "").strip() or None
        return self.get_response(request)


class RequestIdMiddleware:
    """F8-002 — `X-Request-ID` bağlar; yoksa üretir; yanıta yazar; log context."""

    HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = (
            request.headers.get(self.HEADER)
            or request.META.get("HTTP_X_REQUEST_ID", "")
            or ""
        ).strip()
        rid = (raw[:64] if raw else uuid.uuid4().hex)
        request.request_id = rid
        token = request_id_var.set(rid)
        try:
            response = self.get_response(request)
            response[self.HEADER] = rid
            return response
        finally:
            request_id_var.reset(token)


class ApiNoStoreMiddleware:
    """NX-10 — kimlikli API yanıtlarında Cache-Control: no-store."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path or ""
        if not path.startswith(_NO_STORE_PREFIX):
            return response
        if any(path.startswith(p) for p in _NO_STORE_SKIP):
            return response
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            response["Cache-Control"] = "no-store"
        return response
