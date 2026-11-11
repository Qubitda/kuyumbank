"""PRE-002/003 + API-B1 — /me yetenek keşfi; firma yalnız request.user'dan."""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma, can_buyer_commerce_read
from api.services.capabilities_servisi import present_me
from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.services import buyer_dashboard_servisi


class MeView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        # Client ?firma_id= asla kullanılmaz
        return Response(present_me(request.user, request=request))


class MeDashboardView(APIView):
    """GET /me/dashboard/ — alıcı özet sayaçlar (ADR-0029 AO-5)."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        user = request.user
        if can_view_all_tenants(user):
            raise PermissionDenied(
                "Ops kullanıcıları dashboard yerine ilgili API uçlarını kullanır."
            )
        if not can_buyer_commerce_read(user):
            raise PermissionDenied("Yalnız alıcı firma kullanıcıları.")
        try:
            return Response(buyer_dashboard_servisi.ozet_for_actor(actor=user))
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
