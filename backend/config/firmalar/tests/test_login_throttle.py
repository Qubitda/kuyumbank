"""Admin login — LoginThrottleMiddleware (IP + username); ADR-0029."""

from django.core.cache import cache
from django.test import Client, TestCase, override_settings


@override_settings(
    LOGIN_THROTTLE_RATE="3/min",
    LOGIN_THROTTLE_USERNAME_RATE="100/min",
    TRUSTED_PROXY_COUNT=1,
)
class LoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_admin_login_throttle_429(self):
        c = Client()
        for _ in range(3):
            r = c.post("/admin/login/", {"username": "x", "password": "y"})
            self.assertNotEqual(r.status_code, 429)
        blocked = c.post("/admin/login/", {"username": "x", "password": "y"})
        self.assertEqual(blocked.status_code, 429)

    def test_get_login_not_throttled(self):
        c = Client()
        for _ in range(5):
            r = c.get("/admin/login/")
            self.assertEqual(r.status_code, 200)

    def test_trusted_proxy_uses_forwarded_client(self):
        """REMOTE_ADDR proxy iken sayaç XFF client IP üzerinden gider."""
        c = Client()
        xff = "203.0.113.50, 10.0.0.1"
        extra = {
            "REMOTE_ADDR": "10.0.0.1",
            "HTTP_X_FORWARDED_FOR": xff,
        }
        for i in range(3):
            r = c.post(
                "/admin/login/",
                {"username": f"u{i}", "password": "y"},
                **extra,
            )
            self.assertNotEqual(r.status_code, 429)
        blocked = c.post(
            "/admin/login/",
            {"username": "uX", "password": "y"},
            **extra,
        )
        self.assertEqual(blocked.status_code, 429)


@override_settings(
    LOGIN_THROTTLE_RATE="1000/min",
    LOGIN_THROTTLE_USERNAME_RATE="2/min",
)
class LoginUsernameThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_username_bucket_blocks_distributed_guess(self):
        c = Client()
        self.assertNotEqual(
            c.post(
                "/admin/login/",
                {"username": "victim", "password": "a"},
                REMOTE_ADDR="198.51.100.1",
            ).status_code,
            429,
        )
        self.assertNotEqual(
            c.post(
                "/admin/login/",
                {"username": "victim", "password": "b"},
                REMOTE_ADDR="198.51.100.2",
            ).status_code,
            429,
        )
        blocked = c.post(
            "/admin/login/",
            {"username": "victim", "password": "c"},
            REMOTE_ADDR="198.51.100.3",
        )
        self.assertEqual(blocked.status_code, 429)
