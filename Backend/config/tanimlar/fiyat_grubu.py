from .taban import TanimTaban


class FiyatGrubu(TanimTaban):
    """Fiyat sözleşmesinin işçilik şartını bağladığı küçük ürün grubu listesi.

    Sözleşme kalemleri kategoriye değil bu gruba bağlanır; böylece kategori
    listesi değişse de sözleşmeler bozulmaz.
    """

    class Meta:
        verbose_name = "Fiyat grubu"
        verbose_name_plural = "Fiyat grupları"
        ordering = ["ad"]
