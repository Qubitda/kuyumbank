"""API-B2 — PriceLock oluştur / oku. ADR-0019 commerce W."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsBuyerCommerceRead, IsBuyerCommerceWrite
from api.presenters.buyer import BuyerPriceLockPresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.models import PriceLock
from fiyatlama.selectors.buyer_quote import BuyerQuoteNotFound, get_quote_for_actor
from fiyatlama.selectors.tenant import scope_price_lock_queryset
from fiyatlama.services import pricing_service


def _get_lock(user, lock_id: int) -> PriceLock:
    qs = scope_price_lock_queryset(
        PriceLock.objects.select_related("quote"), user
    )
    lock = qs.filter(pk=lock_id).first()
    if lock is None:
        raise NotFound(detail="PriceLock bulunamadı.")
    return lock


class PriceLockCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/price-locks/ — {quote_id} (+ Idempotency-Key)."""

    permission_classes = [IsBuyerCommerceWrite]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        if can_view_all_tenants(request.user):
            raise PermissionDenied(
                detail="Ops on-behalf kilit için ayrı yüzey; alıcı oturumu kullanın."
            )
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            quote_id = int(request.data.get("quote_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"quote_id": "Geçersiz."}) from exc
        try:
            quote = get_quote_for_actor(request.user, quote_id)
            key = request._idempotency["key"]
            lock = pricing_service.lock_quote(
                quote, kullanici=request.user, idempotency_key=key
            )
        except BuyerQuoteNotFound as exc:
            raise NotFound(detail="Quote bulunamadı.") from exc
        except DjangoValidationError as exc:
            raise_drf(exc)
        body = BuyerPriceLockPresenter(lock)
        return self.idempotency_commit(
            request, Response(body, status=status.HTTP_201_CREATED)
        )


class PriceLockDetailView(APIView):
    """GET /api/v1/price-locks/<pk>/ — expires_at + server_now + gecerli."""

    permission_classes = [IsBuyerCommerceRead]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        lock = _get_lock(request.user, pk)
        return Response(BuyerPriceLockPresenter(lock))
