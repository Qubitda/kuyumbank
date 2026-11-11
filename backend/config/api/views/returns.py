"""B3 — İade HTTP (return_servisi; oluşturma manage_return)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

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
from api.presenters.finance_ops import present_return
from api.throttles import BuyerRateThrottle, OpsRateThrottle
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from firmalar.role_permissions import P
from lojistik.models import ReturnRequest, Shipment
from lojistik.services import return_servisi
from siparis.models import Order, OrderLine
from siparis.selectors.tenant import OrderNotFound, get_order_for_actor


def _can_manage_returns(user) -> bool:
    return has_perm(user, P["manage_return"]) or can_view_all_tenants(user)


def _can_post_ledger(user) -> bool:
    return has_perm(user, P["post_ledger"])


def _assert_buyer_or_ops(user) -> None:
    if _can_manage_returns(user) or can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "alici_mi", False):
        return
    raise PermissionDenied(detail="İade yalnız alıcı veya platform ops içindir.")


def _scope_returns(qs, actor):
    # manage_return / view_all: tüm iadeler; alıcı: kendi siparişleri
    if _can_manage_returns(actor):
        return qs
    firma_id = getattr(actor, "firma_id", None)
    if firma_id is None:
        return qs.none()
    return qs.filter(order__alici_firma_id=firma_id)


def _get_return(actor, pk: int) -> ReturnRequest:
    qs = ReturnRequest.objects.select_related("order", "shipment").prefetch_related(
        "lines"
    )
    qs = _scope_returns(qs, actor)
    req = qs.filter(pk=pk).first()
    if req is None:
        raise NotFound(detail="İade bulunamadı.")
    return req


def _load_order(actor, order_id: int) -> Order:
    if _can_manage_returns(actor):
        order = Order.objects.filter(pk=order_id).first()
        if order is None:
            raise NotFound(detail="Sipariş bulunamadı.")
        return order
    try:
        return get_order_for_actor(actor, order_id=order_id)
    except OrderNotFound as exc:
        raise NotFound(detail="Sipariş bulunamadı.") from exc


def _load_shipment(actor, shipment_id: int, order: Order) -> Shipment:
    if _can_manage_returns(actor):
        ship = Shipment.objects.filter(pk=shipment_id, order_id=order.pk).first()
        if ship is None:
            raise NotFound(detail="Sevkiyat bulunamadı.")
        return ship
    # Alıcı yolu: kendi sipariş sevkiyatı
    ship = (
        Shipment.objects.filter(
            pk=shipment_id,
            order_id=order.pk,
            order__alici_firma_id=getattr(actor, "firma_id", None),
        ).first()
    )
    if ship is None:
        raise NotFound(detail="Sevkiyat bulunamadı.")
    return ship


def _parse_line_specs(raw_lines, order) -> list[dict]:
    if not isinstance(raw_lines, list) or not raw_lines:
        raise ValidationError(detail={"lines": "En az bir satır gerekir."})
    specs = []
    for item in raw_lines:
        if not isinstance(item, dict):
            raise ValidationError(detail={"lines": "Geçersiz satır."})
        try:
            ol_id = int(item.get("order_line_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                detail={"lines": "order_line_id geçersiz."}
            ) from exc
        try:
            miktar = Decimal(str(item.get("miktar")))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"lines": "miktar geçersiz."}) from exc
        ol = OrderLine.objects.filter(pk=ol_id, order=order).first()
        if ol is None:
            raise ValidationError(
                detail={"lines": f"order_line {ol_id} siparişte yok."}
            )
        specs.append({"order_line": ol, "miktar": miktar})
    return specs


class ReturnListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur (manage_return + Idempotency-Key)."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get_throttles(self):
        if self.request.method == "POST":
            return [OpsRateThrottle()]
        return [BuyerRateThrottle()]

    def get(self, request):
        _assert_buyer_or_ops(request.user)
        qs = ReturnRequest.objects.select_related("order", "shipment")
        qs = _scope_returns(qs, request.user)
        order_id = request.query_params.get("order_id")
        if order_id:
            try:
                oid = int(order_id)
            except (TypeError, ValueError):
                raise NotFound(detail="Sipariş bulunamadı.") from None
            _load_order(request.user, oid)
            qs = qs.filter(order_id=oid)
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        actor = request.user
        return paginate_queryset(
            request,
            qs.prefetch_related("lines"),
            present=lambda r: present_return(r, actor=actor),
        )

    def post(self, request):
        if not _can_manage_returns(request.user):
            raise PermissionDenied(
                detail="İade oluşturma için manage_return gerekir."
            )
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            order_id = int(request.data.get("order_id"))
            shipment_id = int(request.data.get("shipment_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                detail={"order_id": "order_id ve shipment_id zorunlu."}
            ) from exc
        sebep = request.data.get("sebep") or ""
        notlar = request.data.get("notlar") or ""
        order = _load_order(request.user, order_id)
        ship = _load_shipment(request.user, shipment_id, order)
        specs = _parse_line_specs(request.data.get("lines"), order)
        meta = getattr(request, "_idempotency", None) or {}
        try:
            req = return_servisi.olustur(
                actor=request.user,
                order=order,
                shipment=ship,
                sebep=sebep,
                line_specs=specs,
                notlar=notlar,
                idempotency_key=meta.get("key") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        req = (
            ReturnRequest.objects.prefetch_related("lines")
            .select_related("order", "shipment")
            .get(pk=req.pk)
        )
        return self.idempotency_commit(
            request,
            Response(
                present_return(req, actor=request.user),
                status=status.HTTP_201_CREATED,
            ),
        )


class ReturnDetailView(APIView):
    """GET /api/v1/returns/<pk>/"""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_buyer_or_ops(request.user)
        req = _get_return(request.user, pk)
        return Response(present_return(req, actor=request.user))


class _ReturnTransitionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]
    action = ""

    def post(self, request, pk: int):
        if not _can_manage_returns(request.user):
            raise PermissionDenied(detail="İade yönetimi için manage_return gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        req = _get_return(request.user, pk)
        try:
            if self.action == "submit_review":
                req = return_servisi.incelemeye_al(
                    actor=request.user, return_request=req
                )
            elif self.action == "approve":
                mahsup_raw = request.data.get("mahsup", False)
                if isinstance(mahsup_raw, str):
                    mahsup = mahsup_raw.strip().lower() in ("1", "true", "yes", "evet")
                else:
                    mahsup = bool(mahsup_raw)
                if mahsup and not _can_post_ledger(request.user):
                    raise PermissionDenied(
                        detail="Mahsup için finans.post_ledger gerekir."
                    )
                req = return_servisi.onayla(
                    actor=request.user,
                    return_request=req,
                    mahsup=mahsup,
                )
            elif self.action == "reject":
                reason = request.data.get("reason") or ""
                req = return_servisi.reddet(
                    actor=request.user, return_request=req, reason=reason
                )
            elif self.action == "cancel":
                req = return_servisi.iptal_et(
                    actor=request.user, return_request=req
                )
            else:
                raise ValidationError(detail="Bilinmeyen geçiş.")
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        req = (
            ReturnRequest.objects.prefetch_related("lines")
            .select_related("order", "shipment")
            .get(pk=req.pk)
        )
        return self.idempotency_commit(
            request,
            Response(present_return(req, actor=request.user)),
        )


class ReturnSubmitView(_ReturnTransitionView):
    action = "submit_review"


class ReturnApproveView(_ReturnTransitionView):
    action = "approve"


class ReturnRejectView(_ReturnTransitionView):
    action = "reject"


class ReturnCancelView(_ReturnTransitionView):
    action = "cancel"


class ReturnMahsupView(IdempotencyMixin, APIView):
    """POST /api/v1/returns/<pk>/mahsup/ — ADR-0023 MH-1."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        if not _can_post_ledger(request.user):
            raise PermissionDenied(detail="Mahsup için finans.post_ledger gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        # view_all / manage_return ile kapsam; finance view_all ile görür
        if not _can_manage_returns(request.user):
            raise PermissionDenied(detail="İade erişimi yok.")
        req = _get_return(request.user, pk)
        try:
            from finans.services import mahsup_servisi

            mahsup_servisi.iade_mahsup(actor=request.user, return_request=req)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        req = (
            ReturnRequest.objects.prefetch_related("lines")
            .select_related("order", "shipment")
            .get(pk=req.pk)
        )
        return self.idempotency_commit(
            request,
            Response(present_return(req, actor=request.user)),
        )
