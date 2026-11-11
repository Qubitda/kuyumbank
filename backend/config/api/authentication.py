"""Session auth + süresi dolan Token; CSRF yalnız kimlikli oturumda."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import (
    SessionAuthentication as DRFSessionAuthentication,
    TokenAuthentication as DRFTokenAuthentication,
)
from rest_framework.exceptions import AuthenticationFailed


class SessionAuthentication(DRFSessionAuthentication):
    """Anonim kullanıcıda CSRF/auth deneme yok — NotAuthenticated (401).

    DRF, ilk authenticator `authenticate_header` döndürmezse 401'i 403'e zorlar.
    Session birincil olduğu için buradan sabit bir challenge döneriz (NX-1: 401/403 ayrımı).
    """

    def authenticate(self, request):
        django_user = getattr(request._request, "user", None)
        if django_user is None or not getattr(django_user, "is_authenticated", False):
            return None
        return super().authenticate(request)

    def authenticate_header(self, request):
        return "Session"


class ExpiringTokenAuthentication(DRFTokenAuthentication):
    """authtoken + AUTH_TOKEN_TTL_SECONDS (0 = süresiz; prod'da >0 önerilir)."""

    def authenticate_credentials(self, key):
        user_auth = super().authenticate_credentials(key)
        user, token = user_auth
        ttl = int(getattr(settings, "AUTH_TOKEN_TTL_SECONDS", 0) or 0)
        if ttl > 0:
            created = getattr(token, "created", None)
            if created is None or created < timezone.now() - timedelta(seconds=ttl):
                raise AuthenticationFailed("Token süresi dolmuş; yenileyin.")
        return user, token


def enforce_csrf(request) -> None:
    """DRF APIView csrf_exempt olduğu için yazma uçlarında açık CSRF kontrolü."""
    SessionAuthentication().enforce_csrf(request)
