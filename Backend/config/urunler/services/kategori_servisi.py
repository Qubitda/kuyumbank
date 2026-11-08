"""Kategori ağacı taşıma (K-016)."""

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Kategori


def kategori_tasi(kategori: Kategori, yeni_ust: Kategori | None) -> Kategori:
    """Kategoriyi yeni üste taşır; alt ağaç derinliği MAKS_DERINLIK'i aşamaz.

    Transaction içinde kilit + full_clean. Admin/API aynı servisi kullanmalı.
    """
    with transaction.atomic():
        kategori = Kategori.objects.select_for_update().get(pk=kategori.pk)
        if yeni_ust is not None:
            yeni_ust = Kategori.objects.select_for_update().get(pk=yeni_ust.pk)
            if yeni_ust.pk == kategori.pk:
                raise ValidationError({"ust": "Bir kategori kendisinin altına konamaz."})

        kategori.ust = yeni_ust
        kategori.full_clean()
        kategori.save()
        return kategori
