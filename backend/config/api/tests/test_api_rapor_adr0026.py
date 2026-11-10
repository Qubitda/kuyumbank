"""ADR-0026 — rapor / anomali HTTP."""

from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class RaporHttpTests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.api = APIClient()
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=f"r26-co-{id(self)}"
        )
        order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_buyer_ticari_ozet(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-reports-orders"))
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["siparis_adet"], 1)
        self.assertEqual(res.json()["alici_firma_id"], self.alici.pk)

    def test_buyer_davranis(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-reports-buyer-behavior"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["alici_firma_id"], self.alici.pk)

    def test_finance_anomali(self):
        self.api.force_authenticate(user=self.finance)
        res = self.api.get(
            reverse("api-ops-anomalies-ciro"),
            {"esik_ciro": "0.01"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("uyarilar", res.json())

    def test_buyer_anomali_403(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(
            reverse("api-ops-anomalies-ciro"),
            {"esik_ciro": "1"},
        )
        self.assertEqual(res.status_code, 403)
