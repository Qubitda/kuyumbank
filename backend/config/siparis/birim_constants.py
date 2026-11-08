"""Sepet birimi — stok ile aynı sözlük (U-002); dönüşüm yok."""


class SepetBirimi:
    ADET = "ADET"
    GRAM = "GRAM"
    KARAT = "KARAT"

    CHOICES = (
        (ADET, "Adet"),
        (GRAM, "Gram"),
        (KARAT, "Karat"),
    )
