"""Kur sağlayıcı — tek aktif provider (ADR-0008 B-04 / Dilim 3.3)."""

from django.db import models


class KurSaglayici(models.Model):
    kod = models.CharField("Kod", max_length=32, unique=True)
    ad = models.CharField("Ad", max_length=80)
    aktif = models.BooleanField("Aktif", default=False)
    max_gecikme_saniye = models.PositiveIntegerField(
        "Maksimum gecikme (sn)",
        help_text="Piyasa zamanı ile alınma/now arasındaki üst sınır; aşılırsa gözlem stale.",
    )
    olusturma = models.DateTimeField(auto_now_add=True)
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kur sağlayıcı"
        verbose_name_plural = "Kur sağlayıcıları"
        ordering = ["kod"]
        permissions = [
            ("manage_kur", "Kur politikası yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_gecikme_saniye__gt=0),
                name="kur_saglayici_max_gecikme_pozitif",
            ),
            models.UniqueConstraint(
                fields=["aktif"],
                condition=models.Q(aktif=True),
                name="tek_aktif_kur_saglayici",
            ),
        ]

    def __str__(self):
        durum = "aktif" if self.aktif else "pasif"
        return f"{self.kod} ({durum})"
