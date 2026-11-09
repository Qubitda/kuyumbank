"""F5-032 — Minimal platform finans ops ekranı (view_all / finance RBAC)."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from finans.services import ops_finans_servisi


class OpsFinanceView(LoginRequiredMixin, View):
    """GET /ops/finance/ — yalnız can_view_all_tenants (PLATFORM_FINANCE vb.)."""

    login_url = reverse_lazy("admin:login")

    def get(self, request):
        try:
            data = ops_finans_servisi.ozet(actor=request.user)
            cari = ops_finans_servisi.liste_cari(actor=request.user, limit=50)
        except PermissionDenied:
            raise
        return render(
            request,
            "ops/finance.html",
            {"ozet": data, "cari": cari},
        )
