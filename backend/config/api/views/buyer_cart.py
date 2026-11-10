"""API-B2 — buyer sepet yazma (mevcut cart_servisi). ADR-0019 commerce W."""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import (
    IsBuyerCommerceRead,
    IsBuyerCommerceWrite,
    can_buyer_commerce_write,
)
from api.presenters.buyer import BuyerCartLinePresenter, BuyerCartPresenter
from api.throttles import BuyerRateThrottle
from fiyatlama.selectors.buyer_quote import BuyerQuoteNotFound, get_quote_for_actor
from siparis.models import CartLine
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor
from siparis.services import cart_servisi


def _get_own_line(user, line_id: int) -> CartLine:
    try:
        cart = get_cart_for_actor(user, cart_id=None)
    except CartNotFound as exc:
        raise NotFound(detail="Sepet bulunamadı.") from exc
    line = CartLine.objects.filter(pk=line_id, cart=cart).select_related(
        "price_quote"
    ).first()
    if line is None:
        raise NotFound(detail="Sepet satırı bulunamadı.")
    return line


class CartMineView(APIView):
    """GET /api/v1/carts/me/ — yazma rolünde yoksa oluştur; salt okuma yalnızca mevcut."""

    permission_classes = [IsBuyerCommerceRead]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            if can_buyer_commerce_write(request.user):
                cart = cart_servisi.al_veya_olustur_sepet(actor=request.user)
            else:
                cart = get_cart_for_actor(request.user, cart_id=None)
        except CartNotFound as exc:
            raise NotFound(detail="Sepet bulunamadı.") from exc
        except Exception as exc:
            raise_drf(exc)
        return Response(BuyerCartPresenter(cart))


class CartLineCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/carts/me/lines/ — {quote_id, miktar}."""

    permission_classes = [IsBuyerCommerceWrite]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            quote_id = int(request.data.get("quote_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"quote_id": "Geçersiz."}) from exc
        try:
            miktar = Decimal(str(request.data.get("miktar", "")))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"miktar": "Geçersiz miktar."}) from exc
        try:
            quote = get_quote_for_actor(request.user, quote_id)
            line = cart_servisi.satir_ekle(
                actor=request.user, price_quote=quote, miktar=miktar
            )
        except BuyerQuoteNotFound as exc:
            raise NotFound(detail="Quote bulunamadı.") from exc
        except DjangoValidationError as exc:
            raise_drf(exc)
        cart = line.cart
        body = {
            "line": BuyerCartLinePresenter(line),
            "cart": BuyerCartPresenter(cart),
        }
        return self.idempotency_commit(
            request, Response(body, status=status.HTTP_201_CREATED)
        )


class CartLineDetailView(IdempotencyMixin, APIView):
    """PATCH/DELETE /api/v1/carts/me/lines/<id>/."""

    permission_classes = [IsBuyerCommerceWrite]
    throttle_classes = [BuyerRateThrottle]

    def patch(self, request, line_id: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        line = _get_own_line(request.user, line_id)
        try:
            miktar = Decimal(str(request.data.get("miktar", "")))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"miktar": "Geçersiz miktar."}) from exc
        try:
            line = cart_servisi.satir_guncelle_miktar(
                actor=request.user, line=line, miktar=miktar
            )
        except Exception as exc:
            raise_drf(exc)
        body = {
            "line": BuyerCartLinePresenter(line),
            "cart": BuyerCartPresenter(line.cart),
        }
        return self.idempotency_commit(request, Response(body))

    def delete(self, request, line_id: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        line = _get_own_line(request.user, line_id)
        cart = line.cart
        try:
            cart_servisi.satir_sil(actor=request.user, line=line)
        except Exception as exc:
            raise_drf(exc)
        cart.refresh_from_db()
        body = {"ok": True, "cart": BuyerCartPresenter(cart)}
        return self.idempotency_commit(request, Response(body))
