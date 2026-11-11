"""ADR-0017 NX-1 — session login/logout/csrf + şifre/MFA."""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError as DjangoValidationError
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
from firmalar.services import auth_gate_servisi, mfa_servisi, sifre_servisi


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


def _django_ve_to_drf(exc: DjangoValidationError) -> ValidationError:
    if hasattr(exc, "message_dict"):
        return ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        return ValidationError(list(exc.messages))
    return ValidationError(str(exc))


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
        if user is None:
            raise AuthenticationFailed(detail="Kimlik doğrulanamadı.")
        try:
            auth_gate_servisi.assert_user_may_login(user)
        except DjangoValidationError as exc:
            # Enumeration azalt: genel mesaj; detay PermissionDenied
            raise PermissionDenied(detail=str(exc)) from exc

        login(request, user)
        mfa_servisi.clear_mfa(request.session)
        body = present_me(user)
        if mfa_servisi.user_requires_mfa(user):
            try:
                mfa_servisi.issue_email_otp(user=user)
            except DjangoValidationError as exc:
                logout(request)
                raise _django_ve_to_drf(exc) from exc
            body = {**body, "mfa_required": True, "mfa_ok": False}
            response = Response(body, status=status.HTTP_200_OK)
        else:
            mfa_servisi.mark_mfa_ok(request.session)
            body = {**body, "mfa_required": False, "mfa_ok": True}
            response = Response(body, status=status.HTTP_200_OK)
        response["Cache-Control"] = "no-store"
        return response


class AuthLogoutView(APIView):
    """POST /api/v1/auth/logout/ — oturumu kapat."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        enforce_csrf(request)
        mfa_servisi.clear_mfa(request.session)
        logout(request)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """POST {email} — her zaman genel başarı mesajı."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        try:
            msg = sifre_servisi.request_password_reset(
                email=request.data.get("email") or "",
                request=request,
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response({"detail": msg})


class PasswordResetConfirmView(APIView):
    """POST {uid, token, new_password, new_password_confirm}."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        try:
            sifre_servisi.confirm_password_reset(
                uidb64=request.data.get("uid") or "",
                token=request.data.get("token") or "",
                new_password=request.data.get("new_password") or "",
                new_password_confirm=request.data.get("new_password_confirm")
                or "",
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response({"detail": "Şifre güncellendi. Giriş yapın."})


class PasswordChangeView(APIView):
    """POST {current_password, new_password, new_password_confirm}."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        enforce_csrf(request)
        try:
            user = sifre_servisi.change_password(
                actor=request.user,
                current_password=request.data.get("current_password") or "",
                new_password=request.data.get("new_password") or "",
                new_password_confirm=request.data.get("new_password_confirm")
                or "",
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        update_session_auth_hash(request, user)
        return Response({"detail": "Şifre değiştirildi."})


class MfaVerifyView(APIView):
    """POST {code} — e-posta OTP; MFA_ENFORCE_PLATFORM iken zorunlu."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        if not mfa_servisi.user_requires_mfa(request.user):
            mfa_servisi.mark_mfa_ok(request.session)
            return Response({"mfa_ok": True, "detail": "MFA gerekli değil."})
        try:
            mfa_servisi.verify_email_otp(
                user=request.user,
                code=request.data.get("code") or "",
                session=request.session,
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response({"mfa_ok": True, **present_me(request.user)})


class MfaResendView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        if not mfa_servisi.user_requires_mfa(request.user):
            return Response({"detail": "MFA gerekli değil."})
        try:
            mfa_servisi.issue_email_otp(user=request.user)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response({"detail": "Kod yeniden gönderildi."})
