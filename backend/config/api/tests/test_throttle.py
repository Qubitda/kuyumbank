"""DRF anon/user throttle — güvenlik hijyeni."""

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle


_THROTTLED_RF = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "api.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "2/min",
        "user": "600/min",
    },
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
}


@override_settings(REST_FRAMEWORK=_THROTTLED_RF)
class AnonThrottleTests(TestCase):
    def setUp(self):
        # DRF SimpleRateThrottle sınıf özniteliği import anında kopyalanır;
        # override_settings sonrası api_settings'ten senkronize et.
        self._rates_backup = SimpleRateThrottle.THROTTLE_RATES
        SimpleRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES
        cache.clear()
        self.api = APIClient()
        self.url = reverse("api-health")

    def tearDown(self):
        SimpleRateThrottle.THROTTLE_RATES = self._rates_backup
        cache.clear()

    def test_anon_throttle_returns_429_after_limit(self):
        self.assertEqual(self.api.get(self.url).status_code, 200)
        self.assertEqual(self.api.get(self.url).status_code, 200)
        res = self.api.get(self.url)
        self.assertEqual(res.status_code, 429)
