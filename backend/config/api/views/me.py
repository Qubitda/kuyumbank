"""PRE-002/003 — kimlik iskeleti; firma yalnız request.user'dan."""

from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma


class MeView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        user = request.user
        # Client ?firma_id= asla kullanılmaz
        return Response(
            {
                "id": user.pk,
                "username": user.get_username(),
                "firma_id": user.firma_id,
                "rol": getattr(user, "rol", ""),
            }
        )
