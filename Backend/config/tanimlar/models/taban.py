from django.db import models


class TanimTaban(models.Model):
    """FiyatGrubu ve SatisKanali için ortak taban.

    `urunler.taban.KatalogTanimTaban` ile alan kümesi aynı tutulur (kod, ad, sira, aktif);
    böylece ileride iki uygulama tek tabana indirilebilir. `sira` sayesinde admin'de
    `list_editable` ile görüntüleme sırası düzenlenebilir.
    """

    kod = models.CharField("Kod", max_length=20, unique=True)
    ad = models.CharField("Ad", max_length=80)
    sira = models.PositiveIntegerField("Sıra", default=0)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        abstract = True
        ordering = ["sira", "ad"]

    def __str__(self):
        return self.ad