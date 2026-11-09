"""B4 — OrgBirimi / OrgUyeligi HTTP (org_servisi)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.enterprise import present_org, present_org_member
from api.throttles import BuyerRateThrottle
from firmalar.models import OrgBirimi, OrgUyeligi
from firmalar.role_permissions import P
from firmalar.selectors.org import get_org_for_actor, scope_org_queryset
from firmalar.services import org_servisi
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm

User = get_user_model()


def _can_manage_org(user) -> bool:
    return has_perm(user, P["manage_org"])


def _actor_firma(user):
    firma = getattr(user, "firma", None)
    if firma is None:
        raise PermissionDenied(detail="Firma yok.")
    return firma


class OrgUnitListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur — {kod, ad, parent_id?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        # Client firma_id yok sayılır — selector tenant scope.
        request.query_params.get("firma_id")
        qs = scope_org_queryset(OrgBirimi.objects.all(), request.user)
        qs = apply_ordering(
            qs, request, whitelist=("kod", "pk"), default="kod"
        )
        can_m = _can_manage_org(request.user)
        return paginate_queryset(
            request, qs, present=lambda o: present_org(o, can_manage=can_m)
        )

    def post(self, request):
        if not _can_manage_org(request.user) and not can_view_all_tenants(
            request.user
        ):
            raise PermissionDenied(detail="Org yönetimi için manage_org gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        firma = _actor_firma(request.user)
        kod = request.data.get("kod")
        ad = request.data.get("ad") or ""
        parent = None
        raw_parent = request.data.get("parent_id")
        if raw_parent is not None and raw_parent != "":
            try:
                parent = get_org_for_actor(request.user, int(raw_parent))
            except (ObjectDoesNotExist, TypeError, ValueError) as exc:
                raise NotFound(detail="Parent org bulunamadı.") from exc
        try:
            ob = org_servisi.olustur_birim(
                actor=request.user,
                firma=firma,
                kod=kod,
                ad=ad,
                parent=parent,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(
                present_org(ob, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class OrgUnitDetailView(APIView):
    """GET /api/v1/org-units/<pk>/ — scope dışı → 404."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        try:
            ob = get_org_for_actor(request.user, pk)
        except ObjectDoesNotExist as exc:
            raise NotFound(detail="Org birimi bulunamadı.") from exc
        return Response(
            present_org(ob, can_manage=_can_manage_org(request.user))
        )


class OrgMemberListCreateView(IdempotencyMixin, APIView):
    """GET üyeler; POST üye ekle — {kullanici_id}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def _org(self, request, pk: int) -> OrgBirimi:
        try:
            return get_org_for_actor(request.user, pk)
        except ObjectDoesNotExist as exc:
            raise NotFound(detail="Org birimi bulunamadı.") from exc

    def get(self, request, pk: int):
        ob = self._org(request, pk)
        qs = OrgUyeligi.objects.filter(org_birimi=ob).order_by("pk")
        return paginate_queryset(request, qs, present=present_org_member)

    def post(self, request, pk: int):
        if not _can_manage_org(request.user) and not can_view_all_tenants(
            request.user
        ):
            raise PermissionDenied(detail="Org yönetimi için manage_org gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        ob = self._org(request, pk)
        try:
            uid = int(request.data.get("kullanici_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"kullanici_id": "Geçersiz."}) from exc
        # Çapraz firma kullanıcı → varlık sızdırma yok (404).
        user = User.objects.filter(pk=uid, firma_id=ob.firma_id).first()
        if user is None:
            raise NotFound(detail="Kullanıcı bulunamadı.")
        try:
            uy = org_servisi.uye_ekle(
                actor=request.user, org_birimi=ob, kullanici=user
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(present_org_member(uy), status=status.HTTP_201_CREATED),
        )
