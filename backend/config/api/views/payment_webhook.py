"""F5-021 — Ödeme sağlayıcı webhook (HMAC + replay; AllowAny)."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from finans.services import webhook_servisi
from finans.services.webhook_security import verify_webhook_http


class WebhookAnonThrottle(AnonRateThrottle):
    """Provider yoğun retry için ayrı (daha yüksek) scope opsiyonel; varsayılan anon."""

    scope = "webhook"


class PaymentWebhookView(APIView):
    """POST /api/v1/payments/webhook/

    Body: {event_id, event_type, provider?, payload?}
    Headers: X-Webhook-Timestamp + X-Webhook-Signature (HMAC-SHA256)
    payload.intent_id — payment.succeeded için zorunlu.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [WebhookAnonThrottle]

    def post(self, request):
        try:
            verify_webhook_http(request)
        except DjangoValidationError as exc:
            msg = (
                exc.messages[0]
                if hasattr(exc, "messages") and exc.messages
                else str(exc)
            )
            # Yapılandırma / auth hataları → 401; diğerleri 400
            status = 401
            low = str(msg).lower()
            if "zaman" in low or "replay" in low or "imza" in low:
                status = 401
            if "yapılandırılmamış" in low or "secret" in low or "allow-list" in low:
                status = 401
            return Response({"detail": msg}, status=status)

        data = request.data if isinstance(request.data, dict) else {}
        event_id = data.get("event_id")
        event_type = data.get("event_type")
        provider = data.get("provider") or "fake"
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
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
