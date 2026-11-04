from django.db import models


class KiymetliMetal(models.Model):
    kod = models.CharField("Kod", max_length=10, unique=True)  # ALTIN, GUMUS, PLATIN, CELIK
    ad = models.CharField("Ad", max_length=50)
    gram_bazli = models.BooleanField("Gram bazlı fiyat", default=True)

    class Meta:
        verbose_name = "Kıymetli metal"
        verbose_name_plural = "Kıymetli metaller"

    def __str__(self):
        return self.ad


