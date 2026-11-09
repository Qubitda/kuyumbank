"""F7-020 — WebhookDelivery idempotent."""

from django.test import TestCase

from firmalar.models import OutboxMessage, WebhookDelivery
from firmalar.services import outbox_servisi, webhook_delivery_servisi
from firmalar.services.audit_servisi import domain_atomic


class WebhookDeliveryF7020Tests(TestCase):
    def test_ensure_delivery_idempotent(self):
        with domain_atomic():
            msg = outbox_servisi.enqueue(
                event_type="order.created", payload={"order_id": 1}
            )
        d1 = webhook_delivery_servisi.ensure_delivery(
            outbox=msg, endpoint_key="fake", idempotency_key="k1"
        )
        d2 = webhook_delivery_servisi.ensure_delivery(
            outbox=msg, endpoint_key="fake", idempotency_key="k1"
        )
        self.assertEqual(d1.pk, d2.pk)
        self.assertEqual(
            WebhookDelivery.objects.filter(outbox=msg, idempotency_key="k1").count(),
            1,
        )
        d3 = webhook_delivery_servisi.deliver_fake(outbox=msg, endpoint_key="fake")
        self.assertEqual(d3.durum, WebhookDelivery.Durum.DELIVERED)
