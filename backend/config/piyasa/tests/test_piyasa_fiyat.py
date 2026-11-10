"""ADR-0020/0022 — global marj + PANO/MANUEL + kar + darphane."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from piyasa.models import (
    DarphaneIscilik,
    PiyasaKarPolitikasi,
    PiyasaMarjPolitikasi,
    PiyasaUrun,
)
from piyasa.services import kar_yardimcisi, piyasa_fiyat_servisi
from tanimlar.models import (
    AyarMilyem,
    KiymetliMetal,
    KurPolitikasi,
    KurSaglayici,
    KurTipi,
    MetalKuru,
)

User = get_user_model()


class PiyasaFiyatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.ops = User(
            username="pano_ops",
            firma=platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.ops.set_password("x")
        cls.ops.save()
        sync_user_role_groups(cls.ops)

        cls.metal = KiymetliMetal.objects.create(
            kod="AU_PANO", ad="Altın Pano", gram_bazli=True
        )
        cls.ayar22 = AyarMilyem.objects.create(
            metal=cls.metal,
            ayar_degeri=22,
            ayar_kodu="22K",
            milyem=Decimal("0.916"),
        )
        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        cls.saglayici = KurSaglayici.objects.create(
            kod="PANO_FEED",
            ad="Pano feed",
            aktif=True,
            max_gecikme_saniye=3600,
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )
        now = timezone.now()
        for tip, fiyat in (
            (KurTipi.SATIS, Decimal("6000.0000")),
            (KurTipi.ALIS, Decimal("5990.0000")),
        ):
            MetalKuru.objects.create(
                metal=cls.metal,
                saglayici=cls.saglayici,
                kur_tipi=tip,
                zaman=now,
                alinma_zamani=now,
                saf_birim_fiyat=fiyat,
                kaynak="api",
            )

        PiyasaMarjPolitikasi.objects.update_or_create(
            anahtar="default",
            defaults={"marj_modu": PiyasaMarjPolitikasi.MarjModu.YUZDE},
        )
        PiyasaKarPolitikasi.objects.get_or_create(anahtar="default")

        cls.has = PiyasaUrun.objects.create(
            kod="has",
            ad="Has",
            grup=PiyasaUrun.Grup.HAS,
            metal=cls.metal,
            gram=Decimal("1"),
            alis_marj=Decimal("5"),
            satis_marj=Decimal("2"),
            yuvarlama_adimi=Decimal("10"),
            sira=1,
        )
        cls.a22 = PiyasaUrun.objects.create(
            kod="22ayar",
            ad="22 Ayar",
            grup=PiyasaUrun.Grup.AYAR_GRAM,
            metal=cls.metal,
            ayar=cls.ayar22,
            gram=Decimal("1"),
            alis_marj=Decimal("0"),
            satis_marj=Decimal("0"),
            yuvarlama_adimi=Decimal("10"),
            sira=2,
        )
        DarphaneIscilik.objects.create(
            urun=cls.has,
            kanal=DarphaneIscilik.Kanal.YENI_HAS,
            iscilik_tl=Decimal("40"),
        )

    def test_ayar_metal_tanimlardan(self):
        self.a22.refresh_from_db()
        self.assertEqual(self.a22.metal_id, self.ayar22.metal_id)

    def test_baz_fiyat_has(self):
        baz = piyasa_fiyat_servisi.baz_fiyat("has")
        self.assertEqual(baz["satis"], Decimal("6120.00"))
        self.assertEqual(baz["alis"], Decimal("5690.00"))
        self.assertEqual(baz["grup"], PiyasaUrun.Grup.HAS)
        self.assertEqual(baz["marj_modu"], "YUZDE")

    def test_global_marj_modu_tl(self):
        piyasa_fiyat_servisi.set_marj_modu("TL")
        self.has.alis_marj = Decimal("25")
        self.has.satis_marj = Decimal("30")
        self.has.yuvarlama_adimi = Decimal("0")
        self.has.save()
        baz = piyasa_fiyat_servisi.baz_fiyat("has")
        # alış 5990-25, satış 6000+30
        self.assertEqual(baz["alis"], Decimal("5965.00"))
        self.assertEqual(baz["satis"], Decimal("6030.00"))
        self.assertEqual(baz["marj_modu"], "TL")

    def test_baz_fiyat_22ayar_milyem(self):
        baz = piyasa_fiyat_servisi.baz_fiyat("22ayar")
        self.assertEqual(baz["satis"], Decimal("5500.00"))

    def test_baz_fiyat_kg(self):
        PiyasaUrun.objects.create(
            kod="has_kg",
            ad="Has KG",
            grup=PiyasaUrun.Grup.HAS,
            metal=self.metal,
            olcek=PiyasaUrun.Olcek.KG,
            cikti_pb=PiyasaUrun.CiktiPb.TRY,
            gram=Decimal("1"),
            alis_marj=Decimal("0"),
            satis_marj=Decimal("0"),
            yuvarlama_adimi=Decimal("0"),
            sira=50,
        )
        baz = piyasa_fiyat_servisi.baz_fiyat("has_kg")
        # 6000 * 1000
        self.assertEqual(baz["satis"], Decimal("6000000.00"))
        self.assertEqual(baz["olcek"], "KG")

    def test_baz_fiyat_ons_usd(self):
        from tanimlar.models import DovizKuru

        now = timezone.now()
        DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("34.0000"),
            kaynak="api",
        )
        DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=self.saglayici,
            kur_tipi=KurTipi.ALIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("33.9000"),
            kaynak="api",
        )
        PiyasaUrun.objects.create(
            kod="ons_usd",
            ad="Ons USD",
            grup=PiyasaUrun.Grup.HAS,
            metal=self.metal,
            olcek=PiyasaUrun.Olcek.ONS,
            cikti_pb=PiyasaUrun.CiktiPb.USD,
            gram=Decimal("1"),
            alis_marj=Decimal("0"),
            satis_marj=Decimal("0"),
            yuvarlama_adimi=Decimal("0"),
            sira=51,
        )
        baz = piyasa_fiyat_servisi.baz_fiyat("ons_usd")
        # 6000 * 31.1035 / 34 ≈ 5488.85
        self.assertEqual(baz["cikti_pb"], "USD")
        self.assertEqual(baz["satis"], Decimal("5488.85"))

    def test_pano_ozeti_grup(self):
        rows = piyasa_fiyat_servisi.pano_ozeti()
        self.assertTrue(any(r["kod"] == "has" and r["grup"] == "HAS" for r in rows))

    def test_darphane_listesi(self):
        rows = piyasa_fiyat_servisi.darphane_iscilik_listesi()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["iscilik_tl"], Decimal("40"))

    def test_cozumle_pano(self):
        out = piyasa_fiyat_servisi.cozumle_islem_birim_fiyati(
            kaynak="PANO", taraf="SATIS", urun_kod="has"
        )
        self.assertEqual(out["etkin_birim"], Decimal("6120.00"))

    def test_cozumle_manuel(self):
        out = piyasa_fiyat_servisi.cozumle_islem_birim_fiyati(
            kaynak="MANUEL",
            taraf="SATIS",
            manuel_birim_fiyat=Decimal("7000"),
        )
        self.assertEqual(out["etkin_birim"], Decimal("7000.00"))

    def test_cozumle_pano_katman2(self):
        out = piyasa_fiyat_servisi.cozumle_islem_birim_fiyati(
            kaynak="PANO",
            taraf="SATIS",
            urun_kod="has",
            agirlik_gr=Decimal("1"),
            kullanici_ekleri={"marj": {"tip": "YUZDE", "deger": 1}},
        )
        self.assertEqual(out["etkin_birim"], Decimal("6181.20"))

    def test_manuel_zorunlu(self):
        with self.assertRaises(ValidationError):
            piyasa_fiyat_servisi.cozumle_islem_birim_fiyati(
                kaynak="MANUEL", taraf="SATIS"
            )

    def test_kar_yardimcisi_pano(self):
        out = kar_yardimcisi.simule_pano_urun(
            urun_kod="has",
            taraf="SATIS",
            agirlik_gr=Decimal("10"),
            kar_pct=Decimal("5"),
        )
        self.assertEqual(out["baz_birim"], Decimal("6120.00"))
        self.assertEqual(out["kaynak"], "PANO")
        self.assertGreater(out["net_kar"], 0)

    def test_kar_yardimcisi_metal_ayar(self):
        out = kar_yardimcisi.simule_metal_ayar(
            metal_kod="AU_PANO",
            ayar_kodu="22K",
            taraf="SATIS",
            agirlik_gr=Decimal("1"),
            kar_pct=Decimal("5"),
            iscilik_tl=Decimal("100"),
        )
        self.assertEqual(out["kaynak"], "METAL_AYAR")
        # 6000 * 0.916 = 5496
        self.assertEqual(out["baz_birim"], Decimal("5496.00"))
        self.assertEqual(out["gr_maliyet"], Decimal("5596.00"))

    def test_kar_birimli_tl_kesinti(self):
        out = kar_yardimcisi.simule_pano_urun(
            urun_kod="has",
            taraf="SATIS",
            agirlik_gr=Decimal("1"),
            kar_pct=Decimal("0"),
            banka={"tip": "TL", "deger": Decimal("50")},
            isletme={"tip": "TL", "deger": Decimal("0")},
            gelir_vergisi={"tip": "TL", "deger": Decimal("0")},
            diger={"tip": "TL", "deger": Decimal("0")},
        )
        self.assertEqual(out["banka_kesinti"], Decimal("50.00"))
        self.assertEqual(out["banka_tipi"], "TL")
