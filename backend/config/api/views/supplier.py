"""F7-011 — Supplier API: kendi teklif / stok özeti; alıcı kimliği yok."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.masking import assert_masked
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


class SupplierOfferListView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        firma = request.user.firma
        qs = (
            TedarikciTeklif.objects.filter(tedarikci=firma)
            .order_by("-pk")
            .values("id", "varyant_id", "durum", "versiyon")[:100]
        )
        results = []
        for row in qs:
            item = dict(row)
            # Alıcı kimliği asla
            item.pop("alici_firma_id", None)
            assert_masked(item)
            results.append(item)
        return Response({"count": len(results), "results": results})


class SupplierStockSummaryView(APIView):
    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def get(self, request):
        _require_supplier(request.user)
        firma = request.user.firma
        # Kendi depo bakiyeleri — alıcı yok
        qs = (
            StockBalance.objects.filter(warehouse__sahip_firma=firma)
            .select_related("warehouse")
            .order_by("pk")[:100]
        )
        results = []
        for bal in qs:
            item = {
                "warehouse_id": bal.warehouse_id,
                "varyant_id": bal.varyant_id,
                "on_hand": str(bal.on_hand),
                "reserved": str(bal.reserved),
            }
            assert_masked(item)
            results.append(item)
        return Response({"count": len(results), "results": results})
