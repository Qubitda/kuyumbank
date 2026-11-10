"""Act-as start/stop HTTP — ADR-0021."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods, require_POST

from firmalar.services import act_as_servisi

User = get_user_model()


@login_required
@require_POST
def act_as_start(request, user_id: int):
    actor = getattr(request, "act_as_actor", None) or request.user
    if getattr(request, "act_as_active", False):
        messages.error(request, "Önce mevcut act-as'ı sonlandırın.")
        return redirect("admin:index")
    target = get_object_or_404(User.objects.select_related("firma"), pk=user_id)
    try:
        act_as_servisi.baslat(actor=actor, target=target, session=request.session)
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, str(exc))
        return redirect("admin:firmalar_kullanici_changelist")
    messages.success(
        request,
        f"Act-as: {target.username} ({getattr(target.firma, 'ad', '')})",
    )
    return redirect(act_as_servisi.portal_hedef_url(target))


@login_required
@require_http_methods(["GET", "POST"])
def act_as_stop(request):
    actor = act_as_servisi.durdur(
        session=request.session,
        actor_fallback=getattr(request, "act_as_actor", None),
    )
    messages.info(request, "Act-as sonlandırıldı.")
    if actor is not None and actor.is_staff:
        return redirect("admin:index")
    return redirect("/")
