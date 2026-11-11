"""RFC 7807 problem+json helpers — DRF dışı middleware yanıtları için."""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpResponse


def problem_response(
    *,
    status: int,
    detail: str,
    code: str,
    title: str | None = None,
    request_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> HttpResponse:
    """Middleware / non-DRF yollar için tek problem+json zarfı (NX-3)."""
    body: dict[str, Any] = {
        "type": f"https://kuyumbank.local/problems/{code}",
        "title": title or code,
        "status": status,
        "detail": detail,
        "code": code,
        "request_id": request_id,
    }
    resp = HttpResponse(
        json.dumps(body, ensure_ascii=False),
        status=status,
        content_type="application/problem+json; charset=utf-8",
    )
    if extra_headers:
        for k, v in extra_headers.items():
            resp[k] = v
    return resp
