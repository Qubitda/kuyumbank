"""F5-013 — Finans audit zorunlu alanlar (actor, amount, currency, order_ref, success)."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import finans_audit, ledger_servisi, payment_servisi
from finans.services.finans_audit import REQUIRED_DETAIL_KEYS
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class FinansAuditContractTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def test_helper_rejects_missing_amount(self):
        with self.assertRaises(ValidationError):
            finans_audit.record_finans_audit(
                actor=self.finance,
                action="finans.test",
                amount="",
                currency="TRY",
                order_ref="1",
            )

    def test_helper_rejects_success_without_actor(self):
        with self.assertRaises(ValidationError):
            finans_audit.record_finans_audit(
                actor=None,
                action="finans.test",
                amount=Decimal("1.00"),
                currency="TRY",
                success=True,
            )

    def test_ledger_post_audit_has_required_keys(self):
        entry = ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("25.50"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="aud-le-1",
            referans_tip="Order",
            referans_id="99",
        )
        row = AuditOlay.objects.get(
            action="finans.ledger.post", entity_id=str(entry.pk)
        )
        self.assertTrue(row.success)
        self.assertEqual(row.actor_id, self.finance.pk)
        for key in REQUIRED_DETAIL_KEYS:
            self.assertIn(key, row.detail)
        self.assertEqual(row.detail["amount"], "25.50")
        self.assertEqual(row.detail["currency"], "TRY")
        self.assertEqual(row.detail["order_ref"], "99")

    def test_payment_capture_audit_order_ref(self):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="aud-pay-co"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        pi = payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="aud-pi"
        )
        payment_servisi.tahsil_et(actor=self.finance, intent=pi)
        row = AuditOlay.objects.get(
            action="finans.payment.captured", entity_id=str(pi.pk)
        )
        self.assertTrue(row.success)
        self.assertEqual(row.actor_id, self.finance.pk)
        self.assertEqual(row.detail["order_ref"], str(order.pk))
        self.assertEqual(row.detail["currency"], pi.para_birimi)
        self.assertEqual(row.detail["amount"], str(pi.tutar))
