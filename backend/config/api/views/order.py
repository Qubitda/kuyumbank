"""F4-060/061 + API-B1 — buyer order detay/liste + platform ops liste."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerOrderPresenter
from siparis.models import Order
from siparis.selectors.tenant import (
    OrderNotFound,
    can_ops_read_orders,
    get_order_for_actor,
    scope_order_queryset,
)


def _assert_buyer_or_ops(user) -> None:
    if can_ops_read_orders(user):
        return
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied(
        detail="Sipariş yalnız alıcı veya QC/lojistik/platform ops içindir."
    )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise NotFound(detail="Sipariş bulunamadı.") from exc
        return Response(BuyerOrderPresenter(order))


class OrderListView(APIView):
    """GET /api/v1/orders/ — alıcı kendi; view_all / QC / lojistik tümü. Client firma_id yok."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        _assert_buyer_or_ops(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = scope_order_queryset(
            Order.objects.select_related("alici_firma"),
            request.user,
        )
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk", "durum"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(
            request,
            qs,
            present=lambda o: BuyerOrderPresenter(o, include_lines=False),
            extra={"ops": can_ops_read_orders(request.user)},
        )
