"""Buyer/ops — aktif satış kanalları (quote için satis_kanali_id keşfi)."""

from __future__ import annotations

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from api.throttles import BuyerRateThrottle
from tanimlar.models import SatisKanali


class SalesChannelListView(APIView):
    """GET /api/v1/sales-channels/ — [{id, kod, ad, quote_ttl_saniye}]."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        rows = list(
            SatisKanali.objects.filter(aktif=True)
            .order_by("sira", "kod")
            .values("id", "kod", "ad", "quote_ttl_saniye")
        )
        return Response(
            {
                "count": len(rows),
                "results": rows,
                "server_now": timezone.now().isoformat(),
            }
        )
