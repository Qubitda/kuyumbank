from django.core.management.base import BaseCommand
from django.db import transaction

from tanimlar.models import AyarMilyem, KiymetliMetal, SatisKanali

METALLER = [
    # (kod, ad, gram_bazli)
    ("ALTIN", "Altın", True),
    ("GUMUS", "Gümüş", True),
    ("PLATIN", "Platin", True),
    ("CELIK", "Çelik", False),
]

AYARLAR = [
    # (metal_kodu, ayar_kodu, ayar_degeri, milyem)  — milyem 0.0-1.0 oranı
    ("ALTIN", "8K",      8,   0.333),
    ("ALTIN", "14K",    14,   0.585),
    ("ALTIN", "18K",    18,   0.750),
    ("ALTIN", "22K",    22,   0.916),
    ("ALTIN", "24K",    24,   0.995),
    ("GUMUS", "925",   925,   0.925),
    ("PLATIN", "950",  950,   0.950),
    ("CELIK", "Ayarsız", 0,   0.000),
]

KANALLAR = [
    # (kod, ad)
    ("KUYUMCU_PANEL", "Kuyumcu paneli"),
    ("CANTACI_PANEL", "Çantacı paneli"),
    ("B2B_API", "B2B API"),
    ("B2C_API", "B2C API"),
]


class Command(BaseCommand):
    help = "Varsayılan metal, ayar/milyem ve satış kanalı kayıtlarını ekler (tekrar çalıştırılabilir)."

    @transaction.atomic
    def handle(self, *args, **options):
        yeni = 0

        metaller = {}
        for kod, ad, gram_bazli in METALLER:
            metal, olustu = KiymetliMetal.objects.get_or_create(
                kod=kod, defaults={"ad": ad, "gram_bazli": gram_bazli}
            )
            metaller[kod] = metal
            yeni += olustu

        for metal_kodu, ayar_kodu, ayar_degeri, milyem in AYARLAR:
            _, olustu = AyarMilyem.objects.get_or_create(
                metal=metaller[metal_kodu],
                ayar_kodu=ayar_kodu,
                defaults={"ayar_degeri": ayar_degeri, "milyem": milyem},
            )
            yeni += olustu

        for kod, ad in KANALLAR:
            _, olustu = SatisKanali.objects.get_or_create(
                kod=kod, defaults={"ad": ad, "aktif": True}
            )
            yeni += olustu

        self.stdout.write(self.style.SUCCESS(f"Tamam. {yeni} yeni kayıt eklendi."))