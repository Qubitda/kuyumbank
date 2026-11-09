"""F5-040 — Alıcı kredi özeti / checkout öncesi kontrol."""

from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from finans.services import credit_servisi


def _map_exc(exc):
    if isinstance(exc, DjangoPermissionDenied):
        raise PermissionDenied(detail=str(exc)) from exc
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            raise ValidationError(detail=exc.message_dict) from exc
        raise ValidationError(detail=exc.messages if hasattr(exc, "messages") else str(exc)) from exc
    raise exc


class CreditMineView(APIView):
    """GET /api/v1/credit/me/?para_birimi=TRY"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        pb = request.query_params.get("para_birimi") or "TRY"
        # Client firma_id yok sayılır
        request.query_params.get("firma_id")  # bilerek ignore
        try:
            summary = credit_servisi.ozet_for_actor(
                actor=request.user, para_birimi=pb
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            _map_exc(exc)
        data = credit_servisi.present_credit(summary)
        # Kör: karsi / tedarikçi / başka firma yok
        assert "karsi_firma" not in data
        assert "firma_id" not in data
        return Response(data)


class CreditCheckView(IdempotencyMixin, APIView):
    """POST /api/v1/credit/check/ — {tutar, para_birimi?}; Idempotency-Key zorunlu."""

    permission_classes = [IsAuthenticatedWithFirma]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached

        raw = request.data.get("tutar")
        pb = request.data.get("para_birimi") or "TRY"
        try:
            tutar = Decimal(str(raw))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"tutar": "Geçersiz tutar."}) from exc
        try:
            summary = credit_servisi.assert_musait(
                actor=request.user, tutar=tutar, para_birimi=pb
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            _map_exc(exc)
        response = Response(
            {
                "ok": True,
                "credit": credit_servisi.present_credit(summary),
            }
        )
        return self.idempotency_commit(request, response)
