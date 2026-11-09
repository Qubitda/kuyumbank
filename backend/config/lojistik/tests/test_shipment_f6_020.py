"""F6-020 — Shipment SM + QC gate (PASS zorunlu; FAIL/blok → ValidationError)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.models import Shipment
from lojistik.services import shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class ShipmentF6020Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="ship_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

        cls.log = User(
            username="ship_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def _order(self, key):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _qc_pass(self, order):
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        return inspection_servisi.pass_et(actor=self.qc, inspection=insp)

    def test_create_blocked_without_qc(self):
        order = self._order("ship-noqc")
        with self.assertRaises(ValidationError):
            shipment_servisi.olustur(actor=self.log, order=order)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.shipment.create_denied",
                success=False,
                reason="qc_gate",
            ).exists()
        )

    def test_create_blocked_on_qc_fail(self):
        order = self._order("ship-fail")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=Decimal("9.999"),
        )
        with self.assertRaises(ValidationError):
            shipment_servisi.olustur(actor=self.log, order=order)

    def test_happy_path_after_pass(self):
        order = self._order("ship-ok")
        self._qc_pass(order)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        self.assertEqual(ship.durum, Shipment.Durum.TASLAK)
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.HAZIR)
        ship = shipment_servisi.sevk_et(
            actor=self.log, shipment=ship, takip_no="TRK-1"
        )
        self.assertEqual(ship.durum, Shipment.Durum.YOLDA)
        self.assertEqual(ship.takip_no, "TRK-1")
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.TESLIM)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.shipment.teslim",
                entity_id=str(ship.pk),
                success=True,
            ).exists()
        )

    def test_buyer_denied(self):
        order = self._order("ship-deny")
        self._qc_pass(order)
        with self.assertRaises(PermissionDenied):
            shipment_servisi.olustur(actor=self.buyer, order=order)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.shipment.create_denied",
                success=False,
                reason="yetki_yok",
            ).exists()
        )

    def test_illegal_transition(self):
        order = self._order("ship-bad")
        self._qc_pass(order)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        with self.assertRaises(ValidationError):
            shipment_servisi.teslim_et(actor=self.log, shipment=ship)

    def test_direct_save_blocked(self):
        order = self._order("ship-imm")
        self._qc_pass(order)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        with self.assertRaises(ValidationError):
            ship.notlar = "hack"
            ship.save()
