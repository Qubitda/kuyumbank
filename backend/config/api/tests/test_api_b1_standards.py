"""API-B1 — hata zarfı, /me capabilities, auth/csrf, liste sayfalama (CORS yok)."""

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from api.pagination import _with_pk_tiebreak
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class ProblemJsonB1Tests(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_unauth_me_has_code_and_request_id(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertEqual(data["status"], 401)
        self.assertIn("code", data)
        self.assertIn("request_id", data)
        self.assertTrue(res.get("X-Request-ID"))
        self.assertEqual(data["request_id"], res["X-Request-ID"])


class MeCapabilitiesTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.api = APIClient()

    def test_me_capabilities_buyer(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("capabilities", body)
        self.assertTrue(body["capabilities"]["can_checkout"])
        self.assertTrue(body["capabilities"]["can_view_catalog"])
        self.assertFalse(body["capabilities"]["can_view_ops"])
        self.assertIn("firma", body)
        self.assertEqual(body["firma"]["id"], self.buyer.firma_id)
        self.assertEqual(res.get("Cache-Control"), "no-store")


class AuthSessionTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        cls.buyer.set_password("Secret123!")
        cls.buyer.save()
        # Login kapısı: fixture firmaları onaylı olmalı
        Firma = cls.buyer.firma.__class__
        Firma.objects.filter(pk=cls.buyer.firma_id).update(
            onay_durumu="onayli", aktif=True
        )

    def setUp(self):
        from django.core.cache import cache

        cache.clear()  # login throttle LocMem birikimi
        self.api = APIClient(enforce_csrf_checks=False)

    def _csrf_headers(self) -> dict:
        res = self.api.get(reverse("api-auth-csrf"))
        self.assertEqual(res.status_code, 200)
        token = res.json()["csrf_token"]
        self.assertTrue(token)
        self.assertIn("csrftoken", self.api.cookies)
        return {"HTTP_X_CSRFTOKEN": token}

    def test_csrf_and_login_logout(self):
        bad = self.api.post(
            reverse("api-auth-login"),
            {"username": self.buyer.username, "password": "wrong"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(bad.status_code, 401, bad.content)
        self.assertEqual(bad.json().get("code"), "authentication_failed")

        ok = self.api.post(
            reverse("api-auth-login"),
            {"username": self.buyer.username, "password": "Secret123!"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertIn("capabilities", ok.json())

        out = self.api.post(
            reverse("api-auth-logout"),
            {},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(out.status_code, 200)


class ListPaginationTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(user=self.buyer)

    def test_order_list_envelope(self):
        res = self.api.get(reverse("api-order-list"), {"page": 1, "page_size": 10})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        for key in ("count", "next", "previous", "page", "page_size", "results"):
            self.assertIn(key, body)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 10)


class DeterministicOrderingUnitTests(SimpleTestCase):
    def test_pk_tiebreak_appended(self):
        self.assertEqual(
            _with_pk_tiebreak(["-olusturma_tarihi"]),
            ["-olusturma_tarihi", "-pk"],
        )
        self.assertEqual(_with_pk_tiebreak(["-pk"]), ["-pk"])
        self.assertEqual(_with_pk_tiebreak(["pk"]), ["pk"])
