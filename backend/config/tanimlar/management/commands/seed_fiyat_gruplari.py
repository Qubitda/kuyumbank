from django.core.management.base import BaseCommand

from tanimlar.models import FiyatGrubu

GRUPLAR = [
    ("ZINCIR_BILEZIK", "Zincir / Bilezik"),
    ("YUZUK_ALYANS", "Yüzük / Alyans"),
    ("KOLYE_KUPE", "Kolye / Küpe"),
    ("GENEL", "Diğer / Genel"),
]


class Command(BaseCommand):
    help = "Varsayılan fiyat gruplarını ekler (tekrar çalıştırılabilir). Adları admin'den değiştirebilirsin."

    def handle(self, *args, **options):
        yeni = 0
        for kod, ad in GRUPLAR:
            _, olustu = FiyatGrubu.objects.get_or_create(kod=kod, defaults={"ad": ad})
            yeni += olustu
        self.stdout.write(self.style.SUCCESS(f"Tamam. {yeni} yeni fiyat grubu eklendi."))
