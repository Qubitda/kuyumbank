"""Act-as middleware — ADR-0021 (AuthenticationMiddleware sonrasında).

LoginThrottleMiddleware — HTML login yüzeylerinde brute-force limiti (cache).
"""

from __future__ import annotations

import re
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse

from firmalar.services.act_as_servisi import SESSION_ACTOR, SESSION_TARGET
from firmalar.services.audit_servisi import act_as_audit_context

User = get_user_model()

_LOGIN_PATHS = (
    "/buyer/login/",
    "/supplier/login/",
    "/admin/login/",
)

_RATE_RE = re.compile(r"^(\d+)\s*/\s*(second|sec|minute|min|hour|hr|day)s?$", re.I)
_PERIOD_SECONDS = {
    "second": 1,
    "sec": 1,
    "minute": 60,
    "min": 60,
    "hour": 3600,
    "hr": 3600,
    "day": 86400,
}


class ActAsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.act_as_active = False
        request.act_as_actor = None
        session = getattr(request, "session", None)
        user = getattr(request, "user", None)
        if session is not None and user is not None and getattr(user, "is_authenticated", False):
            actor_id = session.get(SESSION_ACTOR)
            target_id = session.get(SESSION_TARGET)
            if actor_id and target_id and int(actor_id) == int(user.pk):
                target = (
                    User.objects.select_related("firma")
                    .filter(pk=target_id, is_active=True)
                    .first()
                )
                if target is not None:
                    request.act_as_actor = user
                    request.user = target
                    request.act_as_active = True
                    with act_as_audit_context(actor=user, target=target):
                        return self.get_response(request)
                session.pop(SESSION_ACTOR, None)
                session.pop(SESSION_TARGET, None)
                session.modified = True
        return self.get_response(request)


def _parse_login_rate(rate: str) -> tuple[int, int]:
    """'10/min' → (num_requests, period_seconds)."""
    raw = (rate or "10/min").strip()
    m = _RATE_RE.match(raw)
    if not m:
        return 10, 60
    num = int(m.group(1))
    period = _PERIOD_SECONDS[m.group(2).lower()]
    return max(1, num), period


def _client_ip(request) -> str:
    meta = getattr(request, "META", None) or {}
    return (meta.get("REMOTE_ADDR") or "").strip() or "unknown"


class LoginThrottleMiddleware:
    """POST /buyer|/supplier|/admin/login için IP başına rate limit."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in _LOGIN_PATHS:
            blocked = self._throttle(request)
            if blocked is not None:
                return blocked
        return self.get_response(request)

    def _throttle(self, request):
        rate = getattr(settings, "LOGIN_THROTTLE_RATE", "10/min")
        limit, period = _parse_login_rate(str(rate))
        ip = _client_ip(request)
        bucket = int(time.time()) // period
        key = f"login_throttle:{request.path}:{ip}:{bucket}"
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=period + 1)
            count = 1
        if count > limit:
            return HttpResponse(
                "Çok fazla giriş denemesi. Lütfen sonra tekrar deneyin.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        return None
