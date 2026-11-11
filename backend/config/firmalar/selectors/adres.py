"""FirmaAdresi tenant selector — self-service yalnız kendi firma (ops genişlemesi yok)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from firmalar.models import FirmaAdresi


def scope_adres_queryset(qs, actor):
    """Client firma_id yok sayılır; her zaman actor.firma_id."""
    firma_id = getattr(actor, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(firma_id=firma_id)


def get_adres_for_actor(actor, adres_id: int) -> FirmaAdresi:
    qs = scope_adres_queryset(FirmaAdresi.objects.all(), actor)
    try:
        return qs.get(pk=adres_id)
    except FirmaAdresi.DoesNotExist as exc:
        raise ObjectDoesNotExist("FirmaAdresi bulunamadı.") from exc
