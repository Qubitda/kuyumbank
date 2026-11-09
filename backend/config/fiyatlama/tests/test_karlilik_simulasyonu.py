"""Excel A/B P&L simülatörü — quote/ticari gerçeğe bağlı değil."""

from decimal import Decimal

from django.test import SimpleTestCase

from fiyatlama.services import karlilik_simulasyonu as ks


class KarlilikSimulasyonuTests(SimpleTestCase):
    def test_a_marj_pct_matches_sheet(self):
        s = ks.simule_marj_pct(
            maden_fiyati=Decimal("3800"),
            iscilik_tl=Decimal("850"),
            agirlik_gr=Decimal("22.41"),
            kar_pct=Decimal("5"),
        )
        self.assertEqual(s.gr_maliyet, Decimal("4650.00"))
        self.assertEqual(s.kar_gr, Decimal("232.50"))
        self.assertEqual(s.gr_satis, Decimal("4882.50"))
        self.assertEqual(s.toplam_satis, Decimal("109416.83"))
        self.assertEqual(s.brut_kar, Decimal("5210.33"))
        self.assertEqual(s.banka_kesinti, Decimal("2188.34"))
        self.assertEqual(s.isletme_gideri, Decimal("1094.17"))
        self.assertEqual(s.gelir_vergisi, Decimal("385.56"))
        self.assertEqual(s.net_kar, Decimal("1542.26"))
        self.assertEqual(s.mod, "MARJ_PCT")

    def test_b_hedef_toplam_matches_sheet(self):
        s = ks.simule_hedef_toplam(
            maden_fiyati=Decimal("3800"),
            iscilik_tl=Decimal("850"),
            agirlik_gr=Decimal("22.41"),
            hedef_toplam=Decimal("120000"),
        )
        self.assertEqual(s.gr_maliyet, Decimal("4650.00"))
        self.assertEqual(s.gr_satis, Decimal("5354.75"))
        self.assertEqual(s.kar_gr, Decimal("704.75"))
        self.assertEqual(s.toplam_satis, Decimal("120000.00"))
        self.assertEqual(s.brut_kar, Decimal("15793.50"))
        self.assertEqual(s.banka_kesinti, Decimal("2400.00"))
        self.assertEqual(s.isletme_gideri, Decimal("1200.00"))
        self.assertEqual(s.gelir_vergisi, Decimal("2438.70"))
        self.assertEqual(s.net_kar, Decimal("9754.80"))
        self.assertEqual(s.mod, "HEDEF_TOPLAM")
