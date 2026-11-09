"""HTTP middleware — PRE-005 Idempotency-Key + F8-002 request_id."""

from __future__ import annotations

import uuid

from config.logging_utils import request_id_var


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
