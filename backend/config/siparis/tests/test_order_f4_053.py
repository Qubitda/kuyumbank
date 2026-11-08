"""F4-053 — Sipariş iptal + stok IADE (finans yok)."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase

from firmalar.models import AuditOlay
from siparis.models import Order
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance, StockMovement


class OrderCancelTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def _order(self, key="cancel-1", miktar=Decimal("2")):
        self._quote_and_cart(miktar=miktar)
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=key
        )
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_cancel_restores_on_hand_and_available(self):
        order = self._order()
        bal_before = StockBalance.objects.get(
            warehouse=self.wh, teklif=self.teklif
        )
        self.assertEqual(bal_before.on_hand, Decimal("98"))
        self.assertEqual(bal_before.available, Decimal("98"))

        cancelled = order_servisi.iptal_siparis(
            actor=self.buyer, order=order
        )
        self.assertEqual(cancelled.durum, Order.Durum.IPTAL)

        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("100"))
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertEqual(bal.available, Decimal("100"))
        self.assertTrue(
            StockMovement.objects.filter(
                tip=StockMovement.Tip.IADE,
                miktar=Decimal("2"),
                neden__startswith=f"order_cancel:{order.pk}:",
            ).exists()
        )

    def test_cancel_idempotent(self):
        order = self._order(key="cancel-idem")
        a = order_servisi.iptal_siparis(actor=self.buyer, order=order)
        b = order_servisi.iptal_siparis(actor=self.buyer, order=a)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(b.durum, Order.Durum.IPTAL)
        self.assertEqual(
            StockMovement.objects.filter(tip=StockMovement.Tip.IADE).count(),
            1,
        )
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("100"))

    def test_other_firma_cannot_cancel(self):
        order = self._order(key="cancel-tenant")
        with self.assertRaises(PermissionDenied):
            order_servisi.iptal_siparis(actor=self.ted_user, order=order)
        order.refresh_from_db()
        self.assertEqual(order.durum, Order.Durum.OLUSTURULDU)


class OrderCancelFailAuditTests(CheckoutFixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_checkout_world()

    def test_cancel_fail_audit_survives(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="cancel-fail-aud"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        before = AuditOlay.objects.filter(
            action="order.cancel", success=False
        ).count()
        with self.assertRaises(PermissionDenied):
            order_servisi.iptal_siparis(actor=self.ted_user, order=order)
        after = AuditOlay.objects.filter(
            action="order.cancel", success=False
        ).count()
        self.assertGreater(after, before)
