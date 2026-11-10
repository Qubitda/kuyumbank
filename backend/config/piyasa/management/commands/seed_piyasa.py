"""Örnek piyasa panosu — Tanımlar metal/ayar + ADR-0022 grup/politika."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from piyasa.models import (
    DarphaneIscilik,
    PiyasaKarPolitikasi,
    PiyasaMarjPolitikasi,
    PiyasaUrun,
)
from tanimlar.models import AyarMilyem, KiymetliMetal


class Command(BaseCommand):
    help = "Piyasa panosu örnek ürünler + politikalar + örnek darphane."

    def handle(self, *args, **options):
        PiyasaMarjPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={"marj_modu": PiyasaMarjPolitikasi.MarjModu.YUZDE},
        )
        PiyasaKarPolitikasi.objects.get_or_create(anahtar="default")

        metal, _ = KiymetliMetal.objects.get_or_create(
            kod="ALTIN", defaults={"ad": "Altın", "gram_bazli": True}
        )
        ayar22 = AyarMilyem.objects.filter(metal=metal, ayar_degeri=22).first()
        if ayar22 is None:
            ayar22 = AyarMilyem.objects.create(
                metal=metal,
                ayar_degeri=22,
                ayar_kodu="22K",
                milyem=Decimal("0.916"),
            )

        rows = [
            {
                "kod": "has",
                "ad": "Has",
                "grup": PiyasaUrun.Grup.HAS,
                "ayar": None,
                "alis_marj": Decimal("0.30"),
                "satis_marj": Decimal("0.30"),
                "sira": 10,
            },
            {
                "kod": "22ayar",
                "ad": "22 Ayar / 916",
                "grup": PiyasaUrun.Grup.AYAR_GRAM,
                "ayar": ayar22,
                "alis_marj": Decimal("0"),
                "satis_marj": Decimal("0"),
                "sira": 20,
            },
            {
                "kod": "gram24",
                "ad": "24 Ayar Gram Altın",
                "grup": PiyasaUrun.Grup.AYAR_GRAM,
                "ayar": None,
                "alis_marj": Decimal("1.50"),
                "satis_marj": Decimal("1.50"),
                "sira": 30,
            },
            {
                "kod": "ceyrek",
                "ad": "Çeyrek Altın",
                "grup": PiyasaUrun.Grup.SARRAFIYE,
                "varyant_etiket": PiyasaUrun.VaryantEtiket.YENI,
                "ayar": None,
                "alis_marj": Decimal("3"),
                "satis_marj": Decimal("3"),
                "gram": Decimal("1.754"),
                "sira": 40,
            },
            {
                "kod": "ons_usd",
                "ad": "Ons (USD)",
                "grup": PiyasaUrun.Grup.HAS,
                "ayar": None,
                "olcek": PiyasaUrun.Olcek.ONS,
                "cikti_pb": PiyasaUrun.CiktiPb.USD,
                "alis_marj": Decimal("0"),
                "satis_marj": Decimal("0"),
                "gram": Decimal("1"),
                "sira": 5,
            },
            {
                "kod": "has_kg",
                "ad": "Has TL/KG",
                "grup": PiyasaUrun.Grup.HAS,
                "ayar": None,
                "olcek": PiyasaUrun.Olcek.KG,
                "cikti_pb": PiyasaUrun.CiktiPb.TRY,
                "alis_marj": Decimal("0"),
                "satis_marj": Decimal("0"),
                "gram": Decimal("1"),
                "sira": 6,
            },
        ]
        yeni = 0
        for r in rows:
            obj, created = PiyasaUrun.objects.update_or_create(
                kod=r["kod"],
                defaults={
                    "ad": r["ad"],
                    "grup": r["grup"],
                    "varyant_etiket": r.get("varyant_etiket", ""),
                    "metal": metal,
                    "ayar": r["ayar"],
                    "olcek": r.get("olcek", PiyasaUrun.Olcek.GRAM),
                    "cikti_pb": r.get("cikti_pb", PiyasaUrun.CiktiPb.TRY),
                    "gram": r.get("gram", Decimal("1")),
                    "alis_marj": r["alis_marj"],
                    "satis_marj": r["satis_marj"],
                    "yuvarlama_adimi": Decimal("10"),
                    "sira": r["sira"],
                    "aktif": True,
                },
            )
            yeni += int(created)
            if obj.kod == "ceyrek":
                for kanal, tl in (
                    (DarphaneIscilik.Kanal.YENI_HAS, Decimal("50")),
                    (DarphaneIscilik.Kanal.ESKI_HAS, Decimal("30")),
                    (DarphaneIscilik.Kanal.BORSA_HAS, Decimal("20")),
                ):
                    DarphaneIscilik.objects.update_or_create(
                        urun=obj,
                        kanal=kanal,
                        defaults={"iscilik_tl": tl, "aktif": True, "sira": 0},
                    )

        self.stdout.write(
            self.style.SUCCESS(f"seed_piyasa tamam. yeni_urun={yeni}")
        )
