"""NX-3…12 kod sözleşmesi smoke — ADR-0017 madde Kabul değil; runtime kanıt."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import pricing_service
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class Nx3ProblemJsonMediaTypeTests(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_unauth_me_content_type_problem_json(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)
        ctype = res.get("Content-Type", "")
        self.assertTrue(
            ctype.startswith("application/problem+json"),
            msg=f"Content-Type={ctype!r}",
        )
        body = res.json()
        for key in ("type", "title", "status", "detail", "code", "request_id"):
            self.assertIn(key, body)


class Nx5MeAndNx10NoStoreTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(user=self.buyer)

    def test_me_capabilities_and_no_store(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get("Cache-Control"), "no-store")
        body = res.json()
        self.assertIn("capabilities", body)
        self.assertIn("firma", body)


class Nx8PriceLockFieldsTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(user=self.buyer)

    def test_pricelock_presenter_contract_fields(self):
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.buyer,
        )
        lock_res = self.api.post(
            reverse("api-price-lock-create"),
            {"quote_id": quote.pk},
            format="json",
            HTTP_IDEMPOTENCY_KEY="nx8-lock-1",
        )
        self.assertEqual(lock_res.status_code, 201, lock_res.content)
        body = lock_res.json()
        for key in (
            "id",
            "quote_id",
            "durum",
            "toplam_vergisiz",
            "para_birimi",
            "kilit_zamani",
            "expires_at",
            "server_now",
            "gecerli",
            "allowed_actions",
        ):
            self.assertIn(key, body, msg=f"missing {key}")
        self.assertIsInstance(body["allowed_actions"], list)
        self.assertIn("checkout", body["allowed_actions"])
        self.assertEqual(lock_res.get("Cache-Control"), "no-store")

        det = self.api.get(reverse("api-price-lock-detail", kwargs={"pk": body["id"]}))
        self.assertEqual(det.status_code, 200)
        self.assertEqual(det.get("Cache-Control"), "no-store")
        self.assertIn("allowed_actions", det.json())


class Nx11ApiVersionTests(TestCase):
    def test_settings_and_health_api_v1(self):
        self.assertEqual(getattr(settings, "API_VERSION", None), "v1")
        res = APIClient().get(reverse("api-health"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("api"), "v1")
