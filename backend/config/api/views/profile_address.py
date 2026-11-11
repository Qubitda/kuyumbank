"""F9-017 — /me/profile + /me/addresses self-service (ADR-0029 JSON)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.services.capabilities_servisi import present_firma_masked
from api.throttles import BuyerRateThrottle
from firmalar.models import FirmaAdresi
from firmalar.role_permissions import P
from firmalar.selectors.adres import get_adres_for_actor, scope_adres_queryset
from firmalar.services import adres_servisi
from firmalar.services.email_verify_servisi import is_email_verified
from firmalar.services.yetki_servisi import can_manage_all_users, has_perm


def _can_manage_addresses(user) -> bool:
    return can_manage_all_users(user) or has_perm(user, P["manage_users"])


def present_profile(user) -> dict:
    return {
        "id": user.pk,
        "username": user.get_username(),
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "rol": getattr(user, "rol", "") or "",
        "email_verified": is_email_verified(user),
        "firma": present_firma_masked(getattr(user, "firma", None)),
        "allowed_actions": ["update"],
        "server_now": timezone.now().isoformat(),
    }


def present_address(row: FirmaAdresi, *, can_manage: bool = False) -> dict:
    actions = ["view"]
    if can_manage:
        actions.extend(["update", "delete"])
    return {
        "id": row.pk,
        "tip": row.tip,
        "il": row.il,
        "ilce": row.ilce or "",
        "adres": row.adres,
        "varsayilan": bool(row.varsayilan),
        "firma_id": row.firma_id,
        "allowed_actions": actions,
        "server_now": timezone.now().isoformat(),
    }


class MeProfileView(APIView):
    """GET/PATCH /api/v1/me/profile/ — kendi profil (first_name/last_name)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        return Response(present_profile(request.user))

    def patch(self, request):
        data = request.data or {}
        # Yalnız bilinen alanlar; email/rol/firma client'tan yok sayılır
        try:
            user = adres_servisi.guncelle_profil(
                actor=request.user,
                first_name=data["first_name"] if "first_name" in data else None,
                last_name=data["last_name"] if "last_name" in data else None,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return Response(present_profile(user))


class MeAddressListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur — {tip, il, ilce?, adres, varsayilan?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        # Client firma_id yok sayılır
        request.query_params.get("firma_id")
        qs = scope_adres_queryset(FirmaAdresi.objects.all(), request.user)
        tip = (request.query_params.get("tip") or "").strip().lower()
        if tip:
            qs = qs.filter(tip=tip)
        qs = apply_ordering(
            qs, request, whitelist=("tip", "il", "pk", "varsayilan"), default="tip"
        )
        can_m = _can_manage_addresses(request.user)
        return paginate_queryset(
            request, qs, present=lambda a: present_address(a, can_manage=can_m)
        )

    def post(self, request):
        if not _can_manage_addresses(request.user):
            raise PermissionDenied(detail="Adres oluşturmak için manage_users gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        data = request.data or {}
        try:
            row = adres_servisi.olustur(
                actor=request.user,
                tip=data.get("tip"),
                il=data.get("il") or "",
                ilce=data.get("ilce") or "",
                adres=data.get("adres") or "",
                varsayilan=bool(data.get("varsayilan", False)),
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(
                present_address(row, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class MeAddressDetailView(IdempotencyMixin, APIView):
    """GET/PATCH/DELETE /api/v1/me/addresses/<id>/ — scope dışı → 404."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def _get(self, request, pk: int) -> FirmaAdresi:
        try:
            return get_adres_for_actor(request.user, pk)
        except ObjectDoesNotExist as exc:
            raise NotFound(detail="Adres bulunamadı.") from exc

    def get(self, request, pk: int):
        row = self._get(request, pk)
        return Response(
            present_address(row, can_manage=_can_manage_addresses(request.user))
        )

    def patch(self, request, pk: int):
        if not _can_manage_addresses(request.user):
            raise PermissionDenied(detail="Adres güncellemek için manage_users gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        row = self._get(request, pk)
        data = request.data or {}
        kwargs = {}
        for key in ("tip", "il", "ilce", "adres"):
            if key in data:
                kwargs[key] = data.get(key)
        if "varsayilan" in data:
            kwargs["varsayilan"] = bool(data.get("varsayilan"))
        try:
            row = adres_servisi.guncelle(actor=request.user, row=row, **kwargs)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(present_address(row, can_manage=True)),
        )

    def delete(self, request, pk: int):
        if not _can_manage_addresses(request.user):
            raise PermissionDenied(detail="Adres silmek için manage_users gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        row = self._get(request, pk)
        try:
            adres_servisi.sil(actor=request.user, row=row)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response({"detail": "ok"}, status=status.HTTP_200_OK),
        )
