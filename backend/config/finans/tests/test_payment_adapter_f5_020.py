"""F5-020 — PaymentProviderPort + fake adapter; fail-closed."""

from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import PaymentIntent
from finans.payments import ChargeRequest, get_payment_adapter
from finans.payments.fake import FakePaymentAdapter
from finans.services import payment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class PaymentAdapterTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def _intent(self, key="adp"):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=f"{key}-co"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        return payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key=f"{key}-pi"
        )

    def test_fake_charge_ok(self):
        adapter = FakePaymentAdapter()
        res = adapter.charge(
            ChargeRequest(
                intent_id=1,
                order_id=2,
                amount=Decimal("10.00"),
                currency="TRY",
                idempotency_key="k1",
            )
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.provider_ref, "fake-k1")

    def test_fake_force_fail(self):
        adapter = FakePaymentAdapter(force_fail=True)
        res = adapter.charge(
            ChargeRequest(
                intent_id=1,
                order_id=2,
                amount=Decimal("10.00"),
                currency="TRY",
                idempotency_key="k2",
            )
        )
        self.assertFalse(res.ok)

    @override_settings(PAYMENT_PROVIDER="unknown_bank")
    def test_unknown_provider_fail_closed(self):
        with self.assertRaises(ValidationError):
            get_payment_adapter()

    def test_capture_uses_fake_and_records_provider_ref(self):
        pi = self._intent("ok")
        done = payment_servisi.tahsil_et(actor=self.finance, intent=pi)
        self.assertEqual(done.durum, PaymentIntent.Durum.BASARILI)
        row = AuditOlay.objects.get(
            action="finans.payment.captured", entity_id=str(pi.pk)
        )
        self.assertIn("provider_ref", row.detail)
        self.assertTrue(str(row.detail["provider_ref"]).startswith("fake-"))

    def test_provider_reject_blocks_capture(self):
        pi = self._intent("fail")
        with mock.patch(
            "finans.payments.get_payment_adapter",
            return_value=FakePaymentAdapter(force_fail=True),
        ):
            with self.assertRaises(ValidationError):
                payment_servisi.tahsil_et(actor=self.finance, intent=pi)
        pi.refresh_from_db()
        self.assertEqual(pi.durum, PaymentIntent.Durum.BEKLEMEDE)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="finans.payment.provider_rejected",
                entity_id=str(pi.pk),
                success=False,
            ).exists()
        )
