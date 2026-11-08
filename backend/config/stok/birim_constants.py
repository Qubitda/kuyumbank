"""Stok birimi sabitleri — model import döngüsü olmadan."""


class StokBirimi:
    ADET = "ADET"
    GRAM = "GRAM"
    KARAT = "KARAT"

    CHOICES = (
        (ADET, "Adet"),
        (GRAM, "Gram"),
        (KARAT, "Karat"),
    )
