"""F8-002 — request_id context + secret-aware log yardımcıları."""

from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Log extra / message içinde asla tutulmaması gereken anahtarlar
_SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "db_password",
        "payment_webhook_secret",
        "csrfmiddlewaretoken",
    }
)

_REDACT = "***"


def get_request_id() -> str:
    return request_id_var.get()


def redact_mapping(data: dict[str, Any] | None) -> dict[str, Any]:
    """Dict anahtarlarında secret benzeri alanları maskeler (shallow + 1 seviye)."""
    if not data:
        return {}
    out: dict[str, Any] = {}
    for key, value in data.items():
        lk = str(key).lower()
        if lk in _SECRET_KEYS or any(s in lk for s in ("password", "secret", "token")):
            out[key] = _REDACT
        elif isinstance(value, dict):
            out[key] = redact_mapping(value)
        else:
            out[key] = value
    return out


def scrub_message(msg: str) -> str:
    """Ham mesajda Bearer/token kalıntısını maskele (best-effort)."""
    if not msg:
        return msg
    msg = re.sub(
        r"(?i)(authorization\s*[:=]\s*)(Bearer\s+)?\S+",
        rf"\1\2{_REDACT}",
        msg,
    )
    msg = re.sub(
        r"(?i)(?<!authorization: )(Bearer\s+)\S+",
        rf"\1{_REDACT}",
        msg,
    )
    return msg


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class StructuredFormatter(logging.Formatter):
    """Tek satır JSON (stdlib). Secret anahtarları extra'dan düşürür."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", get_request_id()),
            "msg": scrub_message(record.getMessage()),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # bilinen safe alanlar
        for key in ("path", "method", "status_code", "user_id", "firma_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        # record.__dict__ içindeki şüpheli anahtarları asla dump etme
        extra_suspect = {
            k: v
            for k, v in record.__dict__.items()
            if k.lower() in _SECRET_KEYS
            or any(s in k.lower() for s in ("password", "secret", "token"))
        }
        if extra_suspect:
            payload["redacted_keys"] = sorted(extra_suspect.keys())
        return json.dumps(payload, ensure_ascii=False, default=str)
