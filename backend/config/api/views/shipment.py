"""F6-023 + B3 — Buyer sevkiyat takip API (maskeli + allowed_actions)."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.finance_ops import BuyerShipmentPresenter
from api.throttles import BuyerRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants
from lojistik.models import Shipment
from lojistik.services import buyer_shipment_servisi
from lojistik.services.buyer_shipment_servisi import ShipmentNotFound
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor


def _assert_buyer_or_ops(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied(detail="Sevkiyat yalnız alıcı veya platform ops içindir.")


class ShipmentListView(APIView):
    """GET /api/v1/shipments/?order_id= — alıcı kendi; ops view_all."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_buyer_or_ops(request.user)
        qs = Shipment.objects.select_related("order")
        qs = buyer_shipment_servisi.scope_shipment_queryset(qs, request.user)
        order_id = request.query_params.get("order_id")
        if order_id:
            try:
                oid = int(order_id)
            except (TypeError, ValueError):
                raise NotFound(detail="Sipariş bulunamadı.") from None
            try:
                get_order_for_actor(request.user, order_id=oid)
            except OrderNotFound as exc:
                raise NotFound(detail="Sipariş bulunamadı.") from exc
            qs = qs.filter(order_id=oid)
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(request, qs, present=BuyerShipmentPresenter)


class ShipmentDetailView(APIView):
    """GET /api/v1/shipments/<pk>/ — tenant 404; tedarikçi 403."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        try:
            ship = buyer_shipment_servisi.get_shipment_for_actor(
                request.user, shipment_id=pk
            )
        except ShipmentNotFound as exc:
            raise NotFound(detail="Sevkiyat bulunamadı.") from exc
        return Response(BuyerShipmentPresenter(ship))
