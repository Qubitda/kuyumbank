"""ADIM 6 — FE same-origin session/CSRF sözleşmesi (frontend/src/lib/api/client.ts).

Next rewrite: /api/v1/* → Django (CORS yok). Django Client ile:
csrf → login (+ X-CSRFToken) → me → logout; CSRF eksik POST → 403.
"""
from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class FeSessionCsrfFlowTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        cls.buyer.set_password("Secret123!")
        cls.buyer.save()
        Firma = cls.buyer.firma.__class__
        Firma.objects.filter(pk=cls.buyer.firma_id).update(
            onay_durumu="onayli", aktif=True
        )

    def setUp(self):
        cache.clear()
        self.api = APIClient(enforce_csrf_checks=True)

    def _csrf_token(self) -> str:
        res = self.api.get(reverse("api-auth-csrf"))
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        self.assertIn("csrf_token", body)
        self.assertTrue(body["csrf_token"])
        self.assertIn("csrftoken", self.api.cookies)
        # FE client.ts: cookie varsa onu kullanır (Django cookie ≠ body mask olabilir)
        cookie = self.api.cookies.get("csrftoken")
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie.value)
        return cookie.value

    def test_csrf_required_on_login(self):
        missing = self.api.post(
            reverse("api-auth-login"),
            {"username": self.buyer.username, "password": "Secret123!"},
            format="json",
        )
        self.assertEqual(missing.status_code, 403, missing.content)

    def test_csrf_login_me_logout(self):
        token = self._csrf_token()
        login = self.api.post(
            reverse("api-auth-login"),
            {"username": self.buyer.username, "password": "Secret123!"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(login.status_code, 200, login.content)
        self.assertIn("capabilities", login.json())

        me = self.api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 200, me.content)
        self.assertEqual(me.json().get("username"), self.buyer.username)

        # FE: mutating call again ensures CSRF (cookie refresh ok)
        token2 = self._csrf_token()
        out = self.api.post(
            reverse("api-auth-logout"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=token2,
        )
        self.assertEqual(out.status_code, 200, out.content)

        me2 = self.api.get(reverse("api-me"))
        self.assertIn(me2.status_code, (401, 403), me2.content)
