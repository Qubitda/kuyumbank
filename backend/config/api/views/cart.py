"""PRE — ince cart okuma iskeleti (tenant 404)."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor


class CartDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request, pk: int):
        try:
            cart = get_cart_for_actor(request.user, cart_id=pk)
        except CartNotFound as exc:
            raise NotFound(detail="Sepet bulunamadı.") from exc
        return Response(
            {
                "id": cart.pk,
                "alici_firma_id": cart.alici_firma_id,
                "line_count": cart.lines.count(),
            }
        )
