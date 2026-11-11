"""F5-021 webhook — HMAC imza + zaman damgası / replay + isteğe bağlı IP allow-list."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import time

from django.conf import settings
from django.core.exceptions import ValidationError

from firmalar.services.audit_servisi import client_ip


def _secret() -> str:
    return (getattr(settings, "PAYMENT_WEBHOOK_SECRET", "") or "").strip()


def sign_body(*, secret: str, timestamp: str, body: bytes) -> str:
    """HMAC-SHA256(timestamp + '.' + body) → hex."""
    msg = timestamp.encode("utf-8") + b"." + (body or b"")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_webhook_http(request) -> None:
    """İstek doğrula; başarısızda ValidationError (çağıran 401/400 map eder)."""
    secret = _secret()
    if not secret:
        raise ValidationError("Webhook secret yapılandırılmamış.")

    allow = getattr(settings, "PAYMENT_WEBHOOK_IP_ALLOWLIST", None) or []
    if allow:
        ip = client_ip(request) or ""
        ok = False
        for entry in allow:
            entry = (entry or "").strip()
            if not entry:
                continue
            try:
                net = ipaddress.ip_network(entry, strict=False)
                if ipaddress.ip_address(ip) in net:
                    ok = True
                    break
            except ValueError:
                if ip == entry:
                    ok = True
                    break
        if not ok:
            raise ValidationError("Webhook IP allow-list dışı.")

    body = getattr(request, "body", b"") or b""
    ts = (request.headers.get("X-Webhook-Timestamp") or "").strip()
    sig = (request.headers.get("X-Webhook-Signature") or "").strip()
    require_hmac = bool(
        getattr(settings, "PAYMENT_WEBHOOK_REQUIRE_HMAC", True)
    )

    if require_hmac or (ts and sig):
        if not ts or not sig:
            raise ValidationError(
                "X-Webhook-Timestamp ve X-Webhook-Signature zorunlu."
            )
        try:
            ts_i = int(ts)
        except ValueError as exc:
            raise ValidationError("Geçersiz zaman damgası.") from exc
        window = int(
            getattr(settings, "PAYMENT_WEBHOOK_REPLAY_SECONDS", 300) or 300
        )
        now = int(time.time())
        if abs(now - ts_i) > window:
            raise ValidationError("Webhook zaman damgası pencere dışı (replay).")
        expected = sign_body(secret=secret, timestamp=ts, body=body)
        got = sig.removeprefix("sha256=").strip()
        if not hmac.compare_digest(got, expected):
            raise ValidationError("Webhook imzası geçersiz.")
        return

    # Legacy: düz secret header (yalnız REQUIRE_HMAC=False)
    legacy = (
        request.headers.get("X-Payment-Webhook-Secret") or ""
    ).strip()
    if not hmac.compare_digest(legacy, secret):
        raise ValidationError("Webhook secret geçersiz.")
