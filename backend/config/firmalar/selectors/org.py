"""Org birimi tenant/scope selector (ADR-0015 OH-4/OH-5)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.models import OrgBirimi
from firmalar.services.yetki_servisi import can_view_all_tenants


def scope_org_queryset(qs, actor):
    if can_view_all_tenants(actor):
        return qs
    firma = getattr(actor, "firma", None)
    if firma is None:
        return qs.none()
    return qs.filter(firma_id=firma.pk)


def get_org_for_actor(actor, org_id: int) -> OrgBirimi:
    qs = scope_org_queryset(OrgBirimi.objects.all(), actor)
    try:
        return qs.get(pk=org_id)
    except OrgBirimi.DoesNotExist as exc:
        raise ObjectDoesNotExist("OrgBirimi bulunamadı.") from exc


def actor_org_ids(actor) -> set[int]:
    """Aktörün üye olduğu org pk seti (firma yöneticisi tüm firma org'larını görür ayrı)."""
    if actor is None or not getattr(actor, "pk", None):
        return set()
    return set(
        actor.org_uyelikleri.values_list("org_birimi_id", flat=True)
    )
