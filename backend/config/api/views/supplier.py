"""F7-011 + API-B6 — Supplier teklif/stok yazma + ters kör RFQ."""

from __future__ import annotations

from datetime import date
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
from api.presenters.supplier import (
    present_balance,
    present_movement,
    present_offer,
    present_rfq_supplier,
)
from api.throttles import SupplierRateThrottle
from fiyatlama.models import TedarikciTeklif
from fiyatlama.services import teklif_servisi
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from siparis.models import RFQ
from siparis.selectors.rfq import (
    RFQNotFound,
    get_supplier_rfq_for_actor,
    scope_supplier_rfq_queryset,
)
from siparis.services import rfq_servisi
from stok.models import StockBalance, Warehouse
from stok.services import ledger_servisi
from urunler.models import Varyant


def _require_supplier(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "tedarikci_mi", False):
        raise PermissionDenied(detail="Supplier API yalnız tedarikçi firması.")


def _can_manage_offers(user) -> bool:
    return has_perm(user, P["manage_own_teklif"]) or can_view_all_tenants(user)


def _own_offers_qs(user):
    qs = TedarikciTeklif.objects.all()
    if can_view_all_tenants(user):
        return qs
    return qs.filter(tedarikci_id=user.firma_id)


def _get_own_offer(user, pk: int) -> TedarikciTeklif:
    teklif = _own_offers_qs(user).filter(pk=pk).first()
    if teklif is None:
        raise NotFound(detail="Teklif bulunamadı.")
    return teklif


def _own_stock_qs(user):
    qs = StockBalance.objects.select_related("warehouse")
    if can_view_all_tenants(user):
        return qs
    return qs.filter(warehouse__sahip_firma_id=user.firma_id)


class SupplierOfferListView(IdempotencyMixin, APIView):
    """GET liste; POST taslak create (`teklif_servisi.taslak_olustur`)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = _own_offers_qs(request.user)
        durum = (request.query_params.get("durum") or "").strip()
        if durum and durum in {c.value for c in TedarikciTeklif.Durum}:
            qs = qs.filter(durum=durum)
        qs = apply_ordering(
            qs, request, whitelist=("pk", "versiyon", "durum"), default="-pk"
        )
        can_m = _can_manage_offers(request.user)
        return paginate_queryset(
            request, qs, present=lambda t: present_offer(t, can_manage=can_m)
        )

    def post(self, request):
        _require_supplier(request.user)
        if not _can_manage_offers(request.user):
            raise PermissionDenied(detail="Teklif create için manage_own_teklif gerekir.")
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        body = request.data if isinstance(request.data, dict) else {}
        body.get("tedarikci_id")  # ignore — tenant actor.firma
        try:
            vid = int(body.get("varyant_id"))
        except (TypeError, ValueError) as exc:
            raise ValidationError(detail={"varyant_id": "Zorunlu tam sayı."}) from exc
        varyant = Varyant.objects.filter(pk=vid, aktif=True).select_related("urun").first()
        if varyant is None:
            raise ValidationError(detail={"varyant_id": "Aktif varyant bulunamadı."})
        fiyat_modeli = (body.get("fiyat_modeli") or "").strip()
        gram = birim = None
        if body.get("gram") not in (None, ""):
            try:
                gram = Decimal(str(body.get("gram")))
            except (InvalidOperation, TypeError) as exc:
                raise ValidationError(detail={"gram": "Geçersiz."}) from exc
        if body.get("birim_fiyat") not in (None, ""):
            try:
                birim = Decimal(str(body.get("birim_fiyat")))
            except (InvalidOperation, TypeError) as exc:
                raise ValidationError(detail={"birim_fiyat": "Geçersiz."}) from exc
        iscilik = None
        if body.get("iscilik_override") not in (None, ""):
            try:
                iscilik = Decimal(str(body.get("iscilik_override")))
            except (InvalidOperation, TypeError) as exc:
                raise ValidationError(detail={"iscilik_override": "Geçersiz."}) from exc
        def _date(val):
            if val in (None, ""):
                return None
            if isinstance(val, date):
                return val
            try:
                return date.fromisoformat(str(val)[:10])
            except ValueError as exc:
                raise ValidationError(detail={"gecerlilik": "Tarih YYYY-MM-DD."}) from exc

        gun = body.get("uretim_suresi_gun")
        if gun in (None, ""):
            gun_v = None
        else:
            try:
                gun_v = int(gun)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    detail={"uretim_suresi_gun": "Tam sayı gerekir."}
                ) from exc
        try:
            teklif = teklif_servisi.taslak_olustur(
                request.user,
                varyant=varyant,
                fiyat_modeli=fiyat_modeli,
                gram=gram,
                birim_fiyat=birim,
                tedarikci_kodu=str(body.get("tedarikci_kodu") or ""),
                gecerlilik_baslangic=_date(body.get("gecerlilik_baslangic")),
                gecerlilik_bitis=_date(body.get("gecerlilik_bitis")),
                temin_tipi=body.get("temin_tipi") or None,
                uretim_suresi_gun=gun_v,
                iscilik_override=iscilik,
                para_birimi=str(body.get("para_birimi") or "TRY"),
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(
                present_offer(teklif, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class SupplierOfferDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request, pk: int):
        _require_supplier(request.user)
        teklif = _get_own_offer(request.user, pk)
        return Response(
            present_offer(teklif, can_manage=_can_manage_offers(request.user))
        )


class SupplierOfferSubmitView(IdempotencyMixin, APIView):
    """POST — TASLAK → ONAY_BEKLIYOR (teklif_servisi.onaya_gonder)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request, pk: int):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        teklif = _get_own_offer(request.user, pk)
        try:
            teklif = teklif_servisi.onaya_gonder(teklif, request.user)
        except DjangoValidationError as exc:
            raise_drf(exc, as_conflict=True)
        except DjangoPermissionDenied as exc:
            raise_drf(exc)
        teklif = _get_own_offer(request.user, teklif.pk)
        return self.idempotency_commit(
            request,
            Response(present_offer(teklif, can_manage=True)),
        )


class SupplierOfferDeactivateView(IdempotencyMixin, APIView):
    """POST — YAYINDA → PASIF."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request, pk: int):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        teklif = _get_own_offer(request.user, pk)
        try:
            teklif = teklif_servisi.pasifle(teklif, request.user)
        except DjangoValidationError as exc:
            raise_drf(exc, as_conflict=True)
        except DjangoPermissionDenied as exc:
            raise_drf(exc)
        teklif = _get_own_offer(request.user, teklif.pk)
        return self.idempotency_commit(
            request,
            Response(present_offer(teklif, can_manage=True)),
        )


class SupplierOfferVersionView(IdempotencyMixin, APIView):
    """POST — YAYINDA → yeni ONAY_BEKLIYOR versiyon."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request, pk: int):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        teklif = _get_own_offer(request.user, pk)
        body = request.data if isinstance(request.data, dict) else {}
        gram = body.get("gram")
        birim_fiyat = body.get("birim_fiyat")
        kwargs = {}
        if gram is not None:
            try:
                kwargs["gram"] = Decimal(str(gram))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValidationError(detail={"gram": "Geçersiz decimal."}) from exc
        if birim_fiyat is not None:
            try:
                kwargs["birim_fiyat"] = Decimal(str(birim_fiyat))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValidationError(
                    detail={"birim_fiyat": "Geçersiz decimal."}
                ) from exc
        if body.get("fiyat_modeli"):
            kwargs["fiyat_modeli"] = str(body["fiyat_modeli"])
        try:
            yeni = teklif_servisi.yeni_versiyon_olustur(
                teklif, request.user, **kwargs
            )
        except DjangoValidationError as exc:
            raise_drf(exc, as_conflict=True)
        except DjangoPermissionDenied as exc:
            raise_drf(exc)
        yeni = _get_own_offer(request.user, yeni.pk)
        return self.idempotency_commit(
            request,
            Response(
                present_offer(yeni, can_manage=True),
                status=status.HTTP_201_CREATED,
            ),
        )


class SupplierStockSummaryView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = _own_stock_qs(request.user)
        qs = apply_ordering(qs, request, whitelist=("pk",), default="pk")
        return paginate_queryset(request, qs, present=present_balance)


class SupplierStockAdjustView(IdempotencyMixin, APIView):
    """POST — ledger_servisi.duzeltme (manage_own_warehouse)."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        body = request.data if isinstance(request.data, dict) else {}
        try:
            wh_id = int(body.get("warehouse_id"))
            teklif_id = int(body.get("teklif_id"))
            miktar = Decimal(str(body.get("miktar")))
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise ValidationError(
                detail="warehouse_id, teklif_id ve miktar zorunlu."
            ) from exc
        neden = body.get("neden") or ""

        wh = Warehouse.objects.filter(pk=wh_id).first()
        if wh is None:
            raise NotFound(detail="Depo bulunamadı.")
        if not can_view_all_tenants(request.user):
            if wh.sahip_firma_id != request.user.firma_id:
                raise NotFound(detail="Depo bulunamadı.")
        teklif = _get_own_offer(request.user, teklif_id)

        try:
            mv = ledger_servisi.duzeltme(
                actor=request.user,
                warehouse=wh,
                teklif=teklif,
                miktar=miktar,
                neden=neden,
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        return self.idempotency_commit(
            request,
            Response(present_movement(mv), status=status.HTTP_201_CREATED),
        )


class SupplierRfqListView(APIView):
    """GET — GONDERILDI havuzu; alıcı kimliği yok."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        request.query_params.get("firma_id")  # ignore
        qs = scope_supplier_rfq_queryset(
            RFQ.objects.prefetch_related("lines", "messages", "revizyonlar"),
            request.user,
        )
        qs = apply_ordering(
            qs, request, whitelist=("olusturma_tarihi", "pk"), default="-pk"
        )
        return paginate_queryset(request, qs, present=present_rfq_supplier)


class SupplierRfqDetailView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request, pk: int):
        _require_supplier(request.user)
        try:
            rfq = get_supplier_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        return Response(present_rfq_supplier(rfq))


class SupplierRfqMessageView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request, pk: int):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        body = request.data if isinstance(request.data, dict) else {}
        try:
            rfq = get_supplier_rfq_for_actor(request.user, rfq_id=pk)
            rfq_servisi.mesaj_ekle(
                actor=request.user, rfq=rfq, govde=body.get("govde") or ""
            )
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        rfq = get_supplier_rfq_for_actor(request.user, rfq_id=pk)
        return self.idempotency_commit(
            request, Response(present_rfq_supplier(rfq))
        )


class SupplierRfqRevisionView(IdempotencyMixin, APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request, pk: int):
        _require_supplier(request.user)
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        body = request.data if isinstance(request.data, dict) else {}
        try:
            rfq = get_supplier_rfq_for_actor(request.user, rfq_id=pk)
            rfq_servisi.revizyon_ekle(
                actor=request.user, rfq=rfq, ozet=body.get("ozet") or ""
            )
        except RFQNotFound as exc:
            raise NotFound(detail="RFQ bulunamadı.") from exc
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)
        rfq = get_supplier_rfq_for_actor(request.user, rfq_id=pk)
        return self.idempotency_commit(
            request, Response(present_rfq_supplier(rfq))
        )
