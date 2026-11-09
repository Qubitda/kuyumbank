"""ADR-0017 NX-1 — session login/logout/csrf (tarayıcıda token yok)."""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from api.authentication import enforce_csrf
from api.services.capabilities_servisi import present_me


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AuthCsrfView(APIView):
    """GET /api/v1/auth/csrf/ — CSRF çerezi + token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrf_token": get_token(request)})


class AuthLoginView(APIView):
    """POST /api/v1/auth/login/ — {username, password}; session cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        field_errors = {}
        if not username:
            field_errors["username"] = ["Zorunlu."]
        if not password:
            field_errors["password"] = ["Zorunlu."]
        if field_errors:
            raise ValidationError(field_errors)

        user = authenticate(request, username=username, password=password)
        if user is None or not getattr(user, "is_active", False):
            raise AuthenticationFailed(detail="Kimlik doğrulanamadı.")
        if not getattr(user, "firma_id", None):
            raise PermissionDenied(detail="Firma bağlamı gerekli.")

        login(request, user)
        response = Response(present_me(user), status=status.HTTP_200_OK)
        response["Cache-Control"] = "no-store"
        return response


class AuthLogoutView(APIView):
    """POST /api/v1/auth/logout/ — oturumu kapat."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        enforce_csrf(request)
        logout(request)
        return Response({"ok": True}, status=status.HTTP_200_OK)
