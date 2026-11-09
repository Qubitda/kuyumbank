"""F10-020 — RFQ SM + kör mesaj."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class RfqF10020Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        # buyer zaten ALICI_SATINALMACI → manage_rfq
        sync_user_role_groups(cls.buyer)

    def test_rfq_create_gonder_mesaj(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Altın yüzük RFQ",
            line_specs=[
                {"aciklama": "14 ayar", "miktar": Decimal("10"), "birim": "ADET"}
            ],
        )
        self.assertEqual(rfq.durum, RFQ.Durum.TASLAK)
        self.assertEqual(rfq.lines.count(), 1)
        rfq = rfq_servisi.gonder(actor=self.buyer, rfq=rfq)
        self.assertEqual(rfq.durum, RFQ.Durum.GONDERILDI)
        msg = rfq_servisi.mesaj_ekle(
            actor=self.buyer, rfq=rfq, govde="Platform üzerinden soru"
        )
        self.assertEqual(msg.gonderen_rol, roles.ALICI_SATINALMACI)
        self.assertNotIn("tedarikci", msg.govde.lower())

    def test_supplier_cannot_create_rfq(self):
        with self.assertRaises((PermissionDenied, ValidationError)):
            rfq_servisi.olustur(
                actor=self.ted_user,
                baslik="x",
                line_specs=[{"aciklama": "a", "miktar": Decimal("1")}],
            )
