"""F5-021 — Ödeme sağlayıcı webhook endpoint (secret header; AllowAny)."""

from __future__ import annotations

import secrets

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finans.services import webhook_servisi

HEADER = "X-Payment-Webhook-Secret"


class PaymentWebhookView(APIView):
    """POST /api/v1/payments/webhook/

    Body: {event_id, event_type, provider?, payload?}
    payload.intent_id — payment.succeeded için zorunlu.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "") or ""
        if not expected:
            return Response(
                {"detail": "Webhook secret yapılandırılmamış."}, status=401
            )
        got = request.headers.get(HEADER) or ""
        if not secrets.compare_digest(got, expected):
            return Response({"detail": "Webhook secret geçersiz."}, status=401)

        data = request.data if isinstance(request.data, dict) else {}
        event_id = data.get("event_id")
        event_type = data.get("event_type")
        provider = data.get("provider") or "fake"
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        # Düz alanlar da kabul (iskelet)
        if "intent_id" in data and "intent_id" not in payload:
            payload = {**payload, "intent_id": data.get("intent_id")}

        try:
            row = webhook_servisi.isle_webhook(
                provider=provider,
                event_id=str(event_id or ""),
                event_type=str(event_type or ""),
                payload=payload,
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(detail=exc.message_dict) from exc
            raise ValidationError(
                detail=exc.messages if hasattr(exc, "messages") else str(exc)
            ) from exc

        return Response(
            {
                "id": row.pk,
                "event_id": row.event_id,
                "sonuc": row.sonuc,
                "payment_intent_id": row.payment_intent_id,
                "detail": row.detail,
            },
            status=200,
        )
