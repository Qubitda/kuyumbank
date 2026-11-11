"""PRE-005 + API-B2 — Checkout POST (Idempotency-Key)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsBuyerCommerceWrite
from api.throttles import BuyerRateThrottle
from siparis.models import CheckoutAttempt
from siparis.services import checkout_servisi


class CheckoutCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/checkouts/ — sepet → CheckoutAttempt; key zorunlu."""

    permission_classes = [IsBuyerCommerceWrite]
    throttle_classes = [BuyerRateThrottle]

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
            raise_drf(exc)

        body = {
            "id": result.attempt.pk,
            "durum": result.attempt.durum,
            "idempotency_key": result.attempt.idempotency_key,
            "line_count": len(result.lines),
            "allowed_actions": (
                ["create_order"]
                if result.attempt.durum == CheckoutAttempt.Durum.BASARILI
                else []
            ),
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
