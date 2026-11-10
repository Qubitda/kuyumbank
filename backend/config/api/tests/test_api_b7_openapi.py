"""API-B7 — OpenAPI dondurma smoke + DTO bileşenleri."""

from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.schemas.openapi import SchemaGenerator

from api.openapi_components import enrich_openapi_schema
from api.urls import api_urlpatterns


class ApiB7OpenApiFreezeTests(SimpleTestCase):
    def test_schema_paths_no_double_prefix_covers_b1_b6(self):
        schema = enrich_openapi_schema(
            SchemaGenerator(
                title="Kuyumbank API",
                description="API v1 — ADR-0017",
                version="1.0.0",
                url="/api/v1/",
                patterns=api_urlpatterns,
            ).get_schema(request=None, public=True)
        )
        self.assertIsNotNone(schema)
        paths = schema["paths"]
        keys = list(paths.keys())
        self.assertGreaterEqual(len(keys), 70)
        double = [p for p in keys if p.count("/api/v1") >= 2]
        self.assertEqual(double, [], msg=f"çift önek: {double[:5]}")
        required = (
            "/api/v1/me/",
            "/api/v1/catalog/",
            "/api/v1/checkouts/",
            "/api/v1/orders/",
            "/api/v1/finance/me/",
            "/api/v1/rfqs/",
            "/api/v1/ops/inspections/",
            "/api/v1/ops/shipments/",
            "/api/v1/supplier/offers/",
            "/api/v1/supplier/stock/adjustments/",
            "/api/v1/supplier/rfqs/",
        )
        for path in required:
            self.assertIn(path, paths, msg=f"eksik path: {path}")
        comps = schema["components"]["schemas"]
        self.assertIn("MeResponse", comps)
        self.assertIn("BuyerCatalogDetail", comps)
        self.assertIn("ProblemDetail", comps)
        me_schema = (
            schema["paths"]["/api/v1/me/"]["get"]["responses"]["200"]["content"][
                "application/json"
            ]["schema"]
        )
        self.assertEqual(me_schema.get("$ref"), "#/components/schemas/MeResponse")
        self.assertTrue(str(schema.get("openapi", "")).startswith("3."))
        login_rb = schema["paths"]["/api/v1/auth/login/"]["post"]["requestBody"]
        self.assertEqual(
            login_rb["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/LoginRequest",
        )
        self.assertIn("LoginRequest", comps)
        self.assertIn("EmptyRequest", comps)
        self.assertIn("ReasonRequest", comps)
