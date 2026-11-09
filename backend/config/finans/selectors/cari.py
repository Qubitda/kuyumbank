"""Cari okuma — tenant scope (F5-011)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from firmalar.services.yetki_servisi import can_view_all_tenants
from finans.models import CariHesap


class CariNotFound(Exception):
    pass


def scope_cari_queryset(actor):
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Kimlik gerekli.")
    qs = CariHesap.objects.all()
    if can_view_all_tenants(actor):
        return qs
    firma_id = getattr(actor, "firma_id", None)
    if firma_id is None:
        raise PermissionDenied("Firma yok.")
    return qs.filter(firma_id=firma_id)


def get_cari_for_actor(actor, *, pk: int) -> CariHesap:
    try:
        return scope_cari_queryset(actor).get(pk=pk)
    except CariHesap.DoesNotExist as exc:
        raise CariNotFound() from exc
