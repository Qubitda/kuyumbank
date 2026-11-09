"""F6-022 — POD kaydı + opsiyonel teslim zorunluluğu."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.models import ProofOfDelivery, Shipment
from lojistik.services import pod_servisi, shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class PodF6022Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="pod_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="pod_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def _yolda(self, key):
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
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        return shipment_servisi.sevk_et(
            actor=self.log, shipment=ship, takip_no="POD-TRK"
        )

    def test_pod_then_teslim(self):
        ship = self._yolda("pod-ok")
        pod = pod_servisi.kaydet_pod(
            actor=self.log,
            shipment=ship,
            teslim_alan="Ahmet Yilmaz",
        )
        self.assertEqual(pod.teslim_alan, "Ahmet Yilmaz")
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.TESLIM)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.pod.created", entity_id=str(pod.pk)
            ).exists()
        )

    def test_teslim_without_pod_when_optional(self):
        ship = self._yolda("pod-opt")
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.TESLIM)
        self.assertEqual(ProofOfDelivery.objects.count(), 0)

    @override_settings(SHIPMENT_POD_REQUIRED=True)
    def test_teslim_requires_pod_when_configured(self):
        ship = self._yolda("pod-req")
        with self.assertRaises(ValidationError):
            shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        pod_servisi.kaydet_pod(
            actor=self.log, shipment=ship, teslim_alan="Imza Sahibi"
        )
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        self.assertEqual(ship.durum, Shipment.Durum.TESLIM)

    def test_pod_immutable(self):
        ship = self._yolda("pod-imm")
        pod = pod_servisi.kaydet_pod(
            actor=self.log, shipment=ship, teslim_alan="Ali Veli"
        )
        with self.assertRaises(ValidationError):
            pod.teslim_alan = "hack"
            pod.save()
