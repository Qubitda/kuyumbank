"""PRE-002/003 + API-B1 — /me yetenek keşfi; firma yalnız request.user'dan."""

from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from api.services.capabilities_servisi import present_me


class MeView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        # Client ?firma_id= asla kullanılmaz
        return Response(present_me(request.user))
