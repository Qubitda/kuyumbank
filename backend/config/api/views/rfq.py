"""B4 — RFQ HTTP (rfq_servisi; kör mesaj/revizyon)."""

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
from api.presenters.enterprise import present_rfq
from api.throttles import BuyerRateThrottle
from firmalar.role_permissions import P
from firmalar.selectors.org import get_org_for_actor
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from siparis.models import RFQ
from siparis.selectors.rfq import RFQNotFound, get_rfq_for_actor, scope_rfq_queryset
from siparis.services import rfq_servisi
from urunler.models import Varyant


def _assert_rfq_actor(user) -> None:
    """Rol/yetki kapısı → 403 (B2 Order/Quote/Catalog ile aynı desen).

    Tedarikçi bu buyer RFQ yüzeyine giremez → 403.
    Scope dışı nesne (selector) → 404 (detayda).
    """
    if not has_perm(user, P["manage_rfq"]) and not can_view_all_tenants(user):
        raise PermissionDenied(detail="RFQ yetkisi için manage_rfq gerekir.")
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied(detail="RFQ yalnız alıcı içindir.")


def _buyer_catalog_varyant(varyant_id: int):
    """B2 catalog görünürlük kuralı (catalog.py + pricing_service._assert_yayinli_varyant).

    Ayrı buyer-varyant selector yok; katalog_tenant tedarikçi taslak scope'udur.
    Görünmeyen / olmayan → aynı hata (varlık sızdırılmaz).
    """
    return (
        Varyant.objects.select_related("urun")
        .filter(
            pk=varyant_id,
            aktif=True,
            urun__yayin_durumu="aktif",
            urun__onay_durumu="onayli",
        )
        .first()
    )


def _parse_lines(raw) -> list[dict]:
    if not isinstance(raw, list) or not raw:
        raise ValidationError(detail={"lines": "En az bir satır gerekir."})
    specs = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValidationError(detail={"lines": "Geçersiz satır."})
        try:
            miktar = Decimal(str(item.get("miktar")))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError(detail={"lines": "miktar geçersiz."}) from exc
        varyant = None
        raw_v = item.get("varyant_id")
        if raw_v is not None and raw_v != "":
            try:
                vid = int(raw_v)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    detail={"lines": "varyant_id geçersiz."}
                ) from exc
            varyant = _buyer_catalog_varyant(vid)
            if varyant is None:
                # Yok veya yayında değil — aynı mesaj.
                raise ValidationError(detail={"lines": "Varyant bulunamadı."})
        specs.append(
            {
                "aciklama": item.get("aciklama") or "",
                "miktar": miktar,
                "birim": item.get("birim") or "ADET",
                "varyant": varyant,
            }
        )
    return specs


class RfqListCreateView(IdempotencyMixin, APIView):
    """GET liste; POST oluştur."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request):
        _assert_rfq_actor(request.user)
        qs = scope_rfq_queryset(
            RFQ.objects.prefetch_related("lines", "messages", "revizyonlar"),
            request.user,
        )
        qs = apply_ordering(
            qs,
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(request, qs, present=present_rfq)

    def post(self, request):
        _assert_rfq_actor(request.user)
        if can_view_all_tenants(request.user):
            raise PermissionDenied(
                detail="Ops RFQ oluşturmaz; alıcı manage_rfq kullanır."
            )
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        baslik = request.data.get("baslik") or ""
        talep_tipi = request.data.get("talep_tipi") or RFQ.TalepTipi.STANDART
        sube = None
        raw_sube = request.data.get("sube_id")
        if raw_sube is not None and raw_sube != "":
            try:
                sube = get_org_for_actor(request.user, int(raw_sube))
            except (ObjectDoesNotExist, TypeError, ValueError) as exc:
                raise NotFound(detail="Şube/org bulunamadı.") from exc
        specs = _parse_lines(request.data.get("lines"))
        try:
            rfq = rfq_servisi.olustur(
                actor=request.user,
                baslik=baslik,
                line_specs=specs,
                sube=sube,
                talep_tipi=talep_tipi,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        rfq = get_rfq_for_actor(request.user, rfq_id=rfq.pk)
        return self.idempotency_commit(
            request,
            Response(present_rfq(rfq), status=status.HTTP_201_CREATED),
        )


class RfqDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def get(self, request, pk: int):
        _assert_rfq_actor(request.user)
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        return Response(present_rfq(rfq))


class RfqSendView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        _assert_rfq_actor(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        try:
            rfq = rfq_servisi.gonder(actor=request.user, rfq=rfq)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        rfq = get_rfq_for_actor(request.user, rfq_id=rfq.pk)
        return self.idempotency_commit(request, Response(present_rfq(rfq)))


class RfqMessageView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        _assert_rfq_actor(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        try:
            rfq_servisi.mesaj_ekle(
                actor=request.user,
                rfq=rfq,
                govde=request.data.get("govde") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        return self.idempotency_commit(request, Response(present_rfq(rfq)))


class RfqRevisionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [BuyerRateThrottle]

    def post(self, request, pk: int):
        _assert_rfq_actor(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        try:
            rfq_servisi.revizyon_ekle(
                actor=request.user,
                rfq=rfq,
                ozet=request.data.get("ozet") or "",
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            raise_drf(exc)
        rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        return self.idempotency_commit(request, Response(present_rfq(rfq)))
