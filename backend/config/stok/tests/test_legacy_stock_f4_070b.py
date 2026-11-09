"""F4-070b — Legacy Varyant.stok / Teklif.stok_adet kolonları kaldırıldı."""

from decimal import Decimal

from django.test import TestCase

from fiyatlama.models import TedarikciTeklif
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from urunler.models import Varyant


class LegacyStockDroppedTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_fields_absent_from_models(self):
        self.assertNotIn("stok", {f.name for f in Varyant._meta.get_fields()})
        self.assertNotIn(
            "stok_adet", {f.name for f in TedarikciTeklif._meta.get_fields()}
        )

    def test_dual_stock_helper_removed(self):
        import importlib.util

        spec = importlib.util.find_spec("stok.services.dual_stock_envanter")
        self.assertIsNone(spec)

    def test_varyant_other_fields_still_writable(self):
        v = Varyant.objects.get(pk=self.varyant.pk)
        v.ek_bedel = Decimal("12.00")
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.ek_bedel, Decimal("12.00"))

    def test_teklif_version_copy_without_stok_adet(self):
        from fiyatlama.services import teklif_servisi

        yeni = teklif_servisi.yeni_versiyon_olustur(self.teklif, self.ted_user)
        self.assertIsNotNone(yeni.pk)
        self.assertNotEqual(yeni.pk, self.teklif.pk)
        self.assertNotIn(
            "stok_adet", {f.name for f in type(yeni)._meta.get_fields()}
        )
