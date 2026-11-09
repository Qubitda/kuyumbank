"""F5-012 — PaymentIntent + Order tahsilat; çift tahsilat yok."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import CariHesap, LedgerEntry, PaymentIntent
from finans.services import payment_servisi
from siparis.models import Order
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class PaymentIntentTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def _make_order(self, key="pay-ord"):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_intent_and_capture(self):
        order = self._make_order("pay-1")
        pi = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="pi-1"
        )
        self.assertEqual(pi.durum, PaymentIntent.Durum.BEKLEMEDE)
        self.assertGreater(pi.tutar, Decimal("0"))

        done = payment_servisi.tahsil_et(actor=self.finance, intent=pi)
        self.assertEqual(done.durum, PaymentIntent.Durum.BASARILI)
        self.assertIsNotNone(done.ledger_entry_id)

        # Net cari ≈ 0 (borç + tahsilat)
        hesap = CariHesap.objects.get(
            firma=self.alici, karsi_firma=self.platform, para_birimi=pi.para_birimi
        )
        self.assertEqual(hesap.bakiye, Decimal("0.00"))
        self.assertEqual(
            LedgerEntry.objects.filter(
                referans_tip="Order", referans_id=str(order.pk)
            ).count(),
            1,
        )

    def test_idempotent_intent_and_capture(self):
        order = self._make_order("pay-idem")
        a = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="pi-idem"
        )
        b = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="pi-idem"
        )
        self.assertEqual(a.pk, b.pk)
        c1 = payment_servisi.tahsil_et(actor=self.finance, intent=a)
        c2 = payment_servisi.tahsil_et(actor=self.finance, intent=a)
        self.assertEqual(c1.pk, c2.pk)
        self.assertEqual(
            PaymentIntent.objects.filter(
                order=order, durum=PaymentIntent.Durum.BASARILI
            ).count(),
            1,
        )

    def test_second_intent_after_capture_rejected(self):
        order = self._make_order("pay-dup")
        pi = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="pi-dup-1"
        )
        payment_servisi.tahsil_et(actor=self.finance, intent=pi)
        with self.assertRaises(ValidationError):
            payment_servisi.olustur_intent(
                actor=self.buyer, order=order, idempotency_key="pi-dup-2"
            )

    def test_buyer_cannot_capture(self):
        order = self._make_order("pay-deny")
        pi = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="pi-deny"
        )
        with self.assertRaises(PermissionDenied):
            payment_servisi.tahsil_et(actor=self.buyer, intent=pi)

    def test_cancelled_order_no_intent(self):
        order = self._make_order("pay-iptal")
        from siparis.services import order_servisi as osvc

        osvc.iptal_siparis(actor=self.buyer, order=order)
        order.refresh_from_db()
        self.assertEqual(order.durum, Order.Durum.IPTAL)
        with self.assertRaises(ValidationError):
            payment_servisi.olustur_intent(
                actor=self.buyer, order=order, idempotency_key="pi-iptal"
            )
