#!/usr/bin/env python
"""API smoke: route reachability + auth gate (no secrets printed).

Usage (from repo root, with backend env):
  cd backend/config
  python ../../scripts/smoke_api.py
  python ../../scripts/smoke_api.py --base http://127.0.0.1:8000

Exit 0 = all checks passed; 1 = failures; 2 = could not run (env/server).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"


def use_django_client() -> tuple[list[dict[str, Any]], str]:
    """In-process Django test client (no live server required)."""
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.test import Client, override_settings

    # Client host is "testserver"; production ALLOWED_HOSTS often omits it.
    hosts = list(settings.ALLOWED_HOSTS) + ["testserver", "localhost", "127.0.0.1"]
    results: list[dict[str, Any]] = []

    def hit(method: str, path: str, expect: set[int], **kwargs):
        with override_settings(ALLOWED_HOSTS=hosts):
            c = Client()
            fn = getattr(c, method.lower())
            try:
                r = fn(path, **kwargs)
                status = r.status_code
                ok = status in expect
                results.append(
                    {
                        "method": method,
                        "path": path,
                        "status": status,
                        "expect": sorted(expect),
                        "ok": ok,
                        "mode": "django.test.Client",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "method": method,
                        "path": path,
                        "status": None,
                        "expect": sorted(expect),
                        "ok": False,
                        "error": type(exc).__name__ + ": " + str(exc)[:120],
                        "mode": "django.test.Client",
                    }
                )

    # Public / anon
    hit("GET", "/api/v1/health/", {200})
    hit("GET", "/api/v1/auth/csrf/", {200})
    hit("GET", "/api/v1/me/", {401, 403})
    hit("GET", "/api/v1/catalog/", {401, 403})
    hit("GET", "/api/v1/orders/", {401, 403})
    hit("POST", "/api/v1/auth/login/", {400, 401, 403}, data={}, content_type="application/json")
    # Wrong method
    hit("POST", "/api/v1/health/", {405})
    # Unknown
    hit("GET", "/api/v1/this-route-does-not-exist/", {404})
    # Meta docs (may be 200 DEBUG or 401/403 if locked)
    hit("GET", "/api/schema/", {200, 401, 403})
    hit("GET", "/api/docs/", {200, 401, 403})
    # Deprecated HTML portal
    hit("GET", "/buyer/", {404})
    hit("GET", "/supplier/", {404})
    hit("GET", "/ops/", {404})
    # Act-as API exists
    hit("POST", "/api/v1/act-as/stop/", {401, 403}, data={}, content_type="application/json")
    hit("GET", "/api/v1/me/dashboard/", {401, 403})

    return results, "django.test.Client"


def use_http(base: str) -> tuple[list[dict[str, Any]], str]:
    import urllib.error
    import urllib.request

    results: list[dict[str, Any]] = []

    def hit(method: str, path: str, expect: set[int], body: bytes | None = None):
        url = base.rstrip("/") + path
        req = urllib.request.Request(url, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "method": method,
                    "path": path,
                    "status": None,
                    "expect": sorted(expect),
                    "ok": False,
                    "error": type(exc).__name__ + ": " + str(exc)[:120],
                    "mode": "http",
                }
            )
            return
        results.append(
            {
                "method": method,
                "path": path,
                "status": status,
                "expect": sorted(expect),
                "ok": status in expect,
                "mode": "http",
            }
        )

    hit("GET", "/api/v1/health/", {200})
    hit("GET", "/api/v1/auth/csrf/", {200})
    hit("GET", "/api/v1/me/", {401, 403})
    hit("GET", "/api/v1/catalog/", {401, 403})
    hit("POST", "/api/v1/health/", {405})
    hit("GET", "/api/v1/this-route-does-not-exist/", {404})
    hit("GET", "/buyer/", {404})
    return results, "http:" + base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="", help="Live server base URL; empty = Django test client")
    parser.add_argument(
        "--out",
        default=str(ROOT / "docs" / "_audit" / "smoke-results.json"),
        help="JSON results path",
    )
    args = parser.parse_args()

    try:
        if args.base:
            results, mode = use_http(args.base)
        else:
            results, mode = use_django_client()
    except Exception as exc:  # noqa: BLE001
        payload = {
            "ok": False,
            "runnable": False,
            "reason": type(exc).__name__ + ": " + str(exc)[:300],
            "results": [],
        }
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("SMOKE NOT RUNNABLE:", payload["reason"])
        return 2

    failed = [r for r in results if not r.get("ok")]
    payload = {
        "ok": not failed,
        "runnable": True,
        "mode": mode,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "total": len(results),
        "results": results,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("ok", "runnable", "mode", "passed", "failed", "total")}, indent=2))
    for r in failed:
        print("FAIL", r)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
