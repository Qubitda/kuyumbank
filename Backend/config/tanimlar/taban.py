from django.db import models


class TanimTaban(models.Model):
    kod = models.CharField("Kod", max_length=20, unique=True)
    ad = models.CharField("Ad", max_length=80)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.ad