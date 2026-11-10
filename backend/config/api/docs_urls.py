"""OpenAPI meta: /api/schema/ · /api/docs/ · /api/redoc/

Şema: DRF+enrich (`EnrichedOpenAPISchemaView`).
UI: drf-spectacular Swagger/ReDoc (aynı schema URL).
"""

from django.urls import path
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView

from api.docs_access import docs_permission_classes
from api.schema_views import EnrichedOpenAPISchemaView


class _DocsSwaggerView(SpectacularSwaggerView):
    authentication_classes = []

    def get_permissions(self):
        return [perm() for perm in docs_permission_classes()]


class _DocsRedocView(SpectacularRedocView):
    authentication_classes = []

    def get_permissions(self):
        return [perm() for perm in docs_permission_classes()]


urlpatterns = [
    path(
        "schema/",
        EnrichedOpenAPISchemaView.as_view(),
        name="openapi-schema",
    ),
    path(
        "docs/",
        _DocsSwaggerView.as_view(url_name="openapi-schema"),
        name="openapi-docs",
    ),
    path(
        "redoc/",
        _DocsRedocView.as_view(url_name="openapi-schema"),
        name="openapi-redoc",
    ),
]
