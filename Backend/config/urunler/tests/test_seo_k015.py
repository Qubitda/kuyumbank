"""K-015 — SEO marka parametresi; Örnek Kuyumculuk yok."""

from django.test import TestCase, override_settings

from tanimlar.models import FiyatGrubu
from urunler.models import Kategori
from urunler.tests._base import KatalogTestTaban


class SeoBrandTests(KatalogTestTaban):
    @override_settings(PLATFORM_BRAND_NAME="Kuyumbank")
    def test_urun_meta_baslik_uses_brand(self):
        u = self.urun(meta_baslik="", meta_aciklama="")
        u.refresh_from_db()
        self.assertIn("Kuyumbank", u.meta_baslik)
        self.assertNotIn("Örnek Kuyumculuk", u.meta_baslik)

    @override_settings(PLATFORM_BRAND_NAME="")
    def test_urun_meta_baslik_without_brand_is_ad_only(self):
        u = self.urun(ad="Alyans Test", meta_baslik="", meta_aciklama="")
        u.refresh_from_db()
        self.assertEqual(u.meta_baslik, "Alyans Test")
        self.assertEqual(u.meta_aciklama, "")

    @override_settings(PLATFORM_BRAND_NAME="Kuyumbank")
    def test_kategori_seo_no_ornek_marka(self):
        grup = FiyatGrubu.objects.create(kod="SEO_G", ad="SEO G")
        k = Kategori.objects.create(kod="SEO_K", ad="Kolye", fiyat_grubu=grup)
        self.assertIn("Kuyumbank", k.seo_baslik)
        self.assertNotIn("Örnek Kuyumculuk", k.seo_baslik or "")
        self.assertNotIn("En şık ve kaliteli", k.seo_aciklama or "")
