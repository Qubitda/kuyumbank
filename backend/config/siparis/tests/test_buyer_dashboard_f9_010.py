"""F9-010 — Buyer dashboard auth + tenant context (kör)."""

from django.test import Client, TestCase
from django.urls import reverse

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class BuyerDashboardF9010Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.client = Client()

    def test_login_required(self):
        res = self.client.get(reverse("buyer-home"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/buyer/login/", res.url)

    def test_supplier_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-home"))
        self.assertEqual(res.status_code, 403)

    def test_buyer_sees_tenant_context_masked(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("buyer-home"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Alıcı paneli")
        self.assertContains(res, self.alici.ad)
        self.assertContains(res, self.buyer.username)
        self.assertContains(res, self.buyer.rol)
        self.assertNotContains(res, "tedarikci")
        self.assertNotContains(res, self.ted.ad)
        # sepet hâlâ ayrı route
        cart = self.client.get(reverse("buyer-cart"))
        self.assertEqual(cart.status_code, 200)
