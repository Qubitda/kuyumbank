"""F11-013 — Sipariş/QC (ve iade onay) outbox bildirim olayları."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from firmalar import roles
from firmalar.models import OutboxMessage
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class NotifyF11013Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        cls.qc = User(
            username="f11_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_order_created_outbox(self):
        order = self._order("f11-ord")
        self.assertTrue(
            OutboxMessage.objects.filter(
                event_type="order.created",
                payload__order_id=order.pk,
            ).exists()
        )

    def test_qc_pass_outbox(self):
        order = self._order("f11-pass")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=order.lines.get(),
            olculen=order.lines.get().miktar,
        )
        insp = inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        msg = OutboxMessage.objects.get(event_type="qc.passed")
        self.assertEqual(msg.payload.get("inspection_id"), insp.pk)
        self.assertEqual(msg.payload.get("order_id"), order.pk)
        self.assertEqual(msg.durum, OutboxMessage.Durum.PENDING)

    def test_qc_fail_outbox(self):
        order = self._order("f11-fail")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        inspection_servisi.fail_et(
            actor=self.qc, inspection=insp, reason="sapma"
        )
        msg = OutboxMessage.objects.get(event_type="qc.failed")
        self.assertEqual(msg.payload.get("inspection_id"), insp.pk)
        self.assertEqual(msg.payload.get("reason"), "sapma")
