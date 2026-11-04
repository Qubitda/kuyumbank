from django.core.management.base import BaseCommand
from django.db import transaction

from tanimlar.models import FiyatGrubu
from urunler.models import (
    Berraklik, Kategori, KesimKalitesi, Koleksiyon, KopcaTipi, MihlamaTipi, OlcuDegeri, OzelGun, Renk,
    RenkDerecesi, SertifikaKurumu, Stil, TasKesimi, TasMensei, TasTipi, Teknik, YasGrubu,
    ZincirTipi,
)

_TR = str.maketrans("ığüşöçİĞÜŞÖÇ", "igusocIGUSOC")


def kodla(ad):
    """'Çelik Gri' -> 'CELIK_GRI'"""
    temiz = "".join(c if c.isalnum() else "_" for c in ad.translate(_TR))
    while "__" in temiz:
        temiz = temiz.replace("__", "_")
    return temiz.strip("_").upper()[:30]


# Sıra listedeki sıradır (Berraklık/Renk derecesi için anlamlı: ilk = en yüksek kalite).
LISTELER = [
    (Koleksiyon, ["Yeni Koleksiyon"]),
    (Renk, ["Sarı", "Beyaz", "Rose", "Siyah", "Çelik Gri", "Çok Renkli"]),
    (YasGrubu, ["Yetişkin", "Genç", "Çocuk (3-12)", "Bebek (0-2)"]),
    (Teknik, ["Telkari"]),
    (Stil, ["Minimal", "Vintage", "Modern", "Klasik", "Geleneksel"]),
    (OzelGun, ["Nişan", "Düğün", "Hediye", "Doğum", "Doğum Günü", "Anneler Günü", "Babalar Günü",
               "Sevgililer Günü", "Yıldönümü", "Mezuniyet", "Evlilik Teklifi", "Bebek Hediyesi", "Yılbaşı"]),
    (ZincirTipi, ["Halat", "Forse", "Gurmet", "Singapur", "Venedik"]),
    (KopcaTipi, ["Kıskaç", "Bilezik Kilidi", "Vidalı", "Klips"]),
    (TasTipi, ["Pırlanta", "Zirkon", "Safir", "Yakut", "Zümrüt", "İnci", "Ametist", "Topaz"]),
    (TasKesimi, ["Brilliant", "Princess", "Baget", "Oval", "Damla", "Markiz", "Kalp", "Zümrüt Kesim"]),
    (MihlamaTipi, ["Tırnak", "Kanal", "Bezel (Çerçeve)", "Pave", "Gizli"]),
    (TasMensei, ["Doğal", "Laboratuvar üretimi", "Simülant"]),
    (SertifikaKurumu, ["GIA", "IGI", "HRD", "GRS", "Diğer"]),
    (Berraklik, ["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "I1"]),
    (RenkDerecesi, ["D", "E", "F", "G", "H", "I", "J", "K"]),
    (KesimKalitesi, ["Excellent", "Very Good", "Good", "Fair"]),
]

# Başlangıç ölçü değerleri; admin'den düzenlenebilir. (tip, [değerler])
OLCULER = [
    ("yuzuk_no", [str(n) for n in range(8, 31)]),
    ("bilezik_boyu", [f"{n} cm" for n in range(15, 24)]),
    ("zincir_uzunlugu", [f"{n} cm" for n in (35, 38, 40, 42, 45, 50, 55, 60, 70)]),
]

# (ad, fiyat grubu kodu). Alt kategoriler, Excel'deki eşleşme netleşince admin'den eklenir.
KATEGORILER = [
    ("Kolye", "KOLYE_KUPE"),
    ("Yüzük", "YUZUK_ALYANS"),
    ("Küpe", "KOLYE_KUPE"),
    ("Bilezik", "ZINCIR_BILEZIK"),
    ("Alyans", "YUZUK_ALYANS"),
    ("Halhal", "ZINCIR_BILEZIK"),
    ("Kol Düğmesi", "GENEL"),
    ("Charm", "GENEL"),
    ("Set", "GENEL"),
]


class Command(BaseCommand):
    help = "Ürün formundaki seçim listelerini ve ana kategorileri ekler (tekrar çalıştırılabilir)."

    @transaction.atomic
    def handle(self, *args, **options):
        yeni = 0
        for model, adlar in LISTELER:
            for sira, ad in enumerate(adlar, start=1):
                _, olustu = model.objects.get_or_create(kod=kodla(ad), defaults={"ad": ad, "sira": sira})
                yeni += olustu

        for tip, degerler in OLCULER:
            for deger in degerler:
                sira = int("".join(c for c in deger if c.isdigit()))
                _, olustu = OlcuDegeri.objects.get_or_create(tip=tip, deger=deger, defaults={"sira": sira})
                yeni += olustu

        gruplar = {g.kod: g for g in FiyatGrubu.objects.all()}
        if not gruplar:
            self.stdout.write(self.style.ERROR("Önce çalıştır: python manage.py seed_fiyat_gruplari"))
            return
        for sira, (ad, grup_kodu) in enumerate(KATEGORILER, start=1):
            _, olustu = Kategori.objects.get_or_create(
                kod=kodla(ad), defaults={"ad": ad, "sira": sira, "fiyat_grubu": gruplar[grup_kodu]},
            )
            yeni += olustu

        self.stdout.write(self.style.SUCCESS(f"Tamam. {yeni} yeni kayıt eklendi."))
