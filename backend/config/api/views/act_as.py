"""Act-as JSON API — ADR-0021 çekirdek + ADR-0029 API-only."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.authentication import enforce_csrf
from api.permissions import IsAuthenticatedWithFirma
from api.views.auth import _django_ve_to_drf
from firmalar.services import act_as_servisi

User = get_user_model()


class ActAsStartView(APIView):
    """POST {user_id} — session act-as başlat."""

    permission_classes = [IsAuthenticatedWithFirma]

    def post(self, request):
        enforce_csrf(request)
        actor = getattr(request, "act_as_actor", None) or request.user
        if getattr(request, "act_as_active", False):
            raise ValidationError("Önce mevcut act-as oturumunu sonlandırın.")
        raw = request.data.get("user_id")
        try:
            user_id = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"user_id": "Geçersiz kullanıcı."}) from exc
        target = get_object_or_404(User.objects.select_related("firma"), pk=user_id)
        try:
            act_as_servisi.baslat(
                actor=actor, target=target, session=request.session
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(
            {
                "act_as": True,
                "target_id": target.pk,
                "target_username": target.get_username(),
                "redirect_url": act_as_servisi.portal_hedef_url(target),
            }
        )


class ActAsStopView(APIView):
    """POST — act-as bitir."""

    permission_classes = [IsAuthenticatedWithFirma]

    def post(self, request):
        enforce_csrf(request)
        actor = act_as_servisi.durdur(
            session=request.session,
            actor_fallback=getattr(request, "act_as_actor", None),
        )
        return Response(
            {
                "act_as": False,
                "actor_id": getattr(actor, "pk", None),
                "redirect_url": "/admin/" if actor is not None and actor.is_staff else "/",
            }
        )
