"""F7-012 — Ops API genişletme (view_all zorunlu)."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from api.throttles import OpsRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from firmalar.role_permissions import P
from siparis.models import Order


class OpsOrderSummaryView(APIView):
    """GET /api/v1/ops/orders/summary/ — view_all zorunlu."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request):
        if not can_view_all_tenants(request.user):
            raise PermissionDenied(detail="Ops API için view_all_tenants gerekir.")
        total = Order.objects.count()
        by_durum = {
            "OLUSTURULDU": Order.objects.filter(durum="OLUSTURULDU").count(),
            "IPTAL": Order.objects.filter(durum="IPTAL").count(),
        }
        return Response(
            {
                "total": total,
                "by_durum": by_durum,
                "perms": {
                    "view_all": True,
                    "manage_org": has_perm(request.user, P["manage_org"]),
                },
            }
        )
