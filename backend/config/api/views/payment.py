"""B3 — PaymentIntent oluşturma (mevcut payment_servisi)."""

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.finance_ops import BuyerPaymentIntentPresenter
from api.throttles import BuyerRateThrottle
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from finans.services import payment_servisi
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor


class PaymentIntentCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/payments/intents/ — {order_id}; Idempotency-Key zorunlu."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order_id = int(request.data.get("order_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"order_id": "Geçersiz."}) from exc
        try:
            order = get_order_for_actor(request.user, order_id=order_id)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        key = (request.headers.get("Idempotency-Key") or "").strip()
        try:
            pi = payment_servisi.olustur_intent(
                actor=request.user,
                order=order,
                idempotency_key=key,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(
                BuyerPaymentIntentPresenter(pi),
                status=status.HTTP_201_CREATED,
            ),
        )
