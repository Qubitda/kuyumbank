from django.db import models


class UrunKanal(models.Model):
    """Ürünün hangi satış kanalında yayında olduğu."""

    urun = models.ForeignKey("urunler.Urun", verbose_name="Ürün", related_name="kanallar", on_delete=models.CASCADE)
    kanal = models.ForeignKey(
        "tanimlar.SatisKanali", verbose_name="Kanal", related_name="urun_kanallari", on_delete=models.PROTECT,
    )
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Ürün kanalı"
        verbose_name_plural = "Ürün kanalları"
        constraints = [
            models.UniqueConstraint(fields=["urun", "kanal"], name="benzersiz_urun_kanal"),
        ]

    def __str__(self):
        return f"{self.urun.platform_kodu} → {self.kanal}"
