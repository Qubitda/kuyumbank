"""ADR-0030 — `/api/v1/ops/products/` platform katalog yazma HTTP."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.authentication import enforce_csrf
from api.mixins import IdempotencyMixin
from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.presenters.ops_products import present_ops_product, present_ops_variant
from api.throttles import OpsRateThrottle
from api.views.auth import _django_ve_to_drf
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm
from urunler.models import Urun
from urunler.services import (
    onaya_gonder,
    onayla,
    pasife_al,
    reddet,
    taslak_urun_olustur,
    varyant_ekle,
    yayina_al,
)


def _can_ops_products(user) -> bool:
    return (
        has_perm(user, P["submit_urun"])
        or has_perm(user, P["approve_urun"])
        or has_perm(user, P["publish_urun"])
    )


def _require_ops_products(user) -> None:
    firma = getattr(user, "firma", None)
    if not (firma and getattr(firma, "platform_mu", False)):
        raise PermissionDenied(detail="Ops ürün yalnız platform.")
    if not _can_ops_products(user):
        raise PermissionDenied(detail="Ürün ops yetkisi yok.")


def _get_urun(pk: int) -> Urun:
    urun = (
        Urun.objects.select_related("kategori", "ayar", "olusturan_firma")
        .prefetch_related("varyantlar")
        .filter(pk=pk)
        .first()
    )
    if urun is None:
        raise NotFound(detail="Ürün bulunamadı.")
    return urun


class OpsProductListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST taslak create."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request):
        _require_ops_products(request.user)
        qs = (
            Urun.objects.select_related("kategori", "ayar")
            .annotate(
                varyant_count=Count(
                    "varyantlar", filter=Q(varyantlar__aktif=True)
                )
            )
        )
        onay = (request.query_params.get("onay_durumu") or "").strip()
        if onay:
            qs = qs.filter(onay_durumu=onay)
        yayin = (request.query_params.get("yayin_durumu") or "").strip()
        if yayin:
            qs = qs.filter(yayin_durumu=yayin)
        term = (request.query_params.get("q") or "").strip()
        if term:
            qs = qs.filter(
                Q(ad__icontains=term) | Q(platform_kodu__icontains=term)
            )
        qs = apply_ordering(
            qs, request, whitelist=("pk", "ad", "platform_kodu"), default="-pk"
        )
        return paginate_queryset(
            request,
            qs,
            present=lambda u: present_ops_product(u, user=request.user),
        )

    def post(self, request):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        body = request.data if isinstance(request.data, dict) else {}
        try:
            kid = int(body.get("kategori_id"))
            aid = int(body.get("ayar_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                detail={"kategori_id": "kategori_id ve ayar_id zorunlu tam sayı."}
            ) from exc
        try:
            sk = body.get("satis_kanali_id")
            urun = taslak_urun_olustur(
                actor=request.user,
                ad=body.get("ad") or "",
                kategori_id=kid,
                ayar_id=aid,
                aciklama=body.get("aciklama") or "",
                fiyat_tipi=(body.get("fiyat_tipi") or "gram").strip() or "gram",
                satis_kanali_id=int(sk) if sk not in (None, "") else None,
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True),
            status=status.HTTP_201_CREATED,
        )
        return self.idempotency_commit(request, response)


class OpsProductDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def get(self, request, pk: int):
        _require_ops_products(request.user)
        urun = _get_urun(pk)
        return Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )


class OpsProductVariantCreateView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        body = request.data if isinstance(request.data, dict) else {}
        renk_id = body.get("renk_id")
        try:
            v = varyant_ekle(
                actor=request.user,
                urun=urun,
                gram=body.get("gram"),
                renk_id=int(renk_id) if renk_id not in (None, "") else None,
                ek_bedel=body.get("ek_bedel"),
            )
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_variant(v), status=status.HTTP_201_CREATED
        )
        return self.idempotency_commit(request, response)


class OpsProductSubmitView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        try:
            urun = onaya_gonder(urun, request.user)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )
        return self.idempotency_commit(request, response)


class OpsProductApproveView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        try:
            urun = onayla(urun, request.user)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )
        return self.idempotency_commit(request, response)


class OpsProductRejectView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        body = request.data if isinstance(request.data, dict) else {}
        neden = body.get("neden") or body.get("reason") or ""
        try:
            urun = reddet(urun, request.user, neden)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )
        return self.idempotency_commit(request, response)


class OpsProductPublishView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        body = request.data if isinstance(request.data, dict) else {}
        durum = (body.get("durum") or "aktif").strip() or "aktif"
        try:
            urun = yayina_al(urun, request.user, durum=durum)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )
        return self.idempotency_commit(request, response)


class OpsProductUnpublishView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [OpsRateThrottle]

    def post(self, request, pk: int):
        _require_ops_products(request.user)
        enforce_csrf(request)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        urun = get_object_or_404(Urun, pk=pk)
        try:
            urun = pasife_al(urun, request.user)
        except DjangoValidationError as exc:
            raise _django_ve_to_drf(exc) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc
        response = Response(
            present_ops_product(urun, user=request.user, include_variants=True)
        )
        return self.idempotency_commit(request, response)
