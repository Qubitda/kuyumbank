"""API-B2 — sipariş oluştur (checkout’tan), iptal, reorder."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerCartPresenter, BuyerOrderPresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import CheckoutAttempt
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor
from siparis.services import order_servisi, reorder_servisi


def _assert_buyer(user) -> None:
    if can_view_all_tenants(user):
        raise PermissionDenied(detail="Ops bu yazma uçlarını kullanamaz.")
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Yalnız alıcı.")


class OrderFromCheckoutView(IdempotencyMixin, APIView):
    """POST /api/v1/orders/from-checkout/ — {checkout_id}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        _assert_buyer(request.user)
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
    """POST /api/v1/orders/<pk>/cancel/."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        _assert_buyer(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        try:
            order = order_servisi.iptal_siparis(actor=request.user, order=order)
        except DjangoValidationError as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request, Response(BuyerOrderPresenter(order))
        )


class OrderReorderView(IdempotencyMixin, APIView):
    """POST /api/v1/orders/<pk>/reorder/ — {replace_cart?: bool}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        _assert_buyer(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
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
