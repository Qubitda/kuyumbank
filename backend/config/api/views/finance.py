"""F5-030 + B3 — Alıcı finans özeti / cari / ledger API (maskeli)."""

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.finance_ops import (
    BuyerCariPresenter,
    BuyerFinancePresenter,
    BuyerLedgerPresenter,
)
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from finans.models import LedgerEntry
from finans.selectors import get_cari_for_actor, scope_cari_queryset
from finans.selectors.cari import CariNotFound
from finans.services import buyer_finans_servisi


def _assert_buyer(user) -> None:
    if can_view_all_tenants(user):
        raise PermissionDenied(detail="Ops bu alıcı finans uçlarını kullanamaz.")
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Yalnız alıcı.")


class BuyerFinanceSummaryView(APIView):
    """GET /api/v1/finance/me/?para_birimi=TRY"""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer(request.user)
        pb = request.query_params.get("para_birimi") or "TRY"
        request.query_params.get("firma_id")  # client firma_id yok sayılır
        try:
            data = buyer_finans_servisi.ozet_for_actor(
                actor=request.user, para_birimi=pb
            )
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(detail=exc.message_dict) from exc
            raise ValidationError(
                detail=exc.messages if hasattr(exc, "messages") else str(exc)
            ) from exc
        return Response(BuyerFinancePresenter(data))


class BuyerCariListView(APIView):
    """GET /api/v1/finance/cari/ — kendi cari hesapları (maskeli)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer(request.user)
        request.query_params.get("firma_id")
        qs = apply_ordering(
            scope_cari_queryset(request.user),
            request,
            whitelist=("guncelleme_tarihi", "pk"),
            default="-guncelleme_tarihi",
        )
        return paginate_queryset(request, qs, present=BuyerCariPresenter)


class BuyerCariDetailView(APIView):
    """GET /api/v1/finance/cari/<pk>/"""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer(request.user)
        try:
            hesap = get_cari_for_actor(request.user, pk=pk)
        except CariNotFound as exc:
            raise NotFound(detail="Cari hesap bulunamadı.") from exc
        return Response(BuyerCariPresenter(hesap))


class BuyerLedgerListView(APIView):
    """GET /api/v1/finance/ledger/ — kendi ledger (maskeli; karşı firma yok)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer(request.user)
        request.query_params.get("firma_id")
        firma_id = request.user.firma_id
        qs = LedgerEntry.objects.filter(firma_id=firma_id)
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(request, qs, present=BuyerLedgerPresenter)
