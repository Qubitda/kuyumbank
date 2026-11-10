"""HTML login yüzeyleri — LoginThrottleMiddleware."""

from django.core.cache import cache
from django.test import Client, TestCase, override_settings


@override_settings(LOGIN_THROTTLE_RATE="3/min")
class LoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_buyer_login_throttle_429(self):
        c = Client()
        for _ in range(3):
            r = c.post("/buyer/login/", {"username": "x", "password": "y"})
            self.assertNotEqual(r.status_code, 429)
        blocked = c.post("/buyer/login/", {"username": "x", "password": "y"})
        self.assertEqual(blocked.status_code, 429)

    def test_get_login_not_throttled(self):
        c = Client()
        for _ in range(5):
            r = c.get("/buyer/login/")
            self.assertEqual(r.status_code, 200)
