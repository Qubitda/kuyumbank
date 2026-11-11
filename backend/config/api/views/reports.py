"""ADR-0026 — Rapor / anomali HTTP (OL-7 açılımı)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.permissions import IsAuthenticatedWithFirma
from api.throttles import BuyerRateThrottle, OpsRateThrottle
from siparis.services import anomali_servisi, rapor_servisi


def _opt_int(raw, *, field: str) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "Geçerli tamsayı olmalı."}) from exc


class TicariSiparisOzetView(APIView):
    """GET /api/v1/reports/orders/"""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        alici = _opt_int(
            request.query_params.get("alici_firma_id"), field="alici_firma_id"
        )
        try:
            data = rapor_servisi.ticari_siparis_ozet(
                actor=request.user,
                alici_firma_id=alici,
                date_from=request.query_params.get("date_from"),
                date_to=request.query_params.get("date_to"),
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return Response(data)


class AliciDavranisOzetView(APIView):
    """GET /api/v1/reports/buyer-behavior/"""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        alici = _opt_int(
            request.query_params.get("alici_firma_id"), field="alici_firma_id"
        )
        try:
            data = rapor_servisi.alici_davranis_ozet(
                actor=request.user,
                alici_firma_id=alici,
                date_from=request.query_params.get("date_from"),
                date_to=request.query_params.get("date_to"),
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return Response(data)


class CiroAnomaliView(APIView):
    """GET /api/v1/ops/anomalies/ciro/?esik_ciro=..."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request):
        raw = request.query_params.get("esik_ciro")
        if raw is None or raw == "":
            raise ValidationError({"esik_ciro": "Zorunlu."})
        try:
            esik = Decimal(str(raw))
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError({"esik_ciro": "Geçerli Decimal olmalı."}) from exc
        alici = _opt_int(
            request.query_params.get("alici_firma_id"), field="alici_firma_id"
        )
        try:
            data = anomali_servisi.ciro_esik_tara(
                actor=request.user,
                esik_ciro=esik,
                alici_firma_id=alici,
                date_from=request.query_params.get("date_from"),
                date_to=request.query_params.get("date_to"),
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return Response(data)
