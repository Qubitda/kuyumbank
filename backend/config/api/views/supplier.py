"""F7-011 + API-B1 — Supplier API: kendi teklif / stok özeti; alıcı kimliği yok."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from api.masking import assert_masked
from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from api.throttles import SupplierRateThrottle
from fiyatlama.models import TedarikciTeklif
from firmalar.services.yetki_servisi import can_view_all_tenants
from stok.models import StockBalance


def _require_supplier(user) -> None:
    if can_view_all_tenants(user):
        return
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "tedarikci_mi", False):
        raise PermissionDenied(detail="Supplier API yalnız tedarikçi firması.")


def _present_offer(teklif: TedarikciTeklif) -> dict:
    item = {
        "id": teklif.pk,
        "varyant_id": teklif.varyant_id,
        "durum": teklif.durum,
        "versiyon": teklif.versiyon,
    }
    assert_masked(item)
    return item


def _present_balance(bal: StockBalance) -> dict:
    item = {
        "warehouse_id": bal.warehouse_id,
        "varyant_id": bal.varyant_id,
        "on_hand": str(bal.on_hand),
        "reserved": str(bal.reserved),
    }
    assert_masked(item)
    return item


class SupplierOfferListView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        firma = request.user.firma
        qs = TedarikciTeklif.objects.filter(tedarikci=firma)
        qs = apply_ordering(qs, request, whitelist=("pk", "versiyon"), default="-pk")
        return paginate_queryset(request, qs, present=_present_offer)


class SupplierStockSummaryView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        firma = request.user.firma
        qs = StockBalance.objects.filter(warehouse__sahip_firma=firma).select_related(
            "warehouse"
        )
        qs = apply_ordering(qs, request, whitelist=("pk",), default="pk")
        return paginate_queryset(request, qs, present=_present_balance)
