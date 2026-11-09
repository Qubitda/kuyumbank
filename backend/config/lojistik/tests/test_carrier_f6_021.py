"""F6-021 — CarrierPort + fake adapter; fail-closed + sevk entegrasyonu."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.carriers import LabelRequest, get_carrier_adapter
from lojistik.carriers.fake import FakeCarrierAdapter
from lojistik.models import Shipment
from lojistik.services import shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class CarrierAdapterUnitTests(TestCase):
    def test_fake_label_ok(self):
        res = FakeCarrierAdapter().create_label(
            LabelRequest(shipment_id=1, order_id=2, idempotency_key="k1")
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.tracking_no, "FAKE-k1")

    def test_fake_force_fail(self):
        res = FakeCarrierAdapter(force_fail=True).create_label(
            LabelRequest(shipment_id=1, order_id=2, idempotency_key="k2")
        )
        self.assertFalse(res.ok)

    @override_settings(CARRIER_PROVIDER="unknown_shipper")
    def test_unknown_provider_fail_closed(self):
        with self.assertRaises(ValidationError):
            get_carrier_adapter()


class CarrierSevkIntegrationTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="car_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="car_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def _ship_hazir(self, key):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        return shipment_servisi.hazirla(actor=self.log, shipment=ship)

    def test_sevk_auto_fake_tracking(self):
        ship = self._ship_hazir("car-auto")
        ship = shipment_servisi.sevk_et(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.YOLDA)
        self.assertTrue(ship.takip_no.startswith("FAKE-ship-"))

    @override_settings(CARRIER_FAKE_FORCE_FAIL=True)
    def test_sevk_carrier_fail_closed(self):
        ship = self._ship_hazir("car-fail")
        with self.assertRaises(ValidationError):
            shipment_servisi.sevk_et(actor=self.log, shipment=ship)
        ship.refresh_from_db()
        self.assertEqual(ship.durum, Shipment.Durum.HAZIR)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.shipment.sevk_denied",
                success=False,
                reason="carrier_fail",
            ).exists()
        )
