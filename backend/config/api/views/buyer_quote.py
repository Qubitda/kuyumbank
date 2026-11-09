"""API-B2 — buyer quote oluştur / oku (pricing_service + buyer_quote selector)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerQuotePresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.selectors.buyer_quote import BuyerQuoteNotFound, get_quote_for_actor
from fiyatlama.services import pricing_service
from tanimlar.models import SatisKanali
from urunler.models import Varyant


def _assert_buyer(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Quote yalnız alıcı veya ops.")


class QuoteCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/quotes/ — {varyant_id, satis_kanali_id, para_birimi?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request):
        _assert_buyer(request.user)
        if can_view_all_tenants(request.user):
            raise PermissionDenied(detail="Ops quote üretemez; alıcı oturumu kullanın.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            varyant_id = int(request.data.get("varyant_id"))
            kanal_id = int(request.data.get("satis_kanali_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                detail={"varyant_id": "Zorunlu.", "satis_kanali_id": "Zorunlu."}
            ) from exc
        pb = (request.data.get("para_birimi") or "TRY").upper()
        varyant = (
            Varyant.objects.select_related("urun")
            .filter(pk=varyant_id)
            .first()
        )
        kanal = SatisKanali.objects.filter(pk=kanal_id).first()
        if varyant is None:
            raise NotFound(detail="Varyant bulunamadı.")
        if kanal is None:
            raise ValidationError(detail={"satis_kanali_id": "Kanal bulunamadı."})
        try:
            quote = pricing_service.quote(
                alici_firma=request.user.firma,
                satis_kanali=kanal,
                varyant=varyant,
                kullanici=request.user,
                para_birimi=pb,
            )
        except DjangoValidationError as exc:
            raise_drf(exc)
        body = BuyerQuotePresenter(quote)
        return self.idempotency_commit(
            request, Response(body, status=status.HTTP_201_CREATED)
        )


class QuoteDetailView(APIView):
    """GET /api/v1/quotes/<pk>/."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer(request.user)
        try:
            quote = get_quote_for_actor(request.user, pk)
        except BuyerQuoteNotFound as exc:
            raise NotFound(detail="Quote bulunamadı.") from exc
        return Response(BuyerQuotePresenter(quote))
