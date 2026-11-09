"""F7-010 + API-B2 — Buyer katalog liste/detay (maskeli; yayınlı)."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerCatalogItemPresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from urunler.models import Urun


def _assert_buyer_or_ops(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Katalog yalnız alıcı veya ops.")


class BuyerCatalogListView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer_or_ops(request.user)
        qs = Urun.objects.filter(yayin_durumu="aktif", onay_durumu="onayli")
        qs = apply_ordering(
            qs, request, whitelist=("pk", "ad", "platform_kodu"), default="pk"
        )
        return paginate_queryset(
            request, qs, present=BuyerCatalogItemPresenter
        )


class BuyerCatalogDetailView(APIView):
    """GET /api/v1/catalog/<pk>/ — yalnız yayınlı+onaylı."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        urun = Urun.objects.filter(
            pk=pk, yayin_durumu="aktif", onay_durumu="onayli"
        ).first()
        if urun is None:
            raise NotFound(detail="Ürün bulunamadı.")
        return Response(BuyerCatalogItemPresenter(urun))
