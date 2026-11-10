"""F7-010 + API-B2 — Buyer katalog liste/detay (maskeli; yayınlı).

Liste/detay alanları `urunler.services.buyer_katalog_servisi` ile hizalı
(`q` arama HTML F9-011 ile aynı).
"""

from django.db.models import Count, Q
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import (
    BuyerCatalogDetailPresenter,
    BuyerCatalogItemPresenter,
)
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
        qs = (
            Urun.objects.filter(yayin_durumu="aktif", onay_durumu="onayli")
            .select_related("kategori", "ayar")
            .annotate(
                varyant_count=Count(
                    "varyantlar", filter=Q(varyantlar__aktif=True)
                )
            )
        )
        term = (request.query_params.get("q") or "").strip()
        if term:
            qs = qs.filter(
                Q(ad__icontains=term) | Q(platform_kodu__icontains=term)
            )
        qs = apply_ordering(
            qs, request, whitelist=("pk", "ad", "platform_kodu"), default="pk"
        )
        return paginate_queryset(
            request, qs, present=BuyerCatalogItemPresenter
        )


class BuyerCatalogDetailView(APIView):
    """GET /api/v1/catalog/<pk>/ — yalnız yayınlı+onaylı; varyant listesi."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        try:
            data = BuyerCatalogDetailPresenter(pk)
        except LookupError as exc:
            raise NotFound(detail="Ürün bulunamadı.") from exc
        return Response(data)
