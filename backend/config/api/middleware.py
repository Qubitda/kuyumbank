"""PRE-005 — Idempotency-Key iskeleti (header → request)."""


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
