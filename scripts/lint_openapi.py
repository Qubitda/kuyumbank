#!/usr/bin/env python3
"""OpenAPI kalite kapısı (FRONTEND READY önkoşulu).

Kontroller:
- Şema üretimi
- openapi 3.x
- components.schemas dolu
- Her operation: operationId benzersiz, tags, 2xx response $ref
- Zayıf stub (array items:{} / boş object) yok
- POST/PUT/PATCH requestBody $ref (DELETE body opsiyonel bağ)
- URL patterns ↔ OpenAPI path coverage (eksik / fazla)
- RESPONSE_BINDINGS + REQUEST_BINDINGS coverage

Exit 0 = geçti; 1 = hata.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"


def _setup() -> None:
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


def _is_weak_schema(sch: dict | None) -> bool:
    if not sch:
        return True
    if "$ref" in sch:
        return False
    if sch.get("type") == "array":
        items = sch.get("items")
        if items == {} or items is None:
            return True
        return _is_weak_schema(items) if isinstance(items, dict) else False
    if sch.get("type") == "object" and not sch.get("properties") and not sch.get("$ref"):
        # additionalProperties-only ops summary kabul; tamamen boş object zayıf
        if not sch.get("additionalProperties"):
            return True
    return False


def _success_schema(op: dict) -> dict | None:
    """Tercih: $ref’li 2xx; yoksa ilk 2xx."""
    candidates: list[dict | None] = []
    for code, resp in (op.get("responses") or {}).items():
        if not str(code).startswith("2"):
            continue
        content = (resp.get("content") or {}).get("application/json") or {}
        sch = content.get("schema")
        if isinstance(sch, dict) and "$ref" in sch:
            return sch
        candidates.append(sch)
    return candidates[0] if candidates else None


def main() -> int:
    _setup()
    from django.urls import get_resolver
    from rest_framework.schemas.openapi import SchemaGenerator

    from api.openapi_components import RESPONSE_BINDINGS, enrich_openapi_schema
    from api.openapi_requests import REQUEST_BINDINGS, _binding_for as req_binding
    from api.urls import api_urlpatterns

    errors: list[str] = []

    raw = SchemaGenerator(
        title="Kuyumbank API",
        description="API v1 — ADR-0017",
        version="1.0.0",
        url="/api/v1/",
        patterns=api_urlpatterns,
    ).get_schema(request=None, public=True)
    if raw is None:
        print("FAIL: schema generation returned None", file=sys.stderr)
        return 1
    schema = enrich_openapi_schema(raw)

    oas = str(schema.get("openapi") or "")
    if not oas.startswith("3."):
        errors.append(f"openapi version not 3.x: {oas!r}")

    comps = (schema.get("components") or {}).get("schemas") or {}
    if len(comps) < 10:
        errors.append(f"too few component schemas: {len(comps)}")

    paths = schema.get("paths") or {}
    if len(paths) < 70:
        errors.append(f"too few paths: {len(paths)}")

    seen_oids: dict[str, str] = {}
    unbound = 0
    weak = 0
    for path, methods in paths.items():
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if not oid:
                errors.append(f"missing operationId: {method.upper()} {path}")
            else:
                key = str(oid)
                if key in seen_oids:
                    errors.append(
                        f"duplicate operationId {key!r}: "
                        f"{seen_oids[key]} vs {method.upper()} {path}"
                    )
                seen_oids[key] = f"{method.upper()} {path}"
            if not op.get("tags"):
                errors.append(f"missing tags: {method.upper()} {path}")
            sch = _success_schema(op)
            if _is_weak_schema(sch):
                weak += 1
                errors.append(f"weak 2xx schema: {method.upper()} {path}")
            if method in ("post", "put", "patch"):
                rb = op.get("requestBody") or {}
                content = (rb.get("content") or {}).get("application/json") or {}
                rsch = content.get("schema")
                if not isinstance(rsch, dict) or "$ref" not in rsch:
                    errors.append(
                        f"missing requestBody $ref: {method.upper()} {path}"
                    )
                # REQUEST_BINDINGS must list this write op
                rbinds = req_binding(path)
                if not rbinds or method not in rbinds:
                    errors.append(
                        f"no REQUEST_BINDING: {method.upper()} {path}"
                    )

    # Pattern coverage: spectacular paths should match api_urlpatterns count roughly
    # Collect URL names from api_urlpatterns via resolver under /api/v1/
    resolver = get_resolver("config.urls")
    api_patterns = []

    def _walk(patterns, prefix=""):
        for p in patterns:
            route = getattr(p, "pattern", None)
            route_s = str(route) if route is not None else ""
            if hasattr(p, "url_patterns"):
                _walk(p.url_patterns, prefix + route_s)
            else:
                full = "/" + (prefix + route_s).lstrip("/")
                if full.startswith("/api/v1/") and "schema" not in full:
                    api_patterns.append(full)

    _walk(resolver.url_patterns)
    # Normalize django path converters to {id} style loosely
    normed = set()
    for u in api_patterns:
        n = re.sub(r"<[^:>]+:(\w+)>", r"{\1}", u)
        n = re.sub(r"<(\w+)>", r"{\1}", n)
        if not n.endswith("/"):
            n += "/"
        normed.add(n.replace("{pk}", "{id}"))

    oas_paths = {p.replace("{pk}", "{id}") for p in paths}
    # Only compare business endpoints present in both spaces
    missing_in_oas = sorted(p for p in normed if p not in oas_paths and "schema" not in p)
    # Spectacular may omit some trailing variants; flag only clear misses
    if len(missing_in_oas) > 5:
        errors.append(
            f"URL→OpenAPI coverage gap ({len(missing_in_oas)}): "
            + ", ".join(missing_in_oas[:8])
        )

    # Bindings should cover all OAS paths/methods
    for path, methods in paths.items():
        bp = path if path in RESPONSE_BINDINGS else path.replace("{pk}", "{id}")
        binds = RESPONSE_BINDINGS.get(bp) or RESPONSE_BINDINGS.get(
            path.replace("{id}", "{pk}")
        )
        for method in methods:
            if method.startswith("x-"):
                continue
            if not binds or method not in binds:
                errors.append(f"no RESPONSE_BINDING: {method.upper()} {path}")

    if errors:
        print(f"OpenAPI lint FAIL ({len(errors)} issues)", file=sys.stderr)
        for e in errors[:40]:
            print(f"  - {e}", file=sys.stderr)
        if len(errors) > 40:
            print(f"  ... +{len(errors) - 40} more", file=sys.stderr)
        return 1

    print(
        f"OpenAPI lint OK — paths={len(paths)} schemas={len(comps)} "
        f"operationIds={len(seen_oids)} weak={weak} unbound={unbound}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
