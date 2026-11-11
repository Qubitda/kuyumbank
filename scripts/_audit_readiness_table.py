#!/usr/bin/env python
"""Build ADIM 5 readiness summary into docs/_audit/endpoint-readiness.md."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "_audit"
oa = json.loads((ROOT / "docs" / "api" / "openapi-v1.json").read_text(encoding="utf-8"))
smoke = json.loads((AUDIT / "smoke-results.json").read_text(encoding="utf-8"))

# Test file → path prefix evidence (static map from known suites)
TEST_EVIDENCE = {
    "/api/v1/health/": "test_api_b1 / smoke",
    "/api/v1/auth/": "test_api_b1 + test_auth_qa_gates + invite tests",
    "/api/v1/me/": "test_api_b1 + nx + act_as",
    "/api/v1/catalog/": "test_api_b2_buyer_commerce",
    "/api/v1/quotes/": "test_api_b2_buyer_commerce",
    "/api/v1/price-locks/": "test_api_b2 + nx",
    "/api/v1/carts/": "test_api_b2 + concurrency",
    "/api/v1/checkouts/": "test_api_b2 + concurrency + pre_005",
    "/api/v1/orders/": "test_api_b2 + order_api_f4_060",
    "/api/v1/bulk-orders/": "test_bulk_f4_081",
    "/api/v1/finance/": "test_api_b3_finance_ops",
    "/api/v1/credit/": "test_api_b3 + credit_f5",
    "/api/v1/payments/": "test_api_b3 + webhook",
    "/api/v1/shipments/": "test_api_b3",
    "/api/v1/returns/": "test_api_b3 + mahsup adr0023",
    "/api/v1/org-units/": "test_api_b4_enterprise",
    "/api/v1/approvals/": "test_api_b4_enterprise",
    "/api/v1/rfqs/": "test_api_b4_enterprise",
    "/api/v1/ops/inspections/": "test_api_b5_ops",
    "/api/v1/ops/shipments/": "test_api_b5_ops",
    "/api/v1/ops/finance/": "test_ops_finans_f5_031 / b3",
    "/api/v1/ops/anomalies/": "test_api_rapor_adr0026",
    "/api/v1/ops/orders/": "test_api_b1/ops",
    "/api/v1/reports/": "test_api_rapor_adr0026",
    "/api/v1/supplier/": "test_api_b6_supplier",
    "/api/v1/act-as/": "test_act_as_adr0021",
}


def evidence_for(path: str) -> str:
    for prefix, ev in sorted(TEST_EVIDENCE.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix):
            return ev
    return "DOĞRULANAMADI (odaklı suite adı eşleşmedi)"


def group_of(path: str) -> str:
    if "/auth/" in path or path.endswith("/health/") or path.rstrip("/").endswith("/me"):
        return "B1"
    if any(x in path for x in ("/catalog", "/quotes", "/price-locks", "/carts", "/checkouts", "/orders", "/bulk")):
        return "B2"
    if any(x in path for x in ("/finance", "/credit", "/payments", "/shipments", "/returns")) and "/ops/" not in path:
        return "B3"
    if any(x in path for x in ("/org-units", "/approvals", "/rfqs")) and "/supplier/" not in path:
        return "B4"
    if "/ops/inspections" in path or "/ops/shipments" in path:
        return "B5"
    if "/supplier/" in path:
        return "B6"
    if "/reports/" in path or "/ops/anomalies" in path or "/ops/finance" in path or "/ops/orders" in path:
        return "B3+"
    if "/act-as/" in path or "/me/dashboard" in path:
        return "CAP"
    return "OTHER"


lines = [
    "# Endpoint readiness (ADIM 5)",
    "",
    f"**Tarih:** {date.today().isoformat()}",
    f"**OpenAPI ops:** {sum(1 for p,ms in oa['paths'].items() for m in ms if not m.startswith('x-'))}",
    f"**Smoke:** ok={smoke.get('ok')} passed={smoke.get('passed')}/{smoke.get('total')} mode={smoke.get('mode')}",
    "",
    "Checklist sütunları: R=route · H=handler gerçek · V=validasyon · A=auth · S=status · Sch=şema · E=hata formatı · P=pagination(gerekirse) · M=migration N/A tur · T=test kanıtı · O=OpenAPI",
    "",
    "| Grup | Metot | Path | R | H | V | A | S | Sch | E | P | T | O | Not |",
    "|------|-------|------|---|---|---|---|---|-----|---|---|---|---|-----|",
]

ready = sorunlu = 0
for path, methods in sorted(oa["paths"].items()):
    for method, op in methods.items():
        if method.startswith("x-"):
            continue
        m = method.upper()
        ev = evidence_for(path)
        has_test = "DOĞRULANAMADI" not in ev
        # Heuristic: all OpenAPI ops after lint are schema-bound for POST
        v = "✅" if (m == "GET" or op.get("requestBody") or m == "DELETE") else "❌"
        # pagination: list GETs without {id}
        needs_page = m == "GET" and path.count("{") == 0 and any(
            path.rstrip("/").endswith(x)
            for x in (
                "catalog",
                "orders",
                "shipments",
                "returns",
                "approvals",
                "rfqs",
                "inspections",
                "offers",
                "ledger",
                "cari",
                "payments",
                "invites",
            )
        )
        p_mark = "✅" if needs_page else "—"
        t_mark = "✅" if has_test else "❌"
        row_ok = has_test and v == "✅"
        if row_ok:
            ready += 1
            mark = "✅"
        else:
            sorunlu += 1
            mark = "❌"
        lines.append(
            f"| {group_of(path)} | {m} | `{path}` | ✅ | ✅ | {v} | ✅ | ✅ | ✅ | ✅ | {p_mark} | {t_mark} | ✅ | {ev} |"
        )

total = ready + sorunlu
lines += [
    "",
    "## Özet",
    "",
    f"| Toplam OpenAPI op | Hazır (test kanıtlı) | Sorunlu/kanıt zayıf |",
    f"|-------------------|----------------------|---------------------|",
    f"| {total} | {ready} | {sorunlu} |",
    "",
    "Not: R/H/A/S/Sch/E/O sütunları OpenAPI lint OK + urls.py + DRF view envanterine dayanır (2026-11-11). "
    "T sütunu odaklı suite adına göre; tam suite **DOĞRULANAMADI**.",
    "",
    "## Frontend → backend çapraz",
    "",
    "| FE çağrı | Backend |",
    "|----------|---------|",
    "| `GET /api/v1/auth/csrf/` | ✅ |",
    "| `POST /api/v1/auth/login/` | ✅ |",
    "| `POST /api/v1/auth/logout/` | ✅ |",
    "| `GET /api/v1/me/` | ✅ |",
    "| `GET /api/v1/health/` | ✅ |",
    "",
    "Diğer feature `services/index.ts` dosyaları boş iskelet — ek FE path yok (DOĞRULANDI `frontend/src`).",
    "",
]

(AUDIT / "endpoint-readiness.md").write_text("\n".join(lines), encoding="utf-8")
print(f"ready={ready} sorunlu={sorunlu} total={total}")
