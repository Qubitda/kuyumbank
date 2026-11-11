"""Davet + e-posta doğrulama API — ADR-0028."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from api.authentication import enforce_csrf
from api.permissions import IsAuthenticatedWithFirma
from api.views.auth import LoginRateThrottle, _django_ve_to_drf
from firmalar.models import Firma, FirmaInvite
from firmalar.role_permissions import P
from firmalar.services import email_verify_servisi, invite_servisi
from firmalar.services.yetki_servisi import can_manage_all_users, has_perm


class InviteCreateView(APIView):
    """POST {email, rol, firma_id?} — manage_users."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        firma = None
        raw_fid = request.data.get("firma_id")
        if raw_fid is not None and str(raw_fid).strip() != "":
            if not can_manage_all_users(request.user):
                raise PermissionDenied("firma_id yalnız platform.")
            try:
                firma = Firma.objects.get(pk=int(raw_fid))
            except (TypeError, ValueError, Firma.DoesNotExist) as exc:
                raise ValidationError({"firma_id": "Geçersiz firma."}) from exc
        try:
            inv = invite_servisi.create_invite(
                actor=request.user,
                email=request.data.get("email") or "",
                rol=request.data.get("rol") or "",
                firma=firma,
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(
            {
                "id": inv.pk,
                "email": inv.email,
                "rol": inv.rol,
                "firma_id": inv.firma_id,
                "expires_at": inv.expires_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class InviteListView(APIView):
    """GET — kendi firma bekleyen davetler (platform: ?firma_id=)."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        if not (
            can_manage_all_users(request.user)
            or has_perm(request.user, P["manage_users"])
        ):
            raise PermissionDenied("Davet listesi için manage_users gerekir.")
        qs = FirmaInvite.objects.filter(kabul_edildi_at__isnull=True).select_related(
            "firma"
        )
        if can_manage_all_users(request.user):
            fid = request.query_params.get("firma_id")
            if fid:
                qs = qs.filter(firma_id=fid)
        else:
            qs = qs.filter(firma_id=request.user.firma_id)
        rows = [
            {
                "id": i.pk,
                "email": i.email,
                "rol": i.rol,
                "firma_id": i.firma_id,
                "expires_at": i.expires_at.isoformat(),
                "expired": i.is_expired,
            }
            for i in qs.order_by("-pk")[:100]
        ]
        return Response({"results": rows})


class InviteAcceptView(APIView):
    """POST {token, username, password, password_confirm}."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        try:
            user = invite_servisi.accept_invite(
                token=request.data.get("token") or "",
                username=request.data.get("username") or "",
                password=request.data.get("password") or "",
                password_confirm=request.data.get("password_confirm") or "",
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response(
            {"detail": "Davet kabul edildi.", "username": user.get_username()},
            status=status.HTTP_201_CREATED,
        )


class EmailVerifyRequestView(APIView):
    """POST {email?} — girişliyse kendi hesabı; anonim email."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        try:
            if getattr(request.user, "is_authenticated", False):
                msg = email_verify_servisi.request_verification(user=request.user)
            else:
                msg = email_verify_servisi.request_verification(
                    email=request.data.get("email") or ""
                )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response({"detail": msg})


class EmailVerifyConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        enforce_csrf(request)
        try:
            user = email_verify_servisi.confirm_verification(
                uidb64=request.data.get("uid") or "",
                token=request.data.get("token") or "",
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        return Response(
            {
                "detail": "E-posta doğrulandı.",
                "username": user.get_username(),
                "email_verified": True,
            }
        )
