"""F8-003 — Sentry init + before_send scrub."""

from django.test import SimpleTestCase, override_settings

from config.sentry_init import init_sentry, sentry_before_send


class SentryF8003Tests(SimpleTestCase):
    def test_empty_dsn_noop(self):
        self.assertFalse(init_sentry(dsn=""))
        self.assertFalse(init_sentry(dsn="   "))

    def test_before_send_redacts_secrets(self):
        event = {
            "message": "Authorization: Bearer super-secret-token",
            "request": {
                "headers": {"Authorization": "Bearer abc", "X-Ok": "1"},
                "data": {"password": "p", "sku": "SKU-1"},
                "cookies": {"sessionid": "x", "token": "t"},
                "query_string": "token=leak",
            },
            "extra": {"api_key": "k", "path": "/ok"},
        }
        out = sentry_before_send(event, {})
        self.assertIn("***", out["message"])
        self.assertEqual(out["request"]["headers"]["Authorization"], "***")
        self.assertEqual(out["request"]["headers"]["X-Ok"], "1")
        self.assertEqual(out["request"]["data"]["password"], "***")
        self.assertEqual(out["request"]["data"]["sku"], "SKU-1")
        self.assertEqual(out["extra"]["api_key"], "***")
        self.assertEqual(out["extra"]["path"], "/ok")

    @override_settings(SENTRY_DSN="")
    def test_settings_import_without_dsn(self):
        from django.conf import settings

        self.assertFalse(bool(getattr(settings, "SENTRY_DSN", "")))
