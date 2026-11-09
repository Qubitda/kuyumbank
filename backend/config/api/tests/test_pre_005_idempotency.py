"""PRE-005 — Idempotency-Key middleware + checkout POST örneği."""

from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import IdempotencyRecord
from siparis.models import CheckoutAttempt
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class CheckoutIdempotencyApiTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()
        self.url = reverse("api-checkout-create")

    def test_post_without_key_400(self):
        self._quote_and_cart(miktar=Decimal("1"))
        self.api.force_authenticate(user=self.buyer)
        res = self.api.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_post_replay_same_key_same_result(self):
        self._quote_and_cart(miktar=Decimal("1"))
        self.api.force_authenticate(user=self.buyer)
        headers = {"HTTP_IDEMPOTENCY_KEY": "pre005-co-1"}
        first = self.api.post(self.url, {}, format="json", **headers)
        self.assertEqual(first.status_code, 201, first.content)
        attempt_id = first.json()["id"]
        self.assertEqual(
            CheckoutAttempt.objects.filter(
                alici_firma=self.buyer.firma, idempotency_key="pre005-co-1"
            ).count(),
            1,
        )

        second = self.api.post(self.url, {}, format="json", **headers)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.json()["id"], attempt_id)
        self.assertEqual(
            CheckoutAttempt.objects.filter(
                alici_firma=self.buyer.firma, idempotency_key="pre005-co-1"
            ).count(),
            1,
        )
        from api.services import idempotency_servisi as idem

        sk = idem.storage_key(
            actor_id=self.buyer.pk, client_key="pre005-co-1"
        )
        self.assertEqual(
            IdempotencyRecord.objects.filter(
                firma=self.buyer.firma, key=sk
            ).count(),
            1,
        )

    def test_same_key_different_body_409(self):
        self._quote_and_cart(miktar=Decimal("1"))
        self.api.force_authenticate(user=self.buyer)
        headers = {"HTTP_IDEMPOTENCY_KEY": "pre005-co-conflict"}
        first = self.api.post(self.url, {}, format="json", **headers)
        self.assertEqual(first.status_code, 201, first.content)
        conflict = self.api.post(
            self.url, {"note": "different"}, format="json", **headers
        )
        self.assertEqual(conflict.status_code, 409)
