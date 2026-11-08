"""Dilim 3.4 — üç fiyat modeli (saf Python; SimpleTestCase)."""

from decimal import Decimal

from django.test import SimpleTestCase

from fiyatlama.services.fiyat_hesaplama import (
    hesapla,
    hesapla_gram_birim,
    hesapla_metal_bazli,
    hesapla_modele_gore,
    hesapla_sabit_parca,
)


class UcModelHesaplamaTests(SimpleTestCase):
    def test_metal_geriye_donuk_v3_ornek(self):
        sonuc = hesapla(
            gram=Decimal("8.41"),
            milyem=Decimal("0.995"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("1500"),
            iscilik=Decimal("250"),
        )
        self.assertEqual(sonuc["toplam_yuvarlanmis"], Decimal("54049.69"))

    def test_metal_bazli_ek_bedel_ve_kalemler(self):
        sonuc = hesapla_metal_bazli(
            gram=Decimal("10"),
            milyem=Decimal("0.585"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("100"),
            iscilik=Decimal("50"),
            tas_bedeli=Decimal("25"),
            ek_bedel=Decimal("10"),
            para_birimi="TRY",
        )
        self.assertEqual(sonuc["fiyat_modeli"], "METAL_BAZLI")
        self.assertEqual(sonuc["kalemler"]["metal"], Decimal("36562.50"))
        self.assertEqual(sonuc["kalemler"]["ek_bedel"], Decimal("10"))
        self.assertNotIn("platform_servis", sonuc["kalemler"])
        expected = (
            Decimal("36562.50")
            + Decimal("50")
            + Decimal("100")
            + Decimal("25")
            + Decimal("10")
        )
        self.assertEqual(sonuc["toplam_vergisiz"], expected.quantize(Decimal("0.01")))

    def test_metal_gecersiz_milyem(self):
        with self.assertRaises(ValueError):
            hesapla_metal_bazli(
                gram=Decimal("1"),
                milyem=Decimal("1.5"),
                saf_birim_fiyat=Decimal("100"),
                marj_tipi="TL_PARCA",
                marj_degeri=Decimal("0"),
            )

    def test_metal_eksik_fiyat(self):
        with self.assertRaises(ValueError):
            hesapla_metal_bazli(
                gram=Decimal("1"),
                milyem=Decimal("0.585"),
                saf_birim_fiyat=Decimal("0"),
                marj_tipi="TL_PARCA",
                marj_degeri=Decimal("0"),
            )

    def test_gram_birim_temel(self):
        sonuc = hesapla_gram_birim(
            gram=Decimal("8.41"),
            birim_fiyat=Decimal("100"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("50"),
            tas_bedeli=Decimal("10"),
            ek_bedel=Decimal("5"),
        )
        self.assertEqual(sonuc["fiyat_modeli"], "GRAM_BIRIM")
        self.assertNotIn("metal", sonuc["kalemler"])
        self.assertEqual(sonuc["kalemler"]["gram_birim"], Decimal("841.00"))
        self.assertEqual(
            sonuc["toplam_vergisiz"],
            Decimal("841.00") + Decimal("50") + Decimal("10") + Decimal("5"),
        )

    def test_gram_birim_yuzde_marj(self):
        sonuc = hesapla_gram_birim(
            gram=Decimal("10"),
            birim_fiyat=Decimal("200"),
            marj_tipi="YUZDE",
            marj_degeri=Decimal("10"),
        )
        # taban 2000, marj %10 = 200
        self.assertEqual(sonuc["kalemler"]["kanal_marj"], Decimal("200"))
        self.assertEqual(sonuc["toplam_vergisiz"], Decimal("2200.00"))

    def test_gram_birim_sifir_gram(self):
        with self.assertRaises(ValueError):
            hesapla_gram_birim(
                gram=Decimal("0"),
                birim_fiyat=Decimal("100"),
                marj_tipi="TL_PARCA",
                marj_degeri=Decimal("0"),
            )

    def test_sabit_parca_gramdan_bagimsiz(self):
        a = hesapla_sabit_parca(
            birim_fiyat=Decimal("5000"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("100"),
            gram=Decimal("1"),
            ek_bedel=Decimal("20"),
        )
        b = hesapla_sabit_parca(
            birim_fiyat=Decimal("5000"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("100"),
            gram=Decimal("99"),
            ek_bedel=Decimal("20"),
        )
        self.assertEqual(a["kalemler"]["sabit_parca"], Decimal("5000"))
        self.assertEqual(a["toplam_vergisiz"], b["toplam_vergisiz"])
        self.assertNotIn("metal", a["kalemler"])

    def test_sabit_parca_tl_gr_marj_gram_zorunlu(self):
        with self.assertRaises(ValueError):
            hesapla_sabit_parca(
                birim_fiyat=Decimal("100"),
                marj_tipi="TL_GR",
                marj_degeri=Decimal("10"),
                gram=None,
            )

    def test_modele_gore_dispatcher(self):
        m = hesapla_modele_gore(
            "METAL_BAZLI",
            gram=Decimal("1"),
            milyem=Decimal("1"),
            saf_birim_fiyat=Decimal("10"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("0"),
        )
        self.assertEqual(m["fiyat_modeli"], "METAL_BAZLI")
        with self.assertRaises(ValueError):
            hesapla_modele_gore("BILINMEYEN", marj_tipi="TL_PARCA", marj_degeri=0)

    def test_half_up_rounding(self):
        # 1 * 0.585 * 1000.005 → metal ham; toplam quantize HALF_UP
        sonuc = hesapla_metal_bazli(
            gram=Decimal("1"),
            milyem=Decimal("0.585"),
            saf_birim_fiyat=Decimal("1000.005"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("0"),
        )
        self.assertEqual(
            sonuc["toplam_vergisiz"],
            (Decimal("1") * Decimal("0.585") * Decimal("1000.005")).quantize(
                Decimal("0.01")
            ),
        )
