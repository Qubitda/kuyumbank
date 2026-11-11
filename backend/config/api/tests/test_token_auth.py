"""SEC-001 — DRF ExpiringTokenAuthentication."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class TokenAuthTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()
        self.token = Token.objects.create(user=self.buyer)

    def test_me_with_token_200(self):
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["firma_id"], self.buyer.firma_id)

    def test_me_without_auth_still_401(self):
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)

    @override_settings(AUTH_TOKEN_TTL_SECONDS=3600)
    def test_expired_token_401(self):
        Token.objects.filter(pk=self.token.pk).update(
            created=timezone.now() - timedelta(hours=2)
        )
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        res = self.api.get(reverse("api-me"))
        self.assertEqual(res.status_code, 401)
