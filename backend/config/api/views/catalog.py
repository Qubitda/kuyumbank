"""F7-010 — Buyer katalog listesi (maskeli; platform yayınlı)."""

from rest_framework.response import Response
from rest_framework.views import APIView

from api.masking import assert_masked
from api.permissions import IsAuthenticatedWithFirma
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from urunler.models import Urun


class BuyerCatalogListView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        user = request.user
        firma = getattr(user, "firma", None)
        if not can_view_all_tenants(user):
            if firma is None or not getattr(firma, "alici_mi", False):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(detail="Katalog yalnız alıcı veya ops.")

        qs = (
            Urun.objects.filter(yayin_durumu="aktif", onay_durumu="onayli")
            .order_by("pk")
            .values("id", "ad", "platform_kodu", "yayin_durumu")[:100]
        )
        results = list(qs)
        for row in results:
            assert_masked(row)
        return Response({"count": len(results), "results": results})
