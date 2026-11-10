"""F8-003 — Sentry SDK bağlama (DSN yoksa no-op)."""

from __future__ import annotations

from typing import Any

from config.logging_utils import redact_mapping, scrub_message


def sentry_before_send(event: dict[str, Any], hint: dict[str, Any] | None = None):
    """PII/secret scrub — logging_utils ile aynı anahtar seti."""
    del hint  # unused; SDK imzası
    if "request" in event and isinstance(event["request"], dict):
        req = event["request"]
        if isinstance(req.get("headers"), dict):
            req["headers"] = redact_mapping(req["headers"])
        if isinstance(req.get("data"), dict):
            req["data"] = redact_mapping(req["data"])
        if isinstance(req.get("cookies"), dict):
            req["cookies"] = redact_mapping(req["cookies"])
        if isinstance(req.get("query_string"), str):
            req["query_string"] = scrub_message(req["query_string"])
    if "extra" in event and isinstance(event["extra"], dict):
        event["extra"] = redact_mapping(event["extra"])
    if "message" in event and isinstance(event["message"], str):
        event["message"] = scrub_message(event["message"])
    return event


def init_sentry(*, dsn: str, environment: str = "development", traces_sample_rate: float = 0.0) -> bool:
    """DSN boşsa False (SDK yüklenmez). Başarılı init → True."""
    dsn = (dsn or "").strip()
    if not dsn:
        return False
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        environment=environment or "development",
        traces_sample_rate=max(0.0, min(float(traces_sample_rate), 1.0)),
        send_default_pii=False,
        before_send=sentry_before_send,
    )
    return True
