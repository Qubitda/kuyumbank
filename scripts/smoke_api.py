#!/usr/bin/env python
"""API smoke — rol bazlı OpenAPI matrisi + opsiyonel canlı HTTP.

Varsayılan (Django Client / TestCase):
  cd backend/config
  python ../../scripts/smoke_api.py --matrix

  → api.tests.test_openapi_smoke_matrix (enforce_csrf_checks, anon/wrong_role/
    invalid_body/success) + docs/_audit/smoke-matrix-results.json +
    endpoint-readiness.md yeniden üretilir.

Canlı sunucu (yalnız anon kapı — seed yok):
  python ../../scripts/smoke_api.py --base http://127.0.0.1:8000

Exit: 0 OK · 1 fail · 2 not runnable.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"
AUDIT = ROOT / "docs" / "_audit"


def run_matrix() -> int:
    """Rol bazlı kanıt: Django test → readiness dosyaları test tarafından yazılır."""
    cmd = [
        sys.executable,
        "manage.py",
        "test",
        "api.tests.test_openapi_smoke_matrix",
        "--keepdb",
        "-v1",
    ]
    print("SMOKE MATRIX:", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(BACKEND))
    results_path = AUDIT / "smoke-matrix-results.json"
    readiness_path = AUDIT / "endpoint-readiness.md"
    summary: dict[str, Any] = {
        "mode": "django.test.matrix",
        "exit_code": proc.returncode,
        "results_file": str(results_path.relative_to(ROOT)) if results_path.exists() else None,
        "readiness_file": str(readiness_path.relative_to(ROOT))
        if readiness_path.exists()
        else None,
    }
    if results_path.exists():
        try:
            data = json.loads(results_path.read_text(encoding="utf-8"))
            summary.update(
                {
                    "ok": bool(data.get("ok")),
                    "openapi_ops": data.get("openapi_ops"),
                    "passed": data.get("passed"),
                    "failed": data.get("failed"),
                    "total_checks": data.get("total_checks"),
                }
            )
        except json.JSONDecodeError as exc:
            summary["ok"] = False
            summary["error"] = f"JSONDecodeError: {exc}"
    else:
        summary["ok"] = False
        summary["error"] = "smoke-matrix-results.json missing after test"
    out = AUDIT / "smoke-results.json"
    AUDIT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if proc.returncode != 0:
        return 1
    return 0 if summary.get("ok") else 1


def use_django_client_anon() -> tuple[list[dict[str, Any]], str]:
    """Hafif anon kapı (matrix dışı hızlı smoke)."""
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.test import Client, override_settings

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

    hit("GET", "/api/v1/health/", {200})
    hit("GET", "/api/v1/auth/csrf/", {200})
    hit("GET", "/api/v1/me/", {401, 403})
    hit("GET", "/api/v1/catalog/", {401, 403})
    hit("GET", "/api/v1/orders/", {401, 403})
    hit("POST", "/api/v1/auth/login/", {400, 401, 403}, data={}, content_type="application/json")
    hit("POST", "/api/v1/health/", {405})
    hit("GET", "/api/v1/this-route-does-not-exist/", {404})
    hit("GET", "/api/schema/", {200, 401, 403})
    hit("GET", "/buyer/", {404})
    hit("GET", "/supplier/", {404})
    hit("GET", "/ops/", {404})
    hit("GET", "/api/v1/me/profile/", {401, 403})
    hit("GET", "/api/v1/me/addresses/", {401, 403})
    hit("GET", "/api/v1/supplier/offers/", {401, 403})
    return results, "django.test.Client.anon"


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
    hit("GET", "/api/v1/me/profile/", {401, 403})
    return results, "http:" + base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix",
        action="store_true",
        default=True,
        help="Rol bazlı OpenAPI smoke matrix (varsayılan)",
    )
    parser.add_argument(
        "--anon-only",
        action="store_true",
        help="Yalnız anon kapı (matrix atla)",
    )
    parser.add_argument("--base", default="", help="Live server base URL")
    parser.add_argument(
        "--out",
        default=str(AUDIT / "smoke-results.json"),
        help="JSON results path",
    )
    args = parser.parse_args()

    if args.base:
        try:
            results, mode = use_http(args.base)
        except Exception as exc:  # noqa: BLE001
            payload = {
                "ok": False,
                "runnable": False,
                "reason": type(exc).__name__ + ": " + str(exc)[:300],
                "results": [],
                "note": "Live HTTP anon-only; rol matrisi --matrix ile Client üzerinden",
            }
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
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
            "note": "Live HTTP = anon kapı; tam rol matrisi Django Client --matrix",
        }
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps({k: payload[k] for k in ("ok", "mode", "passed", "failed", "total")}, indent=2))
        for r in failed:
            print("FAIL", r)
        return 0 if not failed else 1

    if args.anon_only:
        try:
            results, mode = use_django_client_anon()
        except Exception as exc:  # noqa: BLE001
            print("SMOKE NOT RUNNABLE:", exc)
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
        Path(args.out).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps({k: payload[k] for k in ("ok", "mode", "passed", "failed", "total")}, indent=2))
        return 0 if not failed else 1

    return run_matrix()


if __name__ == "__main__":
    raise SystemExit(main())
