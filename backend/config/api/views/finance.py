"""F5-030 — Alıcı finans özeti API (maskeli)."""

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from finans.services import buyer_finans_servisi


class BuyerFinanceSummaryView(APIView):
    """GET /api/v1/finance/me/?para_birimi=TRY"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        pb = request.query_params.get("para_birimi") or "TRY"
        request.query_params.get("firma_id")  # client firma_id yok sayılır
        try:
            data = buyer_finans_servisi.ozet_for_actor(
                actor=request.user, para_birimi=pb
            )
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(detail=exc.message_dict) from exc
            raise ValidationError(
                detail=exc.messages if hasattr(exc, "messages") else str(exc)
            ) from exc
        return Response(data)
