#!/usr/bin/env python
"""ADIM 0 helper: dump Django URL routes + OpenAPI ops for docs/_audit."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.urls import get_resolver  # noqa: E402
from rest_framework.views import APIView  # noqa: E402


def iter_patterns(patterns, prefix=""):
    for p in patterns:
        if hasattr(p, "url_patterns"):
            yield from iter_patterns(p.url_patterns, prefix + str(p.pattern))
        else:
            yield prefix + str(p.pattern), p


def http_methods(callback):
    view = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    if view is None:
        return ["?"], None, None
    methods = []
    for m in ("get", "post", "put", "patch", "delete", "head", "options"):
        if hasattr(view, m) and callable(getattr(view, m)):
            # APIView always has options/head via mixins sometimes; skip pure APIView defaults
            if m in ("options",) and getattr(view, m) is getattr(APIView, m, None):
                continue
            methods.append(m.upper())
    if not methods:
        methods = ["?"]
    # permission classes
    perms = getattr(view, "permission_classes", None)
    auth = getattr(view, "authentication_classes", None)
    perm_names = [getattr(c, "__name__", str(c)) for c in (perms or [])]
    auth_names = [getattr(c, "__name__", str(c)) for c in (auth or [])]
    return methods, view.__module__ + "." + view.__name__, (perm_names, auth_names)


def main():
    resolver = get_resolver()
    rows = []
    for path, pattern in iter_patterns(resolver.url_patterns):
        cb = getattr(pattern, "callback", None)
        if cb is None:
            continue
        name = getattr(pattern, "name", None) or ""
        methods, handler, auth_info = http_methods(cb)
        perms, auths = auth_info or ([], [])
        # Only API-ish routes
        if not (path.startswith("api/") or path.startswith("act-as/") or path.startswith("admin/")):
            continue
        if path.startswith("admin/") and "api" not in path:
            continue
        rows.append(
            {
                "path": "/" + path.lstrip("/"),
                "methods": methods,
                "name": name,
                "handler": handler or str(cb),
                "permission_classes": perms,
                "authentication_classes": auths,
            }
        )

    openapi_path = ROOT / "docs" / "api" / "openapi-v1.json"
    openapi = json.loads(openapi_path.read_text(encoding="utf-8"))
    oa_ops = []
    for p, methods in sorted(openapi.get("paths", {}).items()):
        for m, op in methods.items():
            if m.startswith("x-"):
                continue
            oa_ops.append(
                {
                    "method": m.upper(),
                    "path": p,
                    "operationId": op.get("operationId", ""),
                    "tags": op.get("tags") or [],
                    "security": op.get("security", openapi.get("security")),
                    "requestBody": "requestBody" in op,
                    "responses": sorted(op.get("responses", {}).keys()),
                }
            )

    out = {
        "django_routes": rows,
        "openapi_ops": oa_ops,
        "counts": {
            "django_api_routes": len(rows),
            "openapi_paths": len(openapi.get("paths", {})),
            "openapi_ops": len(oa_ops),
        },
    }
    out_path = ROOT / "docs" / "_audit" / "_raw_inventory.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out["counts"], indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
