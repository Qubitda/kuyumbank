"""F4-060 — buyer cart detay okuma (tenant 404)."""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from api.presenters.buyer import BuyerCartPresenter
from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor


def _assert_buyer_or_ops(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied(detail="Sepet yalnız alıcı veya platform ops içindir.")


class CartDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        try:
            cart = get_cart_for_actor(request.user, cart_id=pk)
        except CartNotFound as exc:
            raise NotFound(detail="Sepet bulunamadı.") from exc
        return Response(BuyerCartPresenter(cart))
