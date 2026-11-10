"""F11-014 ciro eşik anomali; platform audit + tedarikçi 403."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import anomali_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class AnomaliF11014Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)
        sync_user_role_groups(cls.ted_user)
        sync_user_role_groups(cls.buyer)

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_esik_asimi_uyari_ve_audit(self):
        self._order("ano-1")
        out = anomali_servisi.ciro_esik_tara(
            actor=self.finance, esik_ciro=Decimal("1.00")
        )
        self.assertGreaterEqual(out["uyari_adet"], 1)
        self.assertTrue(out["uyarilar"][0]["anomali"])
        self.assertEqual(out["uyarilar"][0]["alici_firma_id"], self.alici.pk)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="siparis.anomali.ciro_esik", success=True
            ).exists()
        )
        blob = str(out).lower()
        self.assertNotIn("tedarikci", blob)
        self.assertNotIn("maliyet", blob)

    def test_esik_alti_bos(self):
        self._order("ano-2")
        out = anomali_servisi.ciro_esik_tara(
            actor=self.finance, esik_ciro=Decimal("999999999.00")
        )
        self.assertEqual(out["uyari_adet"], 0)

    def test_supplier_denied(self):
        with self.assertRaises(PermissionDenied):
            anomali_servisi.ciro_esik_tara(
                actor=self.ted_user, esik_ciro=Decimal("1.00")
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="siparis.anomali.denied", success=False
            ).exists()
        )
