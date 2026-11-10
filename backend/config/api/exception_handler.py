"""ADR-0017 / API-B1 — tek problem+json hata zarfı."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    Throttled,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ProblemJSONRenderer(JSONRenderer):
    """NX-3 — RFC 7807 media type (JSON gövde)."""

    media_type = "application/problem+json"

_STATUS_CODE = {
    400: "bad_request",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "unprocessable_entity",
    429: "throttled",
    500: "server_error",
}


def _as_message_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            out.extend(_as_message_list(item))
        return out
    if isinstance(value, dict):
        # Nested — flatten messages only
        out = []
        for v in value.values():
            out.extend(_as_message_list(v))
        return out
    return [str(value)]


def _field_errors(detail: dict) -> dict[str, list[dict[str, str]]]:
    errors: dict[str, list[dict[str, str]]] = {}
    for field, raw in detail.items():
        if field == "detail":
            continue
        msgs = _as_message_list(raw)
        if not msgs:
            continue
        code = "invalid"
        if isinstance(raw, list) and raw and hasattr(raw[0], "code"):
            code = getattr(raw[0], "code", None) or "invalid"
        errors[str(field)] = [{"code": str(code), "message": m} for m in msgs]
    return errors


def _resolve_code(exc: BaseException, status_code: int, errors: dict | None) -> str:
    if isinstance(exc, APIException):
        get_codes = getattr(exc, "get_codes", None)
        if callable(get_codes):
            codes = get_codes()
            if isinstance(codes, str) and codes:
                return codes
            if isinstance(codes, dict) and "detail" in codes and isinstance(
                codes["detail"], str
            ):
                return codes["detail"]
        default = getattr(exc, "default_code", None)
        if isinstance(default, str) and default:
            return default
    if errors:
        return "validation_error"
    return _STATUS_CODE.get(status_code, "error")


def _detail_text(detail: Any, errors: dict | None) -> str:
    if isinstance(detail, dict):
        if "detail" in detail:
            msgs = _as_message_list(detail["detail"])
            if msgs:
                return msgs[0]
        if errors:
            # İlk alanın ilk mesajı
            for items in errors.values():
                if items:
                    return items[0]["message"]
        return "İstek geçersiz."
    msgs = _as_message_list(detail)
    return msgs[0] if msgs else "İstek işlenemedi."


def problem_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    # DRF: authenticate_header yoksa 401→403 zorlar; NX-1 ayrımı koru
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED

    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request is not None else None

    raw = response.data
    errors = None
    if isinstance(raw, dict) and any(k != "detail" for k in raw.keys()):
        # Alan bazlı ValidationError
        maybe = _field_errors(raw)
        if maybe:
            errors = maybe

    detail_val = _detail_text(raw, errors)
    title = type(exc).__name__
    code = _resolve_code(exc, response.status_code, errors)
    type_uri = f"https://kuyumbank.local/problems/{code}"

    body: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": response.status_code,
        "detail": detail_val,
        "code": code,
        "request_id": request_id,
    }
    if errors:
        body["errors"] = errors

    response.data = body
    # NX-3 — APIView.finalize_response request.accepted_renderer'ı response'a kopyalar
    renderer = ProblemJSONRenderer()
    if request is not None:
        request.accepted_renderer = renderer
        request.accepted_media_type = ProblemJSONRenderer.media_type
    response.accepted_renderer = renderer
    response.accepted_media_type = ProblemJSONRenderer.media_type

    if isinstance(exc, Throttled) or response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        wait = getattr(exc, "wait", None)
        if wait is not None:
            response["Retry-After"] = str(max(1, int(wait)))

    return response
