"""F8-002 — request_id middleware + secret redact."""

import json
import logging

from django.test import Client, SimpleTestCase, TestCase, override_settings

from config.logging_utils import (
    StructuredFormatter,
    redact_mapping,
    scrub_message,
)


class RedactUnitTests(SimpleTestCase):
    def test_redact_mapping_masks_secrets(self):
        out = redact_mapping(
            {
                "user": "a",
                "password": "secret123",
                "nested": {"api_key": "xyz", "ok": 1},
            }
        )
        self.assertEqual(out["user"], "a")
        self.assertEqual(out["password"], "***")
        self.assertEqual(out["nested"]["api_key"], "***")
        self.assertEqual(out["nested"]["ok"], 1)

    def test_scrub_bearer(self):
        self.assertIn("***", scrub_message("Authorization: Bearer abc.def"))
        self.assertNotIn("abc.def", scrub_message("Authorization: Bearer abc.def"))

    def test_structured_formatter_json_and_request_id(self):
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello Bearer tokensecret",
            args=(),
            exc_info=None,
        )
        record.request_id = "rid-1"
        record.password = "should-not-dump"
        line = StructuredFormatter().format(record)
        data = json.loads(line)
        self.assertEqual(data["request_id"], "rid-1")
        self.assertNotIn("tokensecret", data["msg"])
        self.assertIn("password", data.get("redacted_keys", []))


@override_settings(ROOT_URLCONF="config.urls")
class RequestIdMiddlewareTests(TestCase):
    def test_generates_and_echoes_request_id(self):
        client = Client()
        res = client.get("/api/v1/health/")
        self.assertIn(res.status_code, (200, 401, 403))
        self.assertTrue(res.get("X-Request-ID"))

    def test_accepts_client_request_id(self):
        client = Client()
        res = client.get("/api/v1/health/", HTTP_X_REQUEST_ID="client-rid-42")
        self.assertEqual(res["X-Request-ID"], "client-rid-42")
