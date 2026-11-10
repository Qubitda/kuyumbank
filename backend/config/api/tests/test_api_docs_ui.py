"""TECH-OPENAPI-02 — schema / Swagger / ReDoc erişimi."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient


@override_settings(DEBUG=True, API_DOCS_PUBLIC=False)
class ApiDocsUiTests(SimpleTestCase):
    def setUp(self):
        self.api = APIClient()

    def test_schema_json_has_components(self):
        res = self.api.get("/api/schema/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(str(body.get("openapi", "")).startswith("3."))
        self.assertIn("MeResponse", body.get("components", {}).get("schemas", {}))
        self.assertIn("/api/v1/me/", body.get("paths", {}))

    def test_swagger_ui(self):
        res = self.api.get("/api/docs/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"swagger", res.content.lower())

    def test_redoc_ui(self):
        res = self.api.get("/api/redoc/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"redoc", res.content.lower())


@override_settings(DEBUG=False, API_DOCS_PUBLIC=False)
class ApiDocsProdGateTests(SimpleTestCase):
    def test_schema_requires_auth_when_not_public(self):
        api = APIClient()
        res = api.get("/api/schema/")
        self.assertIn(res.status_code, (401, 403))
