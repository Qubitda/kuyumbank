"""F5-031 + API-B1 — Platform finans ops API (view_all)."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import apply_ordering, paginate_queryset
from api.permissions import IsAuthenticatedWithFirma
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from finans.models import CariHesap, LedgerEntry, PaymentIntent
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
            ops_finans_servisi.require_ops_finance(request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        qs = apply_ordering(
            CariHesap.objects.all(),
            request,
            whitelist=("guncelleme_tarihi", "pk"),
            default="-guncelleme_tarihi",
        )
        return paginate_queryset(
            request,
            qs,
            present=ops_finans_servisi.present_cari_ops,
            extra={"ops": True},
        )


class OpsFinanceLedgerListView(APIView):
    """GET /api/v1/ops/finance/ledger/"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            ops_finans_servisi.require_ops_finance(request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        qs = apply_ordering(
            LedgerEntry.objects.all(),
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(
            request,
            qs,
            present=ops_finans_servisi.present_ledger_ops,
            extra={"ops": True},
        )


class OpsFinancePaymentListView(APIView):
    """GET /api/v1/ops/finance/payments/"""

    permission_classes = [IsAuthenticatedWithFirma]

    def get(self, request):
        request.query_params.get("firma_id")  # ignore
        try:
            ops_finans_servisi.require_ops_finance(request.user)
        except DjangoPermissionDenied as exc:
            _map_perm(exc)
        qs = apply_ordering(
            PaymentIntent.objects.all(),
            request,
            whitelist=("olusturma_tarihi", "pk"),
            default="-olusturma_tarihi",
        )
        return paginate_queryset(
            request,
            qs,
            present=ops_finans_servisi.present_payment_ops,
            extra={"ops": True},
        )
