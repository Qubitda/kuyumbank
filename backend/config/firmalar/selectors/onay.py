"""OnayTalebi tenant scope — alıcı kendi; view_all ops; başkası DoesNotExist."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.models import OnayTalebi
from firmalar.services.yetki_servisi import can_view_all_tenants


class OnayNotFound(ObjectDoesNotExist):
    """404 semantiği — varlık / çapraz tenant sızdırılmaz."""


def scope_onay_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(firma_id=firma_id)
    return qs.none()


def get_onay_for_actor(user, onay_id: int) -> OnayTalebi:
    if user is None or not getattr(user, "is_authenticated", False):
        raise OnayNotFound("Onay talebi bulunamadı.")
    qs = scope_onay_queryset(
        OnayTalebi.objects.select_related("firma", "org_birimi", "order"),
        user,
    )
    try:
        return qs.get(pk=onay_id)
    except OnayTalebi.DoesNotExist as exc:
        raise OnayNotFound("Onay talebi bulunamadı.") from exc
