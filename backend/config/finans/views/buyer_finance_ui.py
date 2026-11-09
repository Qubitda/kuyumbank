"""F5-032 — Minimal alıcı finans özeti (session; F5-030 servisi)."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from finans.services import buyer_finans_servisi
from siparis.views.buyer_ui import _require_buyer


class BuyerFinanceView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_buyer(request.user)
        pb = (request.GET.get("para_birimi") or "TRY").strip().upper()
        data = buyer_finans_servisi.ozet_for_actor(
            actor=request.user, para_birimi=pb
        )
        buyer_finans_servisi.assert_masked(data)
        return render(request, "buyer/finance.html", {"finance": data})
