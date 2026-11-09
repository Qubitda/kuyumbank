"""API-B7 — OpenAPI dondurma smoke: çift önek yok; B1–B6 path’ler var."""

from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.schemas.openapi import SchemaGenerator

from api.urls import api_urlpatterns


class ApiB7OpenApiFreezeTests(SimpleTestCase):
    def test_schema_paths_no_double_prefix_covers_b1_b6(self):
        schema = SchemaGenerator(
            title="Kuyumbank API",
            description="API v1 — ADR-0017",
            version="1.0.0",
            url="/api/v1/",
            patterns=api_urlpatterns,
        ).get_schema(request=None, public=True)
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
