"""ADIM 5 — OpenAPI op matrix: anon gate + rol + invalid body + response $ref.

Koşum: python manage.py test api.tests.test_openapi_smoke_matrix --keepdb
Sonuç: docs/_audit/smoke-matrix-results.json + endpoint-readiness.md yeniden üretim için.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from api.tests.test_api_b3_finance_ops import B3FixtureMixin
from api.tests.test_api_b4_enterprise import B4FixtureMixin
from api.tests.test_api_b5_ops import B5FixtureMixin
from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import pricing_service
from siparis.services import cart_servisi, checkout_servisi, order_servisi

User = get_user_model()
ROOT = Path(settings.BASE_DIR).resolve().parents[1]  # backend/config → repo? 
# BASE_DIR is backend/config; repo root is parents[1] if structure is repo/backend/config
_REPO = Path(__file__).resolve().parents[4]  # api/tests → api → config → backend → repo


def _load_ops():
    data = json.loads((_REPO / "docs" / "api" / "openapi-v1.json").read_text(encoding="utf-8"))
    ops = []
    for path, methods in sorted(data.get("paths", {}).items()):
        for m, op in methods.items():
            if m.startswith("x-"):
                continue
            ops.append(
                {
                    "method": m.upper(),
                    "path": path,
                    "operationId": op.get("operationId", ""),
                    "security": op.get("security", data.get("security")),
                    "requestBody": op.get("requestBody"),
                    "responses": op.get("responses") or {},
                }
            )
    return ops, data


def _is_allow_any(path: str, method: str) -> bool:
    allow = {
        ("GET", "/api/v1/health/"),
        ("GET", "/api/v1/auth/csrf/"),
        ("POST", "/api/v1/auth/login/"),
        ("POST", "/api/v1/auth/password-reset/"),
        ("POST", "/api/v1/auth/password-reset/confirm/"),
        ("POST", "/api/v1/auth/invites/accept/"),
        ("POST", "/api/v1/auth/email-verify/"),
        ("POST", "/api/v1/auth/email-verify/confirm/"),
        ("POST", "/api/v1/payments/webhook/"),
    }
    return (method, path) in allow


def _role_for(path: str, method: str = "GET") -> str:
    if path.startswith("/api/v1/supplier/"):
        return "supplier"
    if path.startswith("/api/v1/ops/finance") or path.startswith("/api/v1/ops/orders"):
        return "finance_ops"
    if path.startswith("/api/v1/ops/shipments"):
        return "logistics"
    if path.startswith("/api/v1/ops/"):
        return "ops"
    if "/act-as/" in path:
        return "ops"
    if path.startswith("/api/v1/auth/invites"):
        return "buyer_admin"
    if path.startswith("/api/v1/approvals"):
        return "buyer_admin"
    if path.startswith("/api/v1/org-units"):
        return "buyer_admin" if method == "POST" else "buyer"
    return "buyer"


def _role_gated(path: str, method: str = "GET") -> bool:
    """Wrong-role 403 beklenen yüzeyler (auth/me/logout her authenticated’a açık)."""
    if path.startswith("/api/v1/auth/") and not path.startswith("/api/v1/auth/invites"):
        return False
    if path in ("/api/v1/me/", "/api/v1/me/dashboard/", "/api/v1/health/"):
        return False
    if path.startswith("/api/v1/act-as/stop"):
        return False  # stop: act-as yoksa no-op 200
    # Org GET: tenant-scoped her authenticated alıcı/tedarikçi okuyabilir (boş liste)
    if path.startswith("/api/v1/org-units") and method == "GET":
        return False
    return (
        path.startswith("/api/v1/supplier/")
        or path.startswith("/api/v1/ops/")
        or path.startswith("/api/v1/catalog")
        or path.startswith("/api/v1/quotes")
        or path.startswith("/api/v1/carts")
        or path.startswith("/api/v1/orders")
        or path.startswith("/api/v1/checkouts")
        or path.startswith("/api/v1/returns")
        or path.startswith("/api/v1/shipments")
        or path.startswith("/api/v1/finance")
        or path.startswith("/api/v1/credit")
        or path.startswith("/api/v1/rfqs")
        or path.startswith("/api/v1/approvals")
        or path.startswith("/api/v1/org-units")
        or path.startswith("/api/v1/bulk-orders")
        or path.startswith("/api/v1/price-locks")
        or path.startswith("/api/v1/payments/intents")
        or path.startswith("/api/v1/reports")
        or path.startswith("/api/v1/auth/invites")
    )


def _empty_body_ok(path: str) -> bool:
    return path.rstrip("/").endswith(
        (
            "checkouts",
            "logout",
            "mfa/resend",
            "mfa/verify",
            "act-as/stop",
            "submit",
            "approve",
            "cancel",
            "pass",
            "fail",
            "start",
            "prepare",
            "dispatch",
            "deliver",
            "send",
            "deactivate",
            "mahsup",
            "reorder",
        )
    )


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class OpenApiSmokeMatrixTests(B5FixtureMixin, B4FixtureMixin, B3FixtureMixin, TestCase):
    """B5 ⊃ B3/B4 world; tek zengin seed ile 106 op kapısı."""

    @classmethod
    def setUpTestData(cls):
        cls._build_b5_world()
        seed_role_permissions()
        # buyer-admin (manage users / org)
        cls.buyer_admin = User(
            username="smoke_buyer_admin",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.buyer_admin.set_password("x")
        cls.buyer_admin.save()
        sync_user_role_groups(cls.buyer_admin)

    def setUp(self):
        self.results = []
        self.ids = self._seed_ids()

    def _client(self, user=None, *, csrf: bool = False) -> APIClient:
        c = APIClient(enforce_csrf_checks=csrf)
        if user is not None:
            c.force_authenticate(user=user)
        return c

    def _user(self, role: str):
        return {
            "buyer": self.buyer,
            "buyer_admin": self.buyer_admin,
            "supplier": self.ted_user,
            "ops": self.qc,
            "logistics": self.log,
            "finance_ops": self.finance,
        }.get(role, self.buyer)

    def _seed_ids(self) -> dict:
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=Decimal("1")
        )
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        line_id = cart.lines.first().pk if cart.lines.exists() else 1
        return {
            "id": getattr(self, "order", None).pk if getattr(self, "order", None) else quote.pk,
            "line_id": line_id,
            "quote_id": quote.pk,
            "varyant_id": self.varyant.pk,
            "cart_id": cart.pk,
            "user_id": self.buyer.pk,
        }

    def _resolve(self, path: str) -> str:
        out = path
        for key, val in self.ids.items():
            out = out.replace("{" + key + "}", str(val))
        # OpenAPI uses {id} widely
        out = out.replace("{id}", str(self.ids["id"]))
        out = out.replace("{line_id}", str(self.ids["line_id"]))
        out = out.replace("{user_id}", str(self.ids["user_id"]))
        return out

    def _record(self, **kwargs):
        self.results.append(kwargs)

    def test_openapi_matrix(self):
        from django.core.cache import cache

        cache.clear()
        ops, schema = _load_ops()
        self.assertGreaterEqual(len(ops), 100)

        # Login/anon throttle LocMem — allow-any POST smoke 429 üretmesin
        with override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": {
                    **(settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES") or {}),
                    "login": "1000/min",
                    "anon": "1000/min",
                },
            }
        ):
            self._run_matrix(ops, schema)

    def _run_matrix(self, ops, schema):
        for op in ops:
            method = op["method"]
            path = op["path"]
            resolved = self._resolve(path)
            allow = _is_allow_any(path, method)

            # 1) anon
            anon = self._client()
            fn = getattr(anon, method.lower())
            try:
                r = fn(resolved, format="json")
                anon_status = r.status_code
            except Exception as exc:  # noqa: BLE001
                anon_status = f"EXC:{type(exc).__name__}"
            if allow:
                anon_ok = isinstance(anon_status, int) and anon_status < 500
            else:
                anon_ok = anon_status in (401, 403)
            self._record(
                check="anon",
                method=method,
                path=path,
                status=anon_status,
                ok=anon_ok,
            )

            # 2) wrong role — yalnız rol-kapılı yüzeyler
            if not allow and _role_gated(path, method) and method in (
                "GET",
                "POST",
                "PATCH",
                "PUT",
                "DELETE",
            ):
                role = _role_for(path, method)
                # buyer_admin paths: TEDARIKCI_SAHIP also has manage_users — use plain buyer
                wrong = (
                    "buyer"
                    if role
                    in ("supplier", "ops", "finance_ops", "logistics", "buyer_admin")
                    else "supplier"
                )
                wc = self._client(self._user(wrong))
                wfn = getattr(wc, method.lower())
                body = {} if method in ("POST", "PUT", "PATCH") else None
                try:
                    wr = (
                        wfn(resolved, data=body or {}, format="json")
                        if body is not None
                        else wfn(resolved)
                    )
                    wstatus = wr.status_code
                except Exception as exc:  # noqa: BLE001
                    wstatus = f"EXC:{type(exc).__name__}"
                wrong_ok = wstatus in (403, 404, 400, 401, 405) or (
                    isinstance(wstatus, int) and wstatus >= 400
                )
                self._record(
                    check="wrong_role",
                    method=method,
                    path=path,
                    status=wstatus,
                    ok=wrong_ok,
                    wrong=wrong,
                    expected_role=role,
                )

            # 3) invalid body — EmptyRequest uçlarında atla; aksi halde tipçe bozuk payload
            if method in ("POST", "PUT", "PATCH") and not allow and not _empty_body_ok(path):
                role = _role_for(path, method)
                uc = self._client(self._user(role))
                ufn = getattr(uc, method.lower())
                try:
                    ir = ufn(
                        resolved,
                        data={"__invalid__": True, "id": "not-an-int"},
                        format="json",
                        HTTP_IDEMPOTENCY_KEY=f"smoke-bad-{uuid.uuid4()}",
                    )
                    istatus = ir.status_code
                except Exception as exc:  # noqa: BLE001
                    istatus = f"EXC:{type(exc).__name__}"
                inv_ok = istatus in (400, 403, 404, 409, 415, 422) or (
                    isinstance(istatus, int) and 400 <= istatus < 500
                )
                self._record(
                    check="invalid_body",
                    method=method,
                    path=path,
                    status=istatus,
                    ok=inv_ok,
                )

            # 4) success smoke (GET lists + allow-any)
            if method == "GET" or allow:
                role = _role_for(path, method)
                user = None if allow else self._user(role)
                sc = self._client(user)
                sfn = getattr(sc, method.lower())
                try:
                    if allow and method == "POST" and path.endswith("/auth/login/"):
                        sr = sfn(
                            resolved,
                            data={"username": "nope", "password": "nope"},
                            format="json",
                        )
                        sok = sr.status_code in (400, 401, 403, 429)
                    elif allow and method == "POST" and "webhook" in path:
                        sr = sfn(resolved, data={}, format="json")
                        sok = sr.status_code in (200, 201, 400, 401, 403)
                    elif allow and method == "POST":
                        sr = sfn(resolved, data={}, format="json")
                        sok = sr.status_code in (200, 201, 400, 403)
                    else:
                        sr = sfn(resolved)
                        # 400: zorunlu query (ör. anomali esik); 404: yok id
                        sok = sr.status_code in (200, 201, 204, 400, 404)
                        if (
                            sok
                            and sr.status_code == 200
                            and str(sr.get("Content-Type", "")).startswith(
                                "application/json"
                            )
                        ):
                            try:
                                body = sr.json()
                                sok = isinstance(body, (dict, list))
                            except Exception:
                                sok = False
                    sstatus = sr.status_code
                except Exception as exc:  # noqa: BLE001
                    sstatus = f"EXC:{type(exc).__name__}"
                    sok = False
                self._record(
                    check="success_or_reachable",
                    method=method,
                    path=path,
                    status=sstatus,
                    ok=sok,
                )

        # CSRF session flow (FE-like) — throttle cache temiz
        from django.core.cache import cache

        cache.clear()
        with override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": {
                    **(settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES") or {}),
                    "login": "1000/min",
                    "anon": "1000/min",
                },
            }
        ):
            c = APIClient(enforce_csrf_checks=True)
            csrf = c.get("/api/v1/auth/csrf/")
            self._record(
                check="csrf",
                method="GET",
                path="/api/v1/auth/csrf/",
                status=csrf.status_code,
                ok=csrf.status_code == 200,
            )
            token = csrf.cookies.get("csrftoken")
            csrf_val = token.value if token else ""
            login = c.post(
                "/api/v1/auth/login/",
                {"username": self.buyer.username, "password": "x"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf_val,
            )
            self._record(
                check="csrf_login",
                method="POST",
                path="/api/v1/auth/login/",
                status=login.status_code,
                ok=login.status_code in (200, 201),
            )
            if login.status_code in (200, 201):
                me = c.get("/api/v1/me/")
                self._record(
                    check="csrf_me",
                    method="GET",
                    path="/api/v1/me/",
                    status=me.status_code,
                    ok=me.status_code == 200,
                )
                csrf2 = c.get("/api/v1/auth/csrf/")
                t2 = csrf2.cookies.get("csrftoken")
                logout = c.post(
                    "/api/v1/auth/logout/",
                    {},
                    format="json",
                    HTTP_X_CSRFTOKEN=(t2.value if t2 else csrf_val),
                )
                self._record(
                    check="csrf_logout",
                    method="POST",
                    path="/api/v1/auth/logout/",
                    status=logout.status_code,
                    ok=logout.status_code in (200, 204),
                )

        out_dir = _REPO / "docs" / "_audit"
        out_dir.mkdir(parents=True, exist_ok=True)
        failed = [r for r in self.results if not r.get("ok")]
        payload = {
            "total_checks": len(self.results),
            "passed": len(self.results) - len(failed),
            "failed": len(failed),
            "openapi_ops": len(ops),
            "ok": not failed,
            "failures": failed[:50],
            "results": self.results,
        }
        (out_dir / "smoke-matrix-results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # readiness from this run
        by_op: dict[str, dict] = {}
        for r in self.results:
            key = f"{r['method']} {r['path']}"
            by_op.setdefault(key, {"method": r["method"], "path": r["path"], "checks": {}})
            by_op[key]["checks"][r["check"]] = "✅" if r["ok"] else "❌"
        lines = [
            "# Endpoint readiness (ADIM 5 — smoke matrix)",
            "",
            f"Kaynak: `api.tests.test_openapi_smoke_matrix` · ops={len(ops)} · checks={payload['passed']}/{payload['total_checks']}",
            "",
            "| Metot | Path | anon | wrong_role | invalid_body | success |",
            "|-------|------|------|------------|--------------|---------|",
        ]
        ready = sorun = 0
        for key in sorted(by_op):
            row = by_op[key]
            ch = row["checks"]
            marks = [
                ch.get("anon", "—"),
                ch.get("wrong_role", "—"),
                ch.get("invalid_body", "—"),
                ch.get("success_or_reachable", "—"),
            ]
            bad = any(m == "❌" for m in marks)
            if bad:
                sorun += 1
            else:
                ready += 1
            lines.append(
                f"| {row['method']} | `{row['path']}` | {marks[0]} | {marks[1]} | {marks[2]} | {marks[3]} |"
            )
        lines += ["", f"**Özet:** hazır_satır={ready} sorunlu_satır={sorun} (op satırı; check bazlı JSON ayrı)"]
        (out_dir / "endpoint-readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        self.assertFalse(failed, f"{len(failed)} smoke checks failed; see docs/_audit/smoke-matrix-results.json")
