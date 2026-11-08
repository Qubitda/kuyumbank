"""Kur tipi sabitleri (ADR-0008 B-05 / K-019)."""

from django.db import models


class KurTipi(models.TextChoices):
    ALIS = "alis", "Alış"
    SATIS = "satis", "Satış"
    EFEKTIF = "efektif", "Efektif"
    PLATFORM = "platform", "Platform"


class KurTaraf(models.TextChoices):
    ALICI = "alici", "Alıcı"
    TEDARIKCI = "tedarikci", "Tedarikçi"
