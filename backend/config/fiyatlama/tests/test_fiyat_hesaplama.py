from decimal import Decimal

from django.test import SimpleTestCase

from fiyatlama.services.fiyat_hesaplama import hesapla


class FiyatHesaplamaTest(SimpleTestCase):
    """
    v3 §5.6 Excel doğrulama örneği:
      Ürün: 8,41 gr, 24K (milyem 0,995), saf altın 6.250 TL/gr
      İşçilik 250 TL, servis 1.500 TL
      PARA (TRY) toplam: 54.049,69 TL
    """

    def test_v3_ornek_toplam_try(self):
        sonuc = hesapla(
            gram=Decimal("8.41"),
            milyem=Decimal("0.995"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("1500"),
            iscilik=Decimal("250"),
        )
        self.assertEqual(sonuc["metal_bedeli"], Decimal("52299.68750"))
        self.assertEqual(sonuc["toplam_yuvarlanmis"], Decimal("54049.69"))

    def test_yuzde_ham_metal_taban(self):
        """
        v3 §5.6: YUZDE satırı, ham metalin ~%0.5'i işçilik, ~%2.9'u servis
        diyor. Aynı toplamı verecek marj değerini üretiyoruz.
        """
        # İşçilik için marj değeri = 250 / 52299.69 * 100 ≈ 0.4780%
        iscilik_yuzde = Decimal("250") / Decimal("52299.69") * Decimal("100")
        servis_yuzde = Decimal("1500") / Decimal("52299.69") * Decimal("100")

        iscilik_m = hesapla(
            gram=Decimal("8.41"),
            milyem=Decimal("0.995"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="YUZDE",
            marj_degeri=iscilik_yuzde,
            islcilik_dahil_mi=False,
        )
        # ~250 TL
        self.assertAlmostEqual(
            float(iscilik_m["marj"]), 250.00, delta=0.05
        )

        servis_m = hesapla(
            gram=Decimal("8.41"),
            milyem=Decimal("0.995"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="YUZDE",
            marj_degeri=servis_yuzde,
            islcilik_dahil_mi=False,
        )
        self.assertAlmostEqual(
            float(servis_m["marj"]), 1500.00, delta=0.05
        )

    def test_tl_gr_marj(self):
        sonuc = hesapla(
            gram=Decimal("8.41"),
            milyem=Decimal("0.995"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="TL_GR",
            marj_degeri=Decimal("100"),
        )
        # metal + 8.41 * 100
        self.assertAlmostEqual(
            float(sonuc["toplam"]),
            float(Decimal("52299.68750") + Decimal("841.00")),
            places=4,
        )

    def test_14k_ornek(self):
        # v3 §5.6 ek örnek: 10 gr, 14K (0.585), altın 6.250 → ham 36.562,50
        sonuc = hesapla(
            gram=Decimal("10"),
            milyem=Decimal("0.585"),
            saf_birim_fiyat=Decimal("6250"),
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("0"),
        )
        self.assertEqual(sonuc["metal_bedeli_yuvarlanmis"], Decimal("36562.50"))