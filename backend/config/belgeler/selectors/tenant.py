"""Belge tenant scope — client firma_id güvenilmez (F6-012)."""

from __future__ import annotations

from firmalar.services.yetki_servisi import can_view_all_tenants
from belgeler.models import Document


class DocumentNotFound(LookupError):
    pass


def scope_document_queryset(qs, actor):
    if can_view_all_tenants(actor):
        return qs
    firma = getattr(actor, "firma", None)
    if firma is None:
        return qs.none()
    return qs.filter(firma_id=firma.pk)


def get_document_for_actor(actor, *, document_id: int) -> Document:
    qs = Document.objects.filter(pk=document_id)
    qs = scope_document_queryset(qs, actor)
    doc = qs.first()
    if doc is None:
        raise DocumentNotFound()
    return doc
