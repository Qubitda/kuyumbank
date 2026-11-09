"""F4-060/061 — buyer order detay/liste + platform ops liste (view_all)."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import Order
from siparis.selectors.tenant import (
    OrderNotFound,
    get_order_for_actor,
    scope_order_queryset,
)
from siparis.services.presenters import present_order


def _assert_buyer_or_ops(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied(detail="Sipariş yalnız alıcı veya platform ops içindir.")


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        return Response(present_order(order))


class OrderListView(APIView):
    """GET /api/v1/orders/ — alıcı kendi; ops view_all tümü. Client firma_id yok sayılır."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        _assert_buyer_or_ops(request.user)
        # Client firma_id güvenilmez — yok say
        qs = scope_order_queryset(
            Order.objects.select_related("alici_firma").order_by(
                "-olusturma_tarihi", "-pk"
            ),
            request.user,
        )
        items = [present_order(o, include_lines=False) for o in qs[:100]]
        return Response(
            {
                "count": len(items),
                "results": items,
                "ops": can_view_all_tenants(request.user),
            }
        )
