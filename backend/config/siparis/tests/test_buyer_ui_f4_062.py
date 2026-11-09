"""F4-062 — Minimal alıcı UI smoke (session)."""

from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from siparis.services import cart_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class BuyerUiSmokeTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.client = Client()

    def test_login_required_redirects(self):
        res = self.client.get(reverse("buyer-cart"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/buyer/login/", res.url)

    def test_supplier_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-cart"))
        self.assertEqual(res.status_code, 403)

    def test_buyer_cart_and_orders_flow(self):
        self.client.force_login(self.buyer)
        self._quote_and_cart(miktar=Decimal("1"))
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)

        res = self.client.get(reverse("buyer-cart"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f"Sepet #{cart.pk}")

        key = "ui-smoke-ord-1"
        res = self.client.post(
            reverse("buyer-checkout"),
            {"idempotency_key": key},
        )
        self.assertEqual(res.status_code, 302)
        from siparis.models import Order

        order = Order.objects.get(
            alici_firma=self.buyer.firma, idempotency_key=key
        )
        self.assertIn(
            reverse("buyer-order-detail", kwargs={"pk": order.pk}),
            res.url,
        )

        lst = self.client.get(reverse("buyer-order-list"))
        self.assertEqual(lst.status_code, 200)
        self.assertContains(lst, f"#{order.pk}")

        det = self.client.get(
            reverse("buyer-order-detail", kwargs={"pk": order.pk})
        )
        self.assertEqual(det.status_code, 200)
        self.assertContains(det, f"Sipariş #{order.pk}")
        self.assertNotContains(det, "tedarikci")
