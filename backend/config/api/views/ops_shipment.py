"""B5 — Ops sevkiyat HTTP (shipment_servisi / pod_servisi)."""

from __future__ import annotations

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
from api.presenters.ops import can_manage_shipment, present_ops_shipment
from api.throttles import OpsRateThrottle
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from lojistik.models import Shipment
from lojistik.services import pod_servisi, shipment_servisi
from siparis.models import Order


def _assert_ship_ops(user) -> None:
    if has_perm(user, P["manage_shipment"]) or can_view_all_tenants(user):
        return
    raise PermissionDenied(
        detail="Ops sevkiyat için manage_shipment veya view_all gerekir."
    )


def _assert_ship_write(user) -> None:
    if has_perm(user, P["manage_shipment"]):
        return
    raise PermissionDenied(detail="Sevkiyat yazma için manage_shipment gerekir.")


def _load_order(order_id: int) -> Order:
    order = Order.objects.filter(pk=order_id).first()
    if order is None:
        raise NotFound(detail="Sipariş bulunamadı.")
    return order


def _get_shipment(pk: int) -> Shipment:
    ship = Shipment.objects.filter(pk=pk).select_related("order").first()
    if ship is None:
        raise NotFound(detail="Sevkiyat bulunamadı.")
    return ship


class OpsShipmentListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur — {order_id, notlar?, takip_no?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request):
        _assert_ship_ops(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = Shipment.objects.select_related("order")
        durum = (request.query_params.get("durum") or "").strip()
        if durum and durum in {c.value for c in Shipment.Durum}:
            qs = qs.filter(durum=durum)
        order_id = request.query_params.get("order_id")
        if order_id:
            try:
                qs = qs.filter(order_id=int(order_id))
            except (TypeError, ValueError) as exc:
                raise NotFound(detail="Sipariş bulunamadı.") from exc
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        can_m = can_manage_shipment(request.user)
        return paginate_queryset(
            request,
            qs,
            present=lambda s: present_ops_shipment(s, can_manage=can_m),
            extra={"ops": True},
        )

    def post(self, request):
        _assert_ship_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            oid = int(request.data.get("order_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"order_id": "Geçersiz."}) from exc
        order = _load_order(oid)
        try:
            ship = shipment_servisi.olustur(
                actor=request.user,
                order=order,
                notlar=request.data.get("notlar") or "",
                takip_no=request.data.get("takip_no") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        ship = _get_shipment(ship.pk)
        return self.idempotency_commit(
            request,
            Response(
                present_ops_shipment(ship, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class OpsShipmentDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request, pk: int):
        _assert_ship_ops(request.user)
        ship = _get_shipment(pk)
        return Response(
            present_ops_shipment(
                ship, can_manage=can_manage_shipment(request.user)
            )
        )


class _OpsShipmentTransitionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]
    action = ""

    def post(self, request, pk: int):
        _assert_ship_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        ship = _get_shipment(pk)
        try:
            if self.action == "prepare":
                ship = shipment_servisi.hazirla(
                    actor=request.user, shipment=ship
                )
            elif self.action == "dispatch":
                ship = shipment_servisi.sevk_et(
                    actor=request.user,
                    shipment=ship,
                    takip_no=request.data.get("takip_no") or "",
                )
            elif self.action == "deliver":
                ship = shipment_servisi.teslim_et(
                    actor=request.user, shipment=ship
                )
            elif self.action == "cancel":
                ship = shipment_servisi.iptal_et(
                    actor=request.user, shipment=ship
                )
            else:
                raise ValidationError(detail="Bilinmeyen geçiş.")
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        ship = _get_shipment(ship.pk)
        return self.idempotency_commit(
            request, Response(present_ops_shipment(ship, can_manage=True))
        )


class OpsShipmentPrepareView(_OpsShipmentTransitionView):
    action = "prepare"


class OpsShipmentDispatchView(_OpsShipmentTransitionView):
    action = "dispatch"


class OpsShipmentDeliverView(_OpsShipmentTransitionView):
    action = "deliver"


class OpsShipmentCancelView(_OpsShipmentTransitionView):
    action = "cancel"


class OpsShipmentPodCreateView(IdempotencyMixin, APIView):
    """POST /ops/shipments/<pk>/pod/ — {teslim_alan, notlar?, belgeler_ref?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _assert_ship_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        ship = _get_shipment(pk)
        try:
            pod_servisi.kaydet_pod(
                actor=request.user,
                shipment=ship,
                teslim_alan=request.data.get("teslim_alan") or "",
                notlar=request.data.get("notlar") or "",
                belgeler_ref=request.data.get("belgeler_ref") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        ship = _get_shipment(pk)
        return self.idempotency_commit(
            request, Response(present_ops_shipment(ship, can_manage=True))
        )
