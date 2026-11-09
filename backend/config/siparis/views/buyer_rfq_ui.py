"""F10-023 — Minimal RFQ alıcı UI (+ F10-021 katalog dışı satır; kör mesaj)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm
from siparis.models import RFQ
from siparis.selectors.rfq import RFQNotFound, get_rfq_for_actor, scope_rfq_queryset
from siparis.services import rfq_servisi
from siparis.views.buyer_ui import _require_buyer


def _require_rfq_actor(user):
    _require_buyer(user)
    if not has_perm(user, P["manage_rfq"]):
        raise PermissionDenied("RFQ yetkisi gerekli.")


def _present_rfq(rfq: RFQ) -> dict:
    lines = [
        {
            "id": ln.pk,
            "aciklama": ln.aciklama,
            "miktar": str(ln.miktar),
            "birim": ln.birim,
            "katalog_disi": ln.varyant_id is None,
        }
        for ln in rfq.lines.all()
    ]
    messages_dto = [
        {
            "id": m.pk,
            "govde": m.govde,
            "gonderen_rol": m.gonderen_rol,
            "olusturma_tarihi": m.olusturma_tarihi,
        }
        for m in rfq.messages.all()
    ]
    revizyonlar = [
        {
            "sira": r.sira,
            "ozet": r.ozet,
            "gonderen_rol": r.gonderen_rol,
            "olusturma_tarihi": r.olusturma_tarihi,
        }
        for r in rfq.revizyonlar.all()
    ]
    return {
        "id": rfq.pk,
        "baslik": rfq.baslik,
        "talep_tipi": rfq.talep_tipi,
        "durum": rfq.durum,
        "olusturma_tarihi": rfq.olusturma_tarihi,
        "lines": lines,
        "messages": messages_dto,
        "revizyonlar": revizyonlar,
        "can_send": rfq.durum == RFQ.Durum.TASLAK,
        "can_message": rfq.durum
        in {RFQ.Durum.TASLAK, RFQ.Durum.GONDERILDI},
        "can_revise": rfq.talep_tipi == RFQ.TalepTipi.OZEL_URETIM
        and rfq.durum
        in {RFQ.Durum.TASLAK, RFQ.Durum.GONDERILDI},
    }


class BuyerRfqListView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_rfq_actor(request.user)
        qs = scope_rfq_queryset(
            RFQ.objects.order_by("-olusturma_tarihi", "-pk"),
            request.user,
        )
        items = [_present_rfq(r) for r in qs.prefetch_related("lines", "messages")[:50]]
        return render(request, "buyer/rfq_list.html", {"rfqs": items})


class BuyerRfqCreateView(LoginRequiredMixin, View):
    """F10-021 katalog dışı + F10-022 özel üretim (varyantsız satır)."""

    login_url = reverse_lazy("buyer-login")

    def get(self, request):
        _require_rfq_actor(request.user)
        return render(
            request,
            "buyer/rfq_create.html",
            {"talep_tipleri": RFQ.TalepTipi},
        )

    def post(self, request):
        _require_rfq_actor(request.user)
        baslik = (request.POST.get("baslik") or "").strip()
        aciklama = (request.POST.get("aciklama") or "").strip()
        birim = (request.POST.get("birim") or "ADET").strip().upper() or "ADET"
        tip = (request.POST.get("talep_tipi") or RFQ.TalepTipi.KATALOG_DISI).strip()
        try:
            miktar = Decimal(str(request.POST.get("miktar") or "0"))
        except (InvalidOperation, TypeError):
            messages.error(request, "Miktar geçersiz.")
            return redirect("buyer-rfq-create")
        if not aciklama:
            messages.error(request, "Açıklama zorunlu.")
            return redirect("buyer-rfq-create")
        default_baslik = (
            "Özel üretim talebi"
            if tip == RFQ.TalepTipi.OZEL_URETIM
            else "Katalog dışı talep"
        )
        try:
            rfq = rfq_servisi.olustur(
                actor=request.user,
                baslik=baslik or default_baslik,
                talep_tipi=tip,
                line_specs=[
                    {
                        "aciklama": aciklama,
                        "miktar": miktar,
                        "birim": birim,
                        # varyant yok → F10-021 / F10-022
                    }
                ],
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("buyer-rfq-create")
        messages.success(request, f"RFQ oluşturuldu: #{rfq.pk}")
        return redirect("buyer-rfq-detail", pk=rfq.pk)


class BuyerRfqDetailView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def get(self, request, pk: int):
        _require_rfq_actor(request.user)
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise Http404("RFQ bulunamadı.") from exc
        return render(
            request,
            "buyer/rfq_detail.html",
            {"rfq": _present_rfq(rfq)},
        )


class BuyerRfqSendView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def post(self, request, pk: int):
        _require_rfq_actor(request.user)
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise Http404("RFQ bulunamadı.") from exc
        try:
            rfq = rfq_servisi.gonder(actor=request.user, rfq=rfq)
            messages.success(request, f"RFQ gönderildi: #{rfq.pk}")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect("buyer-rfq-detail", pk=pk)


class BuyerRfqMessageView(LoginRequiredMixin, View):
    login_url = reverse_lazy("buyer-login")

    def post(self, request, pk: int):
        _require_rfq_actor(request.user)
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise Http404("RFQ bulunamadı.") from exc
        govde = (request.POST.get("govde") or "").strip()
        try:
            rfq_servisi.mesaj_ekle(actor=request.user, rfq=rfq, govde=govde)
            messages.success(request, "Mesaj eklendi.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect("buyer-rfq-detail", pk=pk)


class BuyerRfqRevisionView(LoginRequiredMixin, View):
    """F10-022 — özel üretim revizyon özeti ekle."""

    login_url = reverse_lazy("buyer-login")

    def post(self, request, pk: int):
        _require_rfq_actor(request.user)
        try:
            rfq = get_rfq_for_actor(request.user, rfq_id=pk)
        except RFQNotFound as exc:
            raise Http404("RFQ bulunamadı.") from exc
        ozet = (request.POST.get("ozet") or "").strip()
        try:
            rev = rfq_servisi.revizyon_ekle(
                actor=request.user, rfq=rfq, ozet=ozet
            )
            messages.success(request, f"Revizyon v{rev.sira} kaydedildi.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        return redirect("buyer-rfq-detail", pk=pk)
