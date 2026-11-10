"""PRE-001…004 — health, auth, tenant 404, OpenAPI schema."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class PreApiHealthTests(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_health_public(self):
        url = reverse("api-health")
        res = self.api.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_me_requires_auth(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)

    @override_settings(DEBUG=True)
    def test_schema_endpoint(self):
        # Prod’da docs kapalı; DEBUG’ta /api/v1/schema/ açık (Spectacular JSON).
        res = self.api.get(reverse("api-schema"))
        self.assertEqual(res.status_code, 200)
        body = res.content.decode("utf-8")
        self.assertTrue(
            "openapi" in body.lower() or "swagger" in body.lower() or "paths" in body
        )


class PreApiTenantTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        from firmalar.models import Firma

        cls.other_firma = Firma.objects.create(
            ad="PREAL2",
            firma_kodu="PREAL2",
            alici_mi=True,
        )
        cls.intruder = User(
            username="pre_intruder",
            firma=cls.other_firma,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.intruder.set_password("x")
        cls.intruder.save()
        sync_user_role_groups(cls.intruder)

    def setUp(self):
        self.api = APIClient()

    def test_me_returns_actor_firma_not_query_param(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-me"), {"firma_id": 999999})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["firma_id"], self.buyer.firma_id)
        self.assertNotEqual(data["firma_id"], 999999)

    def test_cart_cross_tenant_404(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.api.force_authenticate(user=self.intruder)
        res = self.api.get(reverse("api-cart-detail", kwargs={"pk": cart.pk}))
        self.assertEqual(res.status_code, 404)

    def test_cart_same_tenant_200(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-cart-detail", kwargs={"pk": cart.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], cart.pk)
        self.assertEqual(res.json()["alici_firma_id"], self.buyer.firma_id)

    def test_order_cross_tenant_404(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="pre-ord-1"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.api.force_authenticate(user=self.intruder)
        res = self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(res.status_code, 404)
