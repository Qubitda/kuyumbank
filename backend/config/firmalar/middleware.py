"""Act-as middleware — ADR-0021 (AuthenticationMiddleware sonrasında).

LoginThrottleMiddleware — Admin login brute-force (IP + kullanıcı adı).
SessionIdleTimeoutMiddleware — boşta kalma zaman aşımı.
"""

from __future__ import annotations

import re
import time

from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.core.cache import cache
from django.http import HttpResponse

from firmalar.services.act_as_servisi import SESSION_ACTOR, SESSION_TARGET
from firmalar.services.audit_servisi import act_as_audit_context, client_ip
from firmalar.services import mfa_servisi

User = get_user_model()

_LOGIN_PATHS = (
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

_SESSION_LAST_ACTIVITY = "_kb_last_activity"


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


def _bump(key: str, period: int) -> int:
    try:
        return int(cache.incr(key))
    except ValueError:
        cache.add(key, 1, timeout=period + 1)
        return 1


class LoginThrottleMiddleware:
    """POST login: TRUSTED_PROXY_COUNT ile IP + kullanıcı adı kovaları."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in _LOGIN_PATHS:
            blocked = self._throttle(request)
            if blocked is not None:
                return blocked
        return self.get_response(request)

    def _throttle(self, request):
        ip_rate = getattr(settings, "LOGIN_THROTTLE_RATE", "10/min")
        user_rate = getattr(
            settings, "LOGIN_THROTTLE_USERNAME_RATE", "20/min"
        )
        ip_limit, ip_period = _parse_login_rate(str(ip_rate))
        user_limit, user_period = _parse_login_rate(str(user_rate))
        ip = client_ip(request) or "unknown"
        bucket_ip = int(time.time()) // ip_period
        ip_key = f"login_throttle:ip:{request.path}:{ip}:{bucket_ip}"
        if _bump(ip_key, ip_period) > ip_limit:
            return HttpResponse(
                "Çok fazla giriş denemesi. Lütfen sonra tekrar deneyin.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )

        username = (request.POST.get("username") or "").strip().lower()
        if username:
            bucket_u = int(time.time()) // user_period
            # Kullanıcı adı kovası path-bağımsız (dağıtık deneme)
            u_key = f"login_throttle:user:{username}:{bucket_u}"
            if _bump(u_key, user_period) > user_limit:
                return HttpResponse(
                    "Bu kullanıcı için çok fazla giriş denemesi.",
                    status=429,
                    content_type="text/plain; charset=utf-8",
                )
        return None


class SessionIdleTimeoutMiddleware:
    """Kimlikli oturumda boşta kalma → logout (SESSION_IDLE_TIMEOUT sn)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session = getattr(request, "session", None)
        user = getattr(request, "user", None)
        idle = int(getattr(settings, "SESSION_IDLE_TIMEOUT", 0) or 0)
        if (
            idle > 0
            and session is not None
            and user is not None
            and getattr(user, "is_authenticated", False)
        ):
            now = int(time.time())
            last = session.get(_SESSION_LAST_ACTIVITY)
            if last is not None and (now - int(last)) > idle:
                logout(request)
                # act-as oturum anahtarlarını da temizle
                session.pop(SESSION_ACTOR, None)
                session.pop(SESSION_TARGET, None)
            else:
                session[_SESSION_LAST_ACTIVITY] = now
                session.modified = True
        return self.get_response(request)


class MfaEnforceMiddleware:
    """Platform kullanıcılarında MFA_ENFORCE_PLATFORM → session mfa_ok zorunlu.

    İzinli yollar: MFA verify/resend, logout, csrf, password reset, health/ready, static/admin login.
    API engeli: application/problem+json (NX-3).
    """

    _ALLOW_PREFIXES = (
        "/api/v1/auth/mfa/",
        "/api/v1/auth/logout/",
        "/api/v1/auth/csrf/",
        "/api/v1/auth/password-reset/",
        "/api/v1/auth/invites/accept/",
        "/api/v1/auth/email-verify/",
        "/api/v1/health/",
        "/api/v1/ready/",
        "/admin/login/",
        "/static/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            mfa_servisi.mfa_enforce_enabled()
            and user is not None
            and getattr(user, "is_authenticated", False)
            and mfa_servisi.user_requires_mfa(user)
            and not mfa_servisi.session_mfa_ok(request.session)
        ):
            path = request.path or ""
            if not any(path.startswith(p) for p in self._ALLOW_PREFIXES):
                from api.problem import problem_response

                return problem_response(
                    status=403,
                    detail="MFA doğrulaması gerekli.",
                    code="mfa_required",
                    title="MfaRequired",
                    request_id=getattr(request, "request_id", None),
                )
        return self.get_response(request)


class BasicAuthThrottleMiddleware:
    """Authorization: Basic isteklerini sıkı IP limiti (prod Basic açıksa)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION") or ""
        if auth.lower().startswith("basic "):
            rate = getattr(settings, "DRF_THROTTLE_BASIC", "5/min")
            limit, period = _parse_login_rate(str(rate))
            ip = client_ip(request) or "unknown"
            bucket = int(time.time()) // period
            key = f"basic_auth_throttle:{ip}:{bucket}"
            if _bump(key, period) > limit:
                return HttpResponse(
                    "Too many Basic authentication attempts.",
                    status=429,
                    content_type="text/plain; charset=utf-8",
                )
        return self.get_response(request)
