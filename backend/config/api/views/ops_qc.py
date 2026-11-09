"""B5 — Ops QC HTTP (inspection_servisi / olcum_servisi)."""

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
from api.presenters.ops import can_manage_qc, present_inspection, present_measurement
from api.throttles import OpsRateThrottle
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from kalite.models import QualityInspection
from kalite.services import inspection_servisi, olcum_servisi
from siparis.models import Order, OrderLine


def _assert_qc_read(user) -> None:
    if (
        has_perm(user, P["view_qc"])
        or has_perm(user, P["manage_qc"])
        or can_view_all_tenants(user)
    ):
        return
    raise PermissionDenied(detail="QC için view_qc / manage_qc gerekir.")


def _assert_qc_write(user) -> None:
    if has_perm(user, P["manage_qc"]):
        return
    raise PermissionDenied(detail="QC yazma için manage_qc gerekir.")


def _load_order(order_id: int) -> Order:
    order = (
        Order.objects.filter(pk=order_id)
        .prefetch_related("lines")
        .first()
    )
    if order is None:
        raise NotFound(detail="Sipariş bulunamadı.")
    return order


def _get_inspection(pk: int) -> QualityInspection:
    insp = (
        QualityInspection.objects.filter(pk=pk)
        .select_related("order")
        .prefetch_related("measurements")
        .first()
    )
    if insp is None:
        raise NotFound(detail="QC inspection bulunamadı.")
    return insp


class OpsInspectionListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur — {order_id, order_line_id?, notlar?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request):
        _assert_qc_read(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = QualityInspection.objects.select_related("order").prefetch_related(
            "measurements"
        )
        durum = (request.query_params.get("durum") or "").strip()
        if durum and durum in {c.value for c in QualityInspection.Durum}:
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
        can_m = can_manage_qc(request.user)
        return paginate_queryset(
            request,
            qs,
            present=lambda i: present_inspection(i, can_manage=can_m),
            extra={"ops": True},
        )

    def post(self, request):
        _assert_qc_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            oid = int(request.data.get("order_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"order_id": "Geçersiz."}) from exc
        order = _load_order(oid)
        order_line = None
        raw_line = request.data.get("order_line_id")
        if raw_line is not None and raw_line != "":
            try:
                lid = int(raw_line)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    detail={"order_line_id": "Geçersiz."}
                ) from exc
            order_line = order.lines.filter(pk=lid).first()
            if order_line is None:
                raise NotFound(detail="Sipariş satırı bulunamadı.")
        try:
            insp = inspection_servisi.olustur(
                actor=request.user,
                order=order,
                order_line=order_line,
                notlar=request.data.get("notlar") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        insp = _get_inspection(insp.pk)
        return self.idempotency_commit(
            request,
            Response(
                present_inspection(insp, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class OpsInspectionDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request, pk: int):
        _assert_qc_read(request.user)
        insp = _get_inspection(pk)
        return Response(
            present_inspection(insp, can_manage=can_manage_qc(request.user))
        )


class _OpsInspectionTransitionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]
    action = ""

    def post(self, request, pk: int):
        _assert_qc_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        insp = _get_inspection(pk)
        try:
            if self.action == "start":
                insp = inspection_servisi.olcume_al(
                    actor=request.user, inspection=insp
                )
            elif self.action == "pass":
                insp = inspection_servisi.pass_et(
                    actor=request.user, inspection=insp
                )
            elif self.action == "fail":
                insp = inspection_servisi.fail_et(
                    actor=request.user,
                    inspection=insp,
                    reason=request.data.get("reason") or "",
                )
            elif self.action == "cancel":
                insp = inspection_servisi.iptal_et(
                    actor=request.user, inspection=insp
                )
            else:
                raise ValidationError(detail="Bilinmeyen geçiş.")
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        insp = _get_inspection(insp.pk)
        return self.idempotency_commit(
            request, Response(present_inspection(insp, can_manage=True))
        )


class OpsInspectionStartView(_OpsInspectionTransitionView):
    action = "start"


class OpsInspectionPassView(_OpsInspectionTransitionView):
    action = "pass"


class OpsInspectionFailView(_OpsInspectionTransitionView):
    action = "fail"


class OpsInspectionCancelView(_OpsInspectionTransitionView):
    action = "cancel"


class OpsInspectionMeasurementCreateView(IdempotencyMixin, APIView):
    """POST /ops/inspections/<pk>/measurements/ — {order_line_id, olculen, override_gerekce?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _assert_qc_write(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        insp = _get_inspection(pk)
        try:
            lid = int(request.data.get("order_line_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"order_line_id": "Geçersiz."}) from exc
        line = OrderLine.objects.filter(pk=lid, order_id=insp.order_id).first()
        if line is None:
            raise NotFound(detail="Sipariş satırı bulunamadı.")
        try:
            olculen = Decimal(str(request.data.get("olculen")))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"olculen": "Geçersiz."}) from exc
        try:
            m = olcum_servisi.kaydet_olcum(
                actor=request.user,
                inspection=insp,
                order_line=line,
                olculen=olculen,
                override_gerekce=request.data.get("override_gerekce") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(present_measurement(m), status=status.HTTP_201_CREATED),
        )
