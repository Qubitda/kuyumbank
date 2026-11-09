"""FX-001 / HEDGE-001 — open_has + HedgeEntry (ADR-0012 F5-K6/K7)."""

from decimal import Decimal
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings

from finans.services import fx_servisi, hedge_servisi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import checkout_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class HedgeAndFxTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def test_hedge_post_and_immutability(self):
        row = hedge_servisi.kaydet_hedge(
            actor=self.finance,
            grams=Decimal("12.5000"),
            idempotency_key="hg-1",
            metal_kodu="AU",
        )
        self.assertEqual(row.grams, Decimal("12.5000"))
        same = hedge_servisi.kaydet_hedge(
            actor=self.finance,
            grams=Decimal("99"),
            idempotency_key="hg-1",
        )
        self.assertEqual(same.pk, row.pk)
        row.aciklama = "x"
        with self.assertRaises(ValidationError):
            row.save()
        with self.assertRaises(ValidationError):
            row.delete()

    def test_hedge_zero_rejected(self):
        with self.assertRaises(ValidationError):
            hedge_servisi.kaydet_hedge(
                actor=self.finance,
                grams=Decimal("0"),
                idempotency_key="hg-0",
            )

    def test_buyer_cannot_hedge(self):
        with self.assertRaises(PermissionDenied):
            hedge_servisi.kaydet_hedge(
                actor=self.buyer,
                grams=Decimal("1"),
                idempotency_key="hg-deny",
            )

    def test_open_has_locked_minus_hedge(self):
        self._quote_and_cart(miktar=Decimal("2"))
        checkout_servisi.checkout(actor=self.buyer, idempotency_key="fx-co-1")
        locked = fx_servisi.locked_customer_has()
        self.assertGreater(locked, Decimal("0"))

        hedge_servisi.kaydet_hedge(
            actor=self.finance,
            grams=Decimal("1.0000"),
            idempotency_key="hg-fx",
        )
        pos = fx_servisi.open_has_position(limit=Decimal("999999"))
        self.assertEqual(pos.unpaid_supplier, Decimal("0.0000"))
        self.assertEqual(pos.hedge, Decimal("1.0000"))
        self.assertEqual(pos.open_has, locked - Decimal("1.0000"))
        self.assertFalse(pos.over_limit)

    @override_settings(HAS_POSITION_LIMIT=Decimal("0.0001"))
    def test_over_limit_sets_approval_required(self):
        self._quote_and_cart(miktar=Decimal("2"))
        checkout_servisi.checkout(actor=self.buyer, idempotency_key="fx-co-2")
        pos = fx_servisi.open_has_position()
        self.assertTrue(pos.over_limit)
        self.assertTrue(pos.approval_required)

    def test_hedge_lazy_zero_when_empty(self):
        with mock.patch(
            "finans.services.hedge_servisi.hedge_has_total",
            return_value=Decimal("0"),
        ):
            pos = fx_servisi.open_has_position(limit=Decimal("100"))
        self.assertEqual(pos.hedge, Decimal("0.0000"))
