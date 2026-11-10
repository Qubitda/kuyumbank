"""OpenAPI JSON — DRF SchemaGenerator + presenter DTO enrich.

drf-spectacular APIView’lerde serializer bulamayınca uçları şemadan düşürür;
bu yüzden path keşfi DRF generator ile yapılır. Swagger/ReDoc aynı URL’yi tüketir.
"""

from __future__ import annotations

from rest_framework.response import Response
from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.views import APIView

from api.docs_access import docs_permission_classes
from api.openapi_components import enrich_openapi_schema


class EnrichedOpenAPISchemaView(APIView):
    """GET — OpenAPI 3.x JSON (enrich edilmiş)."""

    authentication_classes = []  # docs_access kendi kararını verir

    def get_permissions(self):
        # override_settings(DEBUG=…) testte sınıf attribute’unu dondurmaz
        return [perm() for perm in docs_permission_classes()]

    def get(self, request, *args, **kwargs):
        # Geç import: api.urls ↔ schema_views döngüsünü kır
        from api.urls import api_urlpatterns

        # public=True: generator auth istemez; HTTP erişim permission_classes’ta
        generator = SchemaGenerator(
            title="Kuyumbank API",
            description="API v1 — ADR-0017",
            version="1.0.0",
            url="/api/v1/",
            patterns=api_urlpatterns,
        )
        schema = generator.get_schema(request=None, public=True)
        if schema is None:
            return Response({"detail": "Schema üretilemedi."}, status=500)
        return Response(enrich_openapi_schema(schema))


# SpectacularSwaggerView url_name çözümlemesi için aynı view sınıfı
OpenAPISchemaView = EnrichedOpenAPISchemaView
