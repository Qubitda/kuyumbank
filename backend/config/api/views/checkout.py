"""PRE-005 — Checkout POST (Idempotency-Key örneği)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from siparis.services import checkout_servisi


class CheckoutCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/checkouts/ — sepet → CheckoutAttempt; key zorunlu."""

    permission_classes = [IsAuthenticatedWithFirma]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached

        key = request._idempotency["key"]
        try:
            result = checkout_servisi.checkout(
                actor=request.user, idempotency_key=key
            )
        except DjangoValidationError as exc:
            messages = getattr(exc, "messages", None) or [str(exc)]
            response = Response(
                {"detail": messages[0] if len(messages) == 1 else messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
            return self.idempotency_commit(request, response)
        except ValidationError as exc:
            response = Response(
                exc.detail if hasattr(exc, "detail") else {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
            return self.idempotency_commit(request, response)

        body = {
            "id": result.attempt.pk,
            "durum": result.attempt.durum,
            "idempotency_key": result.attempt.idempotency_key,
            "line_count": len(result.lines),
            "lines": [
                {
                    "cart_line_id": ln.cart_line_id,
                    "lock_id": ln.lock_id,
                    "reservation_id": ln.reservation_id,
                    "miktar": str(ln.miktar),
                    "birim": ln.birim,
                }
                for ln in result.lines
            ],
        }
        response = Response(body, status=status.HTTP_201_CREATED)
        return self.idempotency_commit(request, response)
