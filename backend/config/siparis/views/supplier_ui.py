"""ADR-0021 — Tedarikçi HTML portal (okuma iskeleti; yazma API'de)."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from fiyatlama.models import TedarikciTeklif
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from firmalar.role_permissions import P
from siparis.models import RFQ
from siparis.selectors.rfq import scope_supplier_rfq_queryset
from stok.models import StockBalance


def _require_supplier(user):
    if can_view_all_tenants(user):
        raise PermissionDenied(
            "Ops kullanıcıları /supplier yerine act-as veya API kullanır."
        )
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "tedarikci_mi", False):
        raise PermissionDenied("Yalnız tedarikçi firma kullanıcıları.")


class SupplierLoginView(LoginView):
    template_name = "supplier/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("supplier-home")


class SupplierHomeView(LoginRequiredMixin, View):
    login_url = reverse_lazy("supplier-login")

    def get(self, request):
        _require_supplier(request.user)
        firma = request.user.firma
        teklif_n = TedarikciTeklif.objects.filter(tedarikci_id=firma.pk).count()
        stok_n = StockBalance.objects.filter(
            warehouse__sahip_firma_id=firma.pk
        ).count()
        rfq_n = scope_supplier_rfq_queryset(RFQ.objects.all(), request.user).count()
        return render(
            request,
            "supplier/home.html",
            {
                "firma": firma,
                "teklif_n": teklif_n,
                "stok_n": stok_n,
                "rfq_n": rfq_n,
                "can_manage_teklif": has_perm(request.user, P["manage_own_teklif"]),
            },
        )


class SupplierOfferListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("supplier-login")

    def get(self, request):
        _require_supplier(request.user)
        qs = (
            TedarikciTeklif.objects.filter(tedarikci_id=request.user.firma_id)
            .select_related("varyant", "varyant__urun")
            .order_by("-pk")[:100]
        )
        return render(request, "supplier/offers.html", {"offers": qs})


class SupplierStockListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("supplier-login")

    def get(self, request):
        _require_supplier(request.user)
        qs = (
            StockBalance.objects.filter(warehouse__sahip_firma_id=request.user.firma_id)
            .select_related("warehouse", "teklif", "teklif__varyant")
            .order_by("warehouse_id", "-pk")[:200]
        )
        return render(request, "supplier/stock.html", {"balances": qs})


class SupplierRfqListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("supplier-login")

    def get(self, request):
        _require_supplier(request.user)
        qs = scope_supplier_rfq_queryset(
            RFQ.objects.order_by("-olusturma_tarihi", "-pk"),
            request.user,
        )[:50]
        return render(request, "supplier/rfqs.html", {"rfqs": qs})
