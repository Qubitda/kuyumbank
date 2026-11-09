"""SEC-001 — DRF TokenAuthentication."""

from django.test import TestCase
from django.urls import reverse
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
