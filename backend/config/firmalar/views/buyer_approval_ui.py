"""F10-014 — Minimal alıcı onay kuyruğu (session; zengin portal değil)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from firmalar.models import OnayTalebi
from firmalar.role_permissions import P
from firmalar.selectors.onay import OnayNotFound, get_onay_for_actor, scope_onay_queryset
from firmalar.services import onay_servisi
from firmalar.services.yetki_servisi import has_perm
from siparis.views.buyer_ui import _require_buyer


def _require_approver(user):
    _require_buyer(user)
    if not has_perm(user, P["manage_approval"]):
        raise PermissionDenied("Onay yetkisi gerekli.")


class BuyerApprovalListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_approver(request.user)
        qs = scope_onay_queryset(
            OnayTalebi.objects.order_by("-olusturma_tarihi", "-pk"),
            request.user,
        )
        durum = (request.GET.get("durum") or OnayTalebi.Durum.BEKLEMEDE).strip()
        if durum in {c.value for c in OnayTalebi.Durum}:
            qs = qs.filter(durum=durum)
        items = list(qs[:50])
        return render(
            request,
            "buyer/approvals.html",
            {
                "approvals": items,
                "durum": durum,
                "durumlar": OnayTalebi.Durum,
            },
        )


class BuyerApprovalActionView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def post(self, request, pk: int):
        _require_approver(request.user)
        action = (request.POST.get("action") or "").strip().lower()
        reason = (request.POST.get("reason") or "").strip()
        try:
            onay = get_onay_for_actor(request.user, onay_id=pk)
        except OnayNotFound as exc:
            raise Http404("Onay talebi bulunamadı.") from exc
        try:
            if action == "onayla":
                onay_servisi.onayla(actor=request.user, onay=onay)
                messages.success(request, f"Onaylandı: OT#{onay.pk}")
            elif action == "reddet":
                onay_servisi.reddet(
                    actor=request.user, onay=onay, reason=reason
                )
                messages.success(request, f"Reddedildi: OT#{onay.pk}")
            elif action == "beklemede":
                onay_servisi.beklemede_al(actor=request.user, onay=onay)
                messages.success(request, f"Beklemeye alındı: OT#{onay.pk}")
            else:
                messages.error(request, "Geçersiz işlem.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect("buyer-approval-list")
