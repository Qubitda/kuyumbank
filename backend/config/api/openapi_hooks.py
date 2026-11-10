"""drf-spectacular postprocess — presenter DTO enjeksiyonu."""

from __future__ import annotations


def spectacular_postprocess(result, generator, request, public):
    from api.openapi_components import enrich_openapi_schema

    return enrich_openapi_schema(result)
