"""Şablon render — yalnız allowlist değişkenler (`{{var}}`)."""

from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError

from bildirim.models import EmailTemplate

# Kör havuz: tedarikçi kimliği / maliyet anahtarları yasak.
_FORBIDDEN = frozenset(
    {
        "tedarikci",
        "tedarikci_id",
        "tedarikci_adi",
        "supplier",
        "supplier_id",
        "maliyet",
        "cost",
        "margin",
        "marj",
        "hak_edis",
    }
)

ALLOWED_KEYS = frozenset(
    {
        "order_id",
        "firma_adi",
        "firma_kodu",
        "user_email",
        "user_name",
        "amount",
        "currency",
        "shipment_id",
        "takip_no",
        "inspection_id",
        "return_id",
        "event_type",
        "reason",
        "line_count",
        "document_notes",
        "platform_name",
    }
)

_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def _normalize_context(context: dict[str, Any] | None) -> dict[str, str]:
    raw = dict(context or {})
    out: dict[str, str] = {}
    for key, val in raw.items():
        k = str(key)
        if k.lower() in _FORBIDDEN or k in _FORBIDDEN:
            raise ValidationError(f"Yasak context anahtarı: {k}")
        if k not in ALLOWED_KEYS:
            raise ValidationError(f"Allowlist dışı context: {k}")
        out[k] = "" if val is None else str(val)
    return out


def _replace_mustache(text: str, ctx: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in ALLOWED_KEYS:
            raise ValidationError(f"Şablonda allowlist dışı değişken: {key}")
        return ctx.get(key, "")

    return _VAR_RE.sub(repl, text or "")


def render(*, subject: str, body: str, context: dict[str, Any] | None = None) -> tuple[str, str]:
    ctx = _normalize_context(context)
    return _replace_mustache(subject or "", ctx), _replace_mustache(body or "", ctx)


def render_template(
    template: EmailTemplate, context: dict[str, Any] | None = None
) -> tuple[str, str]:
    if not template.aktif:
        raise ValidationError("Şablon pasif.")
    return render(subject=template.subject, body=template.html_body, context=context)
