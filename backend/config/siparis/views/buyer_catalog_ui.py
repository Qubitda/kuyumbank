"""F9-011 — Alıcı katalog browse UI (session; kör)."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View

from siparis.views.buyer_ui import _require_buyer
from urunler.services import buyer_katalog_servisi
from urunler.services.buyer_katalog_servisi import BuyerCatalogNotFound


class BuyerCatalogListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_buyer(request.user)
        q = (request.GET.get("q") or "").strip()
        items = buyer_katalog_servisi.liste(q=q, limit=50)
        return render(
            request,
            "buyer/catalog_list.html",
            {"items": items, "q": q},
        )


class BuyerCatalogDetailView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request, pk: int):
        _require_buyer(request.user)
        try:
            product = buyer_katalog_servisi.detay(urun_id=pk)
        except BuyerCatalogNotFound as exc:
            raise Http404("Ürün bulunamadı.") from exc
        return render(
            request,
            "buyer/catalog_detail.html",
            {"product": product},
        )
