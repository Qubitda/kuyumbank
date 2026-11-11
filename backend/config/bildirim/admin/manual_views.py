"""Manuel e-posta formu — Django Admin altında."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.urls import path
from django.views.decorators.http import require_http_methods

from bildirim.models import EmailTemplate
from bildirim.services import manual_servisi
from firmalar.services.yetki_servisi import has_perm


class ManualEmailForm(forms.Form):
    to_emails = forms.CharField(
        label="Alıcılar (virgülle)",
        help_text="Örn. a@x.com, b@y.com",
    )
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(aktif=True),
        required=False,
        label="Şablon",
    )
    subject = forms.CharField(required=False, max_length=255, label="Konu")
    body_html = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 10}),
        label="HTML gövde",
    )
    order_id = forms.IntegerField(required=False, label="Sipariş ID")
    context_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Context JSON (allowlist)",
        help_text='Örn. {"firma_adi":"Acme","order_id":"1"}',
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def manual_send_view(request):
    if not (
        has_perm(request.user, "bildirim.send_manual_email")
        or request.user.is_superuser
    ):
        raise PermissionDenied("Manuel e-posta yetkisi yok.")

    form = ManualEmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        raw_to = form.cleaned_data["to_emails"]
        tos = [p.strip() for p in raw_to.split(",") if p.strip()]
        ctx = {}
        raw_ctx = (form.cleaned_data.get("context_json") or "").strip()
        if raw_ctx:
            import json

            try:
                ctx = json.loads(raw_ctx)
            except json.JSONDecodeError as exc:
                form.add_error("context_json", f"JSON hatası: {exc}")
                return render(
                    request,
                    "admin/bildirim/manual_send.html",
                    {"form": form, "title": "Manuel e-posta"},
                )
        try:
            delivery = manual_servisi.enqueue_manual(
                actor=request.user,
                to_emails=tos,
                subject=form.cleaned_data.get("subject") or None,
                body_html=form.cleaned_data.get("body_html") or None,
                template=form.cleaned_data.get("template"),
                context=ctx or None,
                order_id=form.cleaned_data.get("order_id"),
            )
            messages.success(
                request,
                f"Kuyruğa alındı: EmailDelivery#{delivery.pk}. "
                "process_email_queue ile gönderilir.",
            )
            return redirect("admin:bildirim_emaildelivery_changelist")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))

    return render(
        request,
        "admin/bildirim/manual_send.html",
        {"form": form, "title": "Manuel e-posta gönder"},
    )


def get_manual_urls():
    return [
        path(
            "bildirim/manual-send/",
            manual_send_view,
            name="bildirim_manual_send",
        ),
    ]
