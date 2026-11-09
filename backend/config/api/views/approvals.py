"""B4 — OnayTalebi HTTP (onay_servisi)."""

from decimal import Decimal, InvalidOperation

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
from api.presenters.enterprise import present_onay
from api.throttles import BuyerRateThrottle
from firmalar.models import OnayTalebi
from firmalar.role_permissions import P
from firmalar.selectors.onay import (
    OnayNotFound,
    get_onay_for_actor,
    scope_onay_queryset,
)
from firmalar.selectors.org import get_org_for_actor
from firmalar.services import onay_servisi
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor


def _can_manage(user) -> bool:
    return has_perm(user, P["manage_approval"])


def _assert_approver(user) -> None:
    """Rol/yetki kapısı → 403 (B2/B3 buyer uçları ile aynı)."""
    if not _can_manage(user) and not can_view_all_tenants(user):
        raise PermissionDenied(detail="Onay yetkisi için manage_approval gerekir.")
    firma = getattr(user, "firma", None)
    if can_view_all_tenants(user):
        return
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="Onay yalnız alıcı veya platform ops içindir.")


class ApprovalListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur — {tutar, para_birimi?, org_birimi_id?, order_id?, gerekce?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_approver(request.user)
        qs = scope_onay_queryset(OnayTalebi.objects.all(), request.user)
        durum = (request.query_params.get("durum") or "").strip()
        if durum and durum in {c.value for c in OnayTalebi.Durum}:
            qs = qs.filter(durum=durum)
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        can_m = _can_manage(request.user)
        return paginate_queryset(
            request, qs, present=lambda o: present_onay(o, can_manage=can_m)
        )

    def post(self, request):
        _assert_approver(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        firma = request.user.firma
        raw = request.data.get("tutar")
        try:
            tutar = Decimal(str(raw))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"tutar": "Geçersiz tutar."}) from exc
        pb = request.data.get("para_birimi") or "TRY"
        gerekce = request.data.get("gerekce") or ""
        org = None
        raw_org = request.data.get("org_birimi_id")
        if raw_org is not None and raw_org != "":
            try:
                org = get_org_for_actor(request.user, int(raw_org))
            except (ObjectDoesNotExist, TypeError, ValueError) as exc:
                raise NotFound(detail="Org birimi bulunamadı.") from exc
        order = None
        raw_order = request.data.get("order_id")
        if raw_order is not None and raw_order != "":
            try:
                order = get_order_for_actor(request.user, order_id=int(raw_order))
            except (OrderNotFound, TypeError, ValueError) as exc:
                raise NotFound(detail="Sipariş bulunamadı.") from exc
        try:
            ot = onay_servisi.olustur(
                actor=request.user,
                firma=firma,
                tutar=tutar,
                para_birimi=pb,
                org_birimi=org,
                order=order,
                gerekce=gerekce,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(
                present_onay(ot, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class ApprovalDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_approver(request.user)
        try:
            ot = get_onay_for_actor(request.user, onay_id=pk)
        except OnayNotFound as exc:
            raise NotFound(detail="Onay talebi bulunamadı.") from exc
        return Response(present_onay(ot, can_manage=_can_manage(request.user)))


class _ApprovalTransitionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]
    action = ""

    def post(self, request, pk: int):
        _assert_approver(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            ot = get_onay_for_actor(request.user, onay_id=pk)
        except OnayNotFound as exc:
            raise NotFound(detail="Onay talebi bulunamadı.") from exc
        try:
            if self.action == "submit":
                ot = onay_servisi.beklemede_al(actor=request.user, onay=ot)
            elif self.action == "approve":
                ot = onay_servisi.onayla(actor=request.user, onay=ot)
            elif self.action == "reject":
                reason = request.data.get("reason") or ""
                ot = onay_servisi.reddet(
                    actor=request.user, onay=ot, reason=reason
                )
            else:
                raise ValidationError(detail="Bilinmeyen geçiş.")
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request, Response(present_onay(ot, can_manage=True))
        )


class ApprovalSubmitView(_ApprovalTransitionView):
    action = "submit"


class ApprovalApproveView(_ApprovalTransitionView):
    action = "approve"


class ApprovalRejectView(_ApprovalTransitionView):
    action = "reject"
