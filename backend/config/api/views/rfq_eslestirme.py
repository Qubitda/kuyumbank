"""F10-021 — Platform RFQ katalog eşleştirme HTTP (ADR-0029 JSON-only)."""

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
from api.masking import assert_masked
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.throttles import OpsRateThrottle
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import require_perm
from siparis.models import RFQEslestirme, RFQLine
from siparis.services import rfq_eslestirme_servisi
from urunler.models import Varyant


def _assert_platform_match(user) -> None:
    try:
        require_perm(user, P["approve_eslestirme"])
    except DjangoPermissionDenied as exc:
        raise_drf(exc)
    firma = getattr(user, "firma", None)
    if not (firma and getattr(firma, "platform_mu", False)):
        raise PermissionDenied(
            detail="RFQ eşleştirme yalnız platform kullanıcılarınındır."
        )


def _present_match(row: RFQEslestirme) -> dict:
    data = {
        "id": row.pk,
        "rfq_line_id": row.rfq_line_id,
        "varyant_id": row.onerilen_varyant_id,
        "durum": row.durum,
        "skor": row.skor,
        "kanit": row.kanit or {},
        "allowed_actions": (
            ["approve", "reject"]
            if row.durum == RFQEslestirme.Durum.ONERILDI
            else []
        ),
    }
    assert_masked(data)
    return data


def _get_line(line_id: int) -> RFQLine:
    line = (
        RFQLine.objects.filter(pk=line_id)
        .select_related("rfq")
        .first()
    )
    if line is None:
        raise NotFound(detail="RFQ satırı bulunamadı.")
    return line


def _get_match(pk: int) -> RFQEslestirme:
    row = (
        RFQEslestirme.objects.filter(pk=pk)
        .select_related("rfq_line", "onerilen_varyant")
        .first()
    )
    if row is None:
        raise NotFound(detail="Eşleştirme bulunamadı.")
    return row


class OpsRfqMatchCandidatesView(APIView):
    """GET — aday katalog varyantları (yazmaz)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request, line_id: int):
        line = _get_line(line_id)
        try:
            limit = int(request.query_params.get("limit") or 10)
        except (TypeError, ValueError):
            limit = 10
        try:
            adaylar = rfq_eslestirme_servisi.adaylari_bul(
                actor=request.user, rfq_line=line, limit=limit
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        body = {"rfq_line_id": line.pk, "results": adaylar}
        assert_masked(body)
        return Response(body)


class OpsRfqMatchListCreateView(IdempotencyMixin, APIView):
    """GET satır eşleştirmeleri; POST öner {varyant_id, kanit?, skor?}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request, line_id: int):
        _assert_platform_match(request.user)
        line = _get_line(line_id)
        qs = RFQEslestirme.objects.filter(rfq_line=line).order_by("-pk")
        return Response(
            {
                "rfq_line_id": line.pk,
                "results": [_present_match(r) for r in qs[:100]],
            }
        )

    def post(self, request, line_id: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        line = _get_line(line_id)
        body = request.data if isinstance(request.data, dict) else {}
        try:
            vid = int(body.get("varyant_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"varyant_id": "Zorunlu."}) from exc
        varyant = Varyant.objects.filter(pk=vid).select_related("urun").first()
        if varyant is None:
            raise ValidationError(detail={"varyant_id": "Bulunamadı."})
        skor = body.get("skor")
        if skor not in (None, ""):
            try:
                skor = int(skor)
            except (TypeError, ValueError) as exc:
                raise ValidationError(detail={"skor": "Tam sayı."}) from exc
        else:
            skor = None
        try:
            row = rfq_eslestirme_servisi.oner(
                actor=request.user,
                rfq_line=line,
                varyant=varyant,
                kanit=body.get("kanit"),
                skor=skor,
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(_present_match(row), status=status.HTTP_201_CREATED),
        )


class OpsRfqMatchApproveView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        row = _get_match(pk)
        try:
            row = rfq_eslestirme_servisi.onayla(actor=request.user, eslestirme=row)
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        return self.idempotency_commit(request, Response(_present_match(row)))


class OpsRfqMatchRejectView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        row = _get_match(pk)
        body = request.data if isinstance(request.data, dict) else {}
        neden = body.get("neden") or body.get("red_nedeni") or ""
        try:
            row = rfq_eslestirme_servisi.reddet(
                actor=request.user, eslestirme=row, neden=str(neden)
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        return self.idempotency_commit(request, Response(_present_match(row)))
