"""F4-062 — Minimal alıcı sepet/sipariş ekranı (session; portal değil)."""

from __future__ import annotations

import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.selectors.tenant import (
    CartNotFound,
    OrderNotFound,
    get_cart_for_actor,
    get_order_for_actor,
    scope_order_queryset,
)
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.services.presenters import present_cart, present_order
from siparis.models import Order


def _require_buyer(user):
    if can_view_all_tenants(user):
        raise PermissionDenied("Ops kullanıcıları /buyer yerine admin/API kullanır.")
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied("Yalnız alıcı firma kullanıcıları.")


class BuyerLoginView(LoginView):
    template_name = "buyer/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("buyer-cart")


class BuyerCartView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_buyer(request.user)
        try:
            cart = get_cart_for_actor(request.user)
            dto = present_cart(cart)
        except CartNotFound:
            cart = cart_servisi.al_veya_olustur_sepet(actor=request.user)
            dto = present_cart(cart)
        return render(
            request,
            "buyer/cart.html",
            {"cart": dto, "idempotency_key": f"ui-{uuid.uuid4().hex[:16]}"},
        )


class BuyerCheckoutView(LoginRequiredMixin, View):
    """Tek akış: checkout → order (aynı POST)."""

    login_url = reverse_lazy("buyer-login")

    def post(self, request):
        _require_buyer(request.user)
        key = (request.POST.get("idempotency_key") or "").strip()
        if not key:
            messages.error(request, "idempotency_key zorunlu.")
            return redirect("buyer-cart")
        try:
            co = checkout_servisi.checkout(
                actor=request.user, idempotency_key=key
            )
            order = order_servisi.olustur_from_checkout(
                actor=request.user, checkout_attempt=co.attempt
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("buyer-cart")
        messages.success(request, f"Sipariş oluşturuldu: #{order.pk}")
        return redirect("buyer-order-detail", pk=order.pk)


class BuyerOrderListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_buyer(request.user)
        qs = scope_order_queryset(
            Order.objects.order_by("-olusturma_tarihi", "-pk"),
            request.user,
        )
        orders = [present_order(o, include_lines=False) for o in qs[:50]]
        return render(request, "buyer/orders.html", {"orders": orders})


class BuyerOrderDetailView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request, pk: int):
        _require_buyer(request.user)
        try:
            order = get_order_for_actor(request.user, order_id=pk)
        except OrderNotFound as exc:
            raise Http404("Sipariş bulunamadı.") from exc
        return render(
            request,
            "buyer/order_detail.html",
            {"order": present_order(order)},
        )
