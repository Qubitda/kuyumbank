"""F5-021 — webhook iskeleti; tekrarlayan event tek sonuç."""

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import PaymentIntent, PaymentWebhookEvent
from finans.services import payment_servisi, webhook_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class WebhookSkeletonTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def setUp(self):
        self.api = APIClient()

    def _beklemede_intent(self, key="wh"):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=f"{key}-co"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        return payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key=f"{key}-pi"
        )

    def test_webhook_succeeds_and_idempotent(self):
        pi = self._beklemede_intent("idem")
        a = webhook_servisi.isle_webhook(
            provider="fake",
            event_id="evt-1",
            event_type="payment.succeeded",
            payload={"intent_id": pi.pk},
            actor=self.finance,
        )
        self.assertEqual(a.sonuc, PaymentWebhookEvent.Sonuc.ISLENDI)
        pi.refresh_from_db()
        self.assertEqual(pi.durum, PaymentIntent.Durum.BASARILI)

        b = webhook_servisi.isle_webhook(
            provider="fake",
            event_id="evt-1",
            event_type="payment.succeeded",
            payload={"intent_id": pi.pk},
            actor=self.finance,
        )
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(
            PaymentWebhookEvent.objects.filter(event_id="evt-1").count(), 1
        )

    def test_unknown_event_type_yok_sayildi(self):
        row = webhook_servisi.isle_webhook(
            provider="fake",
            event_id="evt-ignored",
            event_type="payment.refunded",
            payload={},
            actor=self.finance,
        )
        self.assertEqual(row.sonuc, PaymentWebhookEvent.Sonuc.YOK_SAYILDI)

    @override_settings(PAYMENT_WEBHOOK_SECRET="test-wh-secret")
    def test_http_webhook_replay(self):
        pi = self._beklemede_intent("http")
        url = reverse("api-payment-webhook")
        body = {
            "event_id": "evt-http-1",
            "event_type": "payment.succeeded",
            "provider": "fake",
            "intent_id": pi.pk,
        }
        headers = {"HTTP_X_PAYMENT_WEBHOOK_SECRET": "test-wh-secret"}
        r1 = self.api.post(url, body, format="json", **headers)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["sonuc"], "ISLENDI")
        r2 = self.api.post(url, body, format="json", **headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        pi.refresh_from_db()
        self.assertEqual(pi.durum, PaymentIntent.Durum.BASARILI)

    @override_settings(PAYMENT_WEBHOOK_SECRET="test-wh-secret")
    def test_http_bad_secret(self):
        url = reverse("api-payment-webhook")
        res = self.api.post(
            url,
            {"event_id": "x", "event_type": "payment.succeeded"},
            format="json",
            HTTP_X_PAYMENT_WEBHOOK_SECRET="wrong",
        )
        self.assertEqual(res.status_code, 401)
