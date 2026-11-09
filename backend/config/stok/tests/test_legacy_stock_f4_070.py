"""F4-070 — Legacy Varyant.stok / Teklif.stok_adet yazma kapalı."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from fiyatlama.models import TedarikciTeklif
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.services import dual_stock_envanter
from urunler.models import Varyant


class LegacyStockWriteLockTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        cls.varyant.refresh_from_db()

    def test_inventory_marks_writes_closed(self):
        self.assertTrue(dual_stock_envanter.legacy_writes_closed())
        inv = dual_stock_envanter.legacy_stock_inventory()
        self.assertTrue(all(r.get("writes_closed") for r in inv))

    def test_varyant_stok_update_rejected(self):
        v = Varyant.objects.get(pk=self.varyant.pk)
        original = v.stok
        v.stok = original + 5
        with self.assertRaises(ValidationError) as ctx:
            v.save()
        self.assertIn("stok", ctx.exception.message_dict)
        v.refresh_from_db()
        self.assertEqual(v.stok, original)

    def test_teklif_stok_adet_update_rejected(self):
        t = TedarikciTeklif.objects.get(pk=self.teklif.pk)
        original = t.stok_adet
        t.stok_adet = original + 3
        with self.assertRaises(ValidationError) as ctx:
            t.save()
        self.assertIn("stok_adet", ctx.exception.message_dict)
        t.refresh_from_db()
        self.assertEqual(t.stok_adet, original)

    def test_other_field_update_still_ok(self):
        v = Varyant.objects.get(pk=self.varyant.pk)
        v.ek_bedel = Decimal("12.00")
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.ek_bedel, Decimal("12.00"))
