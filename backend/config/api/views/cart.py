"""F4-060 — buyer cart detay okuma (tenant 404)."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasCartObjectAccess
from api.presenters.buyer import BuyerCartPresenter
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor


class CartDetailView(APIView):
    permission_classes = [HasCartObjectAccess]

    def get(self, request, pk: int):
        try:
            cart = get_cart_for_actor(request.user, cart_id=pk)
        except CartNotFound as exc:
            raise NotFound(detail="Sepet bulunamadı.") from exc
        self.check_object_permissions(request, cart)
        return Response(BuyerCartPresenter(cart))
