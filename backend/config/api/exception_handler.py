"""F7-014 — tutarlı problem+json benzeri hata gövdesi."""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def problem_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    title = "Error"
    if isinstance(detail, dict):
        if "detail" in detail and len(detail) == 1:
            detail_val = detail["detail"]
        else:
            detail_val = detail
        title = type(exc).__name__
    else:
        detail_val = detail
        title = type(exc).__name__

    type_uri = f"https://kuyumbank.local/problems/{title.lower()}"
    body = {
        "type": type_uri,
        "title": title,
        "status": response.status_code,
        "detail": detail_val,
    }
    response.data = body
    return response
