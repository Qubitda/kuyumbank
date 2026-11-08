from django.db import models


class KatalogTanimTaban(models.Model):
    """Ürün formundaki seçim listelerinin ortak tabanı (renk, taş tipi, stil...)."""

    kod = models.CharField("Kod", max_length=30, unique=True)
    ad = models.CharField("Ad", max_length=80)
    sira = models.PositiveIntegerField("Sıra", default=0)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        abstract = True
        ordering = ["sira", "ad"]

    def __str__(self):
        return self.ad
