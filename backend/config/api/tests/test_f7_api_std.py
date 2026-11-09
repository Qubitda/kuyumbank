"""F7-010…015 — buyer/supplier/ops API, maske, hata, throttle notu."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from api.masking import assert_masked, FORBIDDEN_KEYS
from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class MaskingUnitTests(TestCase):
    def test_assert_masked_rejects_leak(self):
        with self.assertRaises(AssertionError):
            assert_masked({"tedarikci_id": 1})
        assert_masked({"varyant_id": 1, "fiyat": "10"})
        self.assertIn("maliyet", FORBIDDEN_KEYS)


class F7BuyerSupplierOpsTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        sync_user_role_groups(cls.ted_user)
        cls.ops = User(
            username="f7_ops",
            firma=cls.platform,
            rol=roles.PLATFORM_OPS,
            is_staff=True,
        )
        cls.ops.set_password("x")
        cls.ops.save()
        sync_user_role_groups(cls.ops)

    def setUp(self):
        self.api = APIClient()

    def test_buyer_catalog_ok(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-buyer-catalog"))
        self.assertEqual(res.status_code, 200)
        assert_masked(res.json())

    def test_supplier_offers_no_buyer_leak(self):
        self.api.force_authenticate(user=self.ted_user)
        res = self.api.get(reverse("api-supplier-offers"))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        assert_masked(body)
        for row in body.get("results", []):
            self.assertNotIn("alici_firma_id", row)

    def test_supplier_stock_buyer_forbidden(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-supplier-stock"))
        self.assertIn(res.status_code, (403, 401))
        data = res.json()
        self.assertEqual(data.get("status"), res.status_code)
        self.assertIn("type", data)
        self.assertIn("title", data)

    def test_ops_summary_requires_view_all(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-ops-orders-summary"))
        self.assertEqual(res.status_code, 403)
        self.api.force_authenticate(user=self.ops)
        res = self.api.get(reverse("api-ops-orders-summary"))
        self.assertEqual(res.status_code, 200)
        self.assertIn("total", res.json())


class F7ExceptionContractTests(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_unauth_me_problem_json(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertEqual(data["status"], 401)
        self.assertIn("type", data)
        self.assertIn("title", data)
        self.assertIn("detail", data)
