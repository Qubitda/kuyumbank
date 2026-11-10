"""API-B2 — sipariş oluştur / iptal / reorder. ADR-0019 commerce W; OL-2 ops iptal yok."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import HasOrderObjectAccess, IsBuyerCommerceWrite
from api.presenters.buyer import BuyerCartPresenter, BuyerOrderPresenter
from api.throttles import BuyerRateThrottle
from siparis.models import CheckoutAttempt
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor
from siparis.services import order_servisi, reorder_servisi


class OrderFromCheckoutView(IdempotencyMixin, APIView):
    """POST /api/v1/orders/from-checkout/ — {checkout_id}."""

    permission_classes = [IsBuyerCommerceWrite]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            checkout_id = int(request.data.get("checkout_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"checkout_id": "Geçersiz."}) from exc
        attempt = CheckoutAttempt.objects.filter(
            pk=checkout_id, alici_firma_id=request.user.firma_id
        ).first()
        if attempt is None:
            raise NotFound(detail="Checkout bulunamadı.")
        try:
            order = order_servisi.olustur_from_checkout(
                actor=request.user, checkout_attempt=attempt
            )
        except DjangoValidationError as exc:
            raise_drf(exc)
        body = BuyerOrderPresenter(order)
        return self.idempotency_commit(
            request, Response(body, status=status.HTTP_201_CREATED)
        )


class OrderCancelView(IdempotencyMixin, APIView):
    """POST /api/v1/orders/<pk>/cancel/ — yalnız alıcı commerce W (OL-2)."""

    permission_classes = [IsBuyerCommerceWrite, HasOrderObjectAccess]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        self.check_object_permissions(request, order)
        try:
            order = order_servisi.iptal_siparis(actor=request.user, order=order)
        except DjangoValidationError as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request, Response(BuyerOrderPresenter(order))
        )


class OrderReorderView(IdempotencyMixin, APIView):
    """POST /api/v1/orders/<pk>/reorder/ — {replace_cart?: bool}."""

    permission_classes = [IsBuyerCommerceWrite, HasOrderObjectAccess]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        self.check_object_permissions(request, order)
        replace = request.data.get("replace_cart", True)
        if isinstance(replace, str):
            replace = replace.lower() not in ("0", "false", "no")
        try:
            cart = reorder_servisi.sepete_aktar(
                actor=request.user,
                order=order,
                replace_cart=bool(replace),
            )
        except DjangoValidationError as exc:
            raise_drf(exc)
        body = {
            "order_id": order.pk,
            "cart": BuyerCartPresenter(cart),
        }
        return self.idempotency_commit(request, Response(body))
