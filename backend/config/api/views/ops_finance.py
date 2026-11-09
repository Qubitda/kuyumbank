"""F5-031 — Platform finans ops API (view_all)."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthenticatedWithFirma
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from finans.services import ops_finans_servisi


def _map_perm(exc):
    raise PermissionDenied(detail=str(exc)) from exc


class OpsFinanceSummaryView(APIView):
    """GET /api/v1/ops/finance/ — özet + son hareketler. Client firma_id yok sayılır."""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            data = ops_finans_servisi.ozet(actor=request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        return Response(data)


class OpsFinanceCariListView(APIView):
    """GET /api/v1/ops/finance/cari/"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            items = ops_finans_servisi.liste_cari(actor=request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        return Response({"count": len(items), "results": items, "ops": True})


class OpsFinanceLedgerListView(APIView):
    """GET /api/v1/ops/finance/ledger/"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            items = ops_finans_servisi.liste_ledger(actor=request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        return Response({"count": len(items), "results": items, "ops": True})
