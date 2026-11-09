"""API-B2 — buyer sepet yazma (mevcut cart_servisi)."""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerCartLinePresenter, BuyerCartPresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.selectors.buyer_quote import BuyerQuoteNotFound, get_quote_for_actor
from siparis.models import CartLine
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor
from siparis.services import cart_servisi


def _assert_buyer(user) -> None:
    if can_view_all_tenants(user):
        raise PermissionDenied(detail="Ops sepet yazamaz; alıcı oturumu kullanın.")
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Sepet yalnız alıcı içindir.")


def _get_own_line(user, line_id: int) -> CartLine:
    try:
        cart = get_cart_for_actor(user, cart_id=None)
    except CartNotFound as exc:
        raise NotFound(detail="Sepet bulunamadı.") from exc
    line = CartLine.objects.filter(pk=line_id, cart=cart).select_related("price_quote").first()
    if line is None:
        raise NotFound(detail="Sepet satırı bulunamadı.")
    return line


class CartMineView(APIView):
    """GET /api/v1/carts/me/ — yoksa oluştur."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer(request.user)
        try:
            cart = cart_servisi.al_veya_olustur_sepet(actor=request.user)
        except Exception as exc:
            raise_drf(exc)
        return Response(BuyerCartPresenter(cart))


class CartLineCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/carts/me/lines/ — {quote_id, miktar}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        _assert_buyer(request.user)
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

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def patch(self, request, line_id: int):
        _assert_buyer(request.user)
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
        _assert_buyer(request.user)
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
