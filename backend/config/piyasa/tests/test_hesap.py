"""Saf hesap — GoldXT pano marjı."""

from decimal import Decimal

from django.test import SimpleTestCase

from piyasa.services import hesap


class HesapTests(SimpleTestCase):
    def test_yuvarla_onluk(self):
        self.assertEqual(
            hesap.yuvarla(Decimal("6665"), 10, hesap.YAKIN), Decimal("6670")
        )

    def test_satis_yuzde_marj(self):
        # GoldXT: ask = base * (1 + ask_margin/100)
        out = hesap.hesapla_taraf(
            taraf=hesap.SATIS,
            saf_birim_fiyat=6000,
            milyem=1,
            gram=1,
            marj_modu=hesap.YUZDE,
            satis_marj=2,
        )
        self.assertEqual(out["ham"], Decimal("6000.00"))
        self.assertEqual(out["nihai"], Decimal("6120.00"))

    def test_alis_yuzde_marj(self):
        # GoldXT: bid = base * (1 - bid_margin/100)
        out = hesap.hesapla_taraf(
            taraf=hesap.ALIS,
            saf_birim_fiyat=6000,
            milyem=1,
            gram=1,
            marj_modu=hesap.YUZDE,
            alis_marj=5,
        )
        self.assertEqual(out["nihai"], Decimal("5700.00"))

    def test_tl_marj(self):
        out = hesap.uygula_pano_marj(
            1000, taraf=hesap.ALIS, marj_modu=hesap.TL, alis_marj=25
        )
        self.assertEqual(out, Decimal("975"))
        out2 = hesap.uygula_pano_marj(
            1000, taraf=hesap.SATIS, marj_modu=hesap.TL, satis_marj=25
        )
        self.assertEqual(out2, Decimal("1025"))

    def test_kullanici_fiyati_katman2(self):
        out = hesap.kullanici_fiyati(
            baz_birim_fiyat=6540,
            agirlik_gr=10,
            marj={"tip": hesap.YUZDE, "deger": 1},
        )
        self.assertEqual(out["metal_bedeli"], Decimal("65400.00"))
        self.assertEqual(out["birim_toplam"], Decimal("6605.40"))

    def test_ham_kg_try(self):
        ham = hesap.hesapla_ham(
            saf_birim_fiyat=6000, milyem=1, miktar=1, olcek=hesap.KG, cikti_pb=hesap.TRY
        )
        self.assertEqual(ham, Decimal("6000000"))

    def test_ham_ons_usd(self):
        # saf 100 TRY/gr → oz TRY = 100 * 31.1035; /34 USDTRY
        ham = hesap.hesapla_ham(
            saf_birim_fiyat=100,
            milyem=1,
            miktar=1,
            olcek=hesap.ONS,
            cikti_pb=hesap.USD,
            usd_try=Decimal("34"),
        )
        self.assertEqual(ham.quantize(Decimal("0.01")), Decimal("91.48"))
