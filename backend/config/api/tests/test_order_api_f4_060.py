"""F4-060/061 — buyer cart/order API + ops list; tedarikçi 403; çapraz 404."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class BuyerOrderApiTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()

    def _make_order(self, key="api-ord-1"):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_buyer_order_list_and_detail(self):
        order = self._make_order()
        self.api.force_authenticate(user=self.buyer)
        lst = self.api.get(reverse("api-order-list"), {"firma_id": 999999})
        self.assertEqual(lst.status_code, 200)
        self.assertFalse(lst.json()["ops"])
        ids = [r["id"] for r in lst.json()["results"]]
        self.assertIn(order.pk, ids)

        det = self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(det.status_code, 200)
        body = det.json()
        self.assertEqual(body["id"], order.pk)
        self.assertIn("lines", body)
        self.assertGreaterEqual(len(body["lines"]), 1)
        # Kör havuz: tedarikçi alanları yok
        self.assertNotIn("tedarikci", body)
        self.assertNotIn("teklif", body["lines"][0])

    def test_buyer_cart_mine(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-cart-mine"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], cart.pk)
        self.assertIn("lines", res.json())

    def test_supplier_forbidden(self):
        order = self._make_order(key="api-sup-1")
        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(
            self.api.get(reverse("api-order-list")).status_code, 403
        )
        self.assertEqual(
            self.api.get(
                reverse("api-order-detail", kwargs={"pk": order.pk})
            ).status_code,
            403,
        )
        self.assertEqual(self.api.get(reverse("api-cart-mine")).status_code, 403)

    def test_ops_list_sees_buyer_order(self):
        self.assertTrue(can_view_all_tenants(self.finance))
        order = self._make_order(key="api-ops-1")
        self.api.force_authenticate(user=self.finance)
        res = self.api.get(reverse("api-order-list"))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ops"])
        ids = [r["id"] for r in res.json()["results"]]
        self.assertIn(order.pk, ids)
