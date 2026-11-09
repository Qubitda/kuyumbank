"""F6-010 — QualityInspection SM + shipment_blok + manage_qc."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.models import QualityInspection
from kalite.services import inspection_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class InspectionF6010Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="qc_user",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

    def _order(self, key="qc-ord"):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_happy_path_pass_clears_block(self):
        order = self._order("qc-pass")
        self.assertTrue(inspection_servisi.order_shipment_blocked(order))

        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        self.assertEqual(insp.durum, QualityInspection.Durum.TASLAK)
        self.assertFalse(insp.shipment_blok)
        self.assertTrue(inspection_servisi.order_shipment_blocked(order))

        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        self.assertEqual(insp.durum, QualityInspection.Durum.OLCUMDE)

        insp = inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        self.assertEqual(insp.durum, QualityInspection.Durum.PASS)
        self.assertFalse(insp.shipment_blok)
        self.assertFalse(inspection_servisi.order_shipment_blocked(order))

        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.pass", entity_id=str(insp.pk), success=True
            ).exists()
        )

    def test_fail_sets_shipment_blok(self):
        order = self._order("qc-fail")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        insp = inspection_servisi.fail_et(
            actor=self.qc, inspection=insp, reason="gram sapma"
        )
        self.assertEqual(insp.durum, QualityInspection.Durum.FAIL)
        self.assertTrue(insp.shipment_blok)
        self.assertTrue(inspection_servisi.order_shipment_blocked(order))

    def test_illegal_transition(self):
        order = self._order("qc-bad")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        with self.assertRaises(ValidationError):
            inspection_servisi.pass_et(actor=self.qc, inspection=insp)

    def test_buyer_denied(self):
        order = self._order("qc-deny")
        with self.assertRaises(PermissionDenied):
            inspection_servisi.olustur(actor=self.buyer, order=order)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.create_denied",
                success=False,
                reason="yetki_yok",
            ).exists()
        )

    def test_direct_save_blocked(self):
        order = self._order("qc-imm")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        with self.assertRaises(ValidationError):
            insp.notlar = "hack"
            insp.save()
