"""GAP-F3-01 — GET /api/v1/piyasa/pano/ (maskeli board)."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from api.throttles import BuyerRateThrottle
from piyasa.selectors.pano import present_buyer_pano


class PiyasaPanoView(APIView):
    """GET /api/v1/piyasa/pano/?olcek=ONS|KG|GRAM — alıcı board; marj yok."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        olcek = request.query_params.get("olcek")
        try:
            body = present_buyer_pano(olcek=olcek)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        return Response(body)
