"""PRE — ince order okuma iskeleti (tenant 404)."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import Order


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request, pk: int):
        qs = Order.objects.all()
        if not can_view_all_tenants(request.user):
            qs = qs.filter(alici_firma_id=request.user.firma_id)
        order = qs.filter(pk=pk).first()
        if order is None:
            raise NotFound(detail="Sipariş bulunamadı.")
        return Response(
            {
                "id": order.pk,
                "durum": order.durum,
                "alici_firma_id": order.alici_firma_id,
                "line_count": order.lines.count(),
            }
        )
