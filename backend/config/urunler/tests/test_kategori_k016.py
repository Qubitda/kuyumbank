"""K-016 — kategori alt ağaç derinliği + taşıma servisi."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from tanimlar.models import FiyatGrubu
from urunler.models import Kategori
from urunler.services.kategori_servisi import kategori_tasi


class KategoriTasimaTests(TestCase):
    def setUp(self):
        self.grup = FiyatGrubu.objects.create(kod="KT_G", ad="Kat G")
        self.kok = Kategori.objects.create(kod="KOK", ad="Kök", fiyat_grubu=self.grup)
        self.alt = Kategori.objects.create(kod="ALT", ad="Alt", ust=self.kok)
        self.yaprak = Kategori.objects.create(kod="YAP", ad="Yaprak", ust=self.alt)

    def test_alt_agac_yuksekligi(self):
        self.assertEqual(self.kok.alt_agac_yuksekligi(), 3)
        self.assertEqual(self.yaprak.alt_agac_yuksekligi(), 1)

    def test_tasi_subtree_depth_blocked(self):
        """Derin alt ağacı daha derine taşımak MAKS_DERINLIK'i aşar."""
        baska_kok = Kategori.objects.create(
            kod="KOK2", ad="Kök2", fiyat_grubu=self.grup
        )
        orta = Kategori.objects.create(kod="ORT", ad="Orta", ust=baska_kok)
        # kok(1)-alt(2)-yaprak(3) ağacını orta(2) altına taşımak → max derinlik 4
        with self.assertRaises(ValidationError):
            kategori_tasi(self.kok, orta)

    def test_tasi_allowed_under_root(self):
        baska = Kategori.objects.create(kod="BASKA", ad="Başka", fiyat_grubu=self.grup)
        # tek düğüm taşıma kök altına OK
        sonuc = kategori_tasi(baska, self.kok)
        self.assertEqual(sonuc.ust_id, self.kok.pk)
        self.assertEqual(sonuc.derinlik(), 2)
